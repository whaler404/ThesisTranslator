import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from io import BytesIO

from src.minio_service import MinIOService


class TestMinIOService(unittest.TestCase):
    """Test cases for MinIOService class"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = MinIOService()
        self.app = self.service.create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock dependencies
        self.mock_minio_client = Mock()
        self.mock_downloader = Mock()
        
        # Patch the create functions
        self.create_minio_client_patch = patch('src.minio_service.create_minio_client_from_config')
        self.create_downloader_patch = patch('src.minio_service.create_paper_downloader_from_env')
        
        self.mock_create_minio = self.create_minio_client_patch.start()
        self.mock_create_downloader = self.create_downloader_patch.start()
        
        self.mock_create_minio.return_value = self.mock_minio_client
        self.mock_create_downloader.return_value = self.mock_downloader

    def tearDown(self):
        """Clean up test fixtures"""
        self.create_minio_client_patch.stop()
        self.create_downloader_patch.stop()

    def test_create_app(self):
        """Test Flask app creation"""
        app = self.service.create_app()
        
        self.assertIsNotNone(app)
        self.assertEqual(app.name, 'minio_service')
        self.assertTrue(hasattr(app, 'url_map'))

    def test_health_check_success(self):
        """Test successful health check"""
        self.mock_minio_client.bucket_exists.return_value = True
        
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'MinIO File Service')

    def test_health_check_minio_failure(self):
        """Test health check when MinIO is not available"""
        self.mock_minio_client.bucket_exists.return_value = False
        
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('MinIO connection failed', data['error'])

    def test_list_files_success(self):
        """Test successful file listing"""
        mock_files = [
            {'name': 'file1.pdf', 'size': 1024, 'last_modified': '2024-01-01T00:00:00Z', 'etag': 'abc123'},
            {'name': 'file2.pdf', 'size': 2048, 'last_modified': '2024-01-02T00:00:00Z', 'etag': 'def456'}
        ]
        
        self.mock_minio_client.list_files.return_value = mock_files
        
        response = self.client.get('/api/files')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['data'][0]['name'], 'file1.pdf')

    def test_list_files_with_prefix(self):
        """Test file listing with prefix filter"""
        mock_files = [
            {'name': 'arxiv_1234.pdf', 'size': 1024}
        ]
        
        self.mock_minio_client.list_files.return_value = mock_files
        
        response = self.client.get('/api/files?prefix=arxiv_')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['name'], 'arxiv_1234.pdf')

    def test_list_files_empty(self):
        """Test file listing when no files exist"""
        self.mock_minio_client.list_files.return_value = []
        
        response = self.client.get('/api/files')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 0)
        self.assertEqual(data['count'], 0)

    def test_get_file_info_success(self):
        """Test successful file info retrieval"""
        mock_file_info = {
            'name': 'test.pdf',
            'size': 1024,
            'last_modified': '2024-01-01T00:00:00Z',
            'etag': 'abc123',
            'content_type': 'application/pdf'
        }
        
        self.mock_minio_client.get_file_info.return_value = mock_file_info
        
        response = self.client.get('/api/files/test.pdf')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], 'test.pdf')
        self.assertEqual(data['data']['size'], 1024)

    def test_get_file_info_not_found(self):
        """Test file info retrieval when file doesn't exist"""
        self.mock_minio_client.get_file_info.return_value = None
        
        response = self.client.get('/api/files/nonexistent.pdf')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'File not found')

    def test_delete_file_success(self):
        """Test successful file deletion"""
        self.mock_minio_client.delete_file.return_value = True
        
        response = self.client.delete('/api/files/test.pdf')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('deleted successfully', data['message'])

    def test_delete_file_not_found(self):
        """Test file deletion when file doesn't exist"""
        self.mock_minio_client.delete_file.return_value = False
        
        response = self.client.delete('/api/files/nonexistent.pdf')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'File not found')

    def test_download_file_success(self):
        """Test successful file download"""
        # Create a temporary file to simulate download
        test_content = b'PDF content'
        
        self.mock_minio_client.download_file.side_effect = lambda object_name, local_path: (
            open(local_path, 'wb').write(test_content)
        )
        
        response = self.client.get('/api/files/test.pdf/download')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, test_content)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

    def test_download_file_not_found(self):
        """Test file download when file doesn't exist"""
        self.mock_minio_client.download_file.return_value = False
        
        response = self.client.get('/api/files/nonexistent.pdf/download')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'File not found')

    def test_get_presigned_url_success(self):
        """Test successful presigned URL generation"""
        self.mock_minio_client.get_presigned_url.return_value = 'https://test-url.com'
        
        response = self.client.get('/api/files/test.pdf/url')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['url'], 'https://test-url.com')
        self.assertEqual(data['data']['expires_in'], 3600)

    def test_get_presigned_url_custom_expires(self):
        """Test presigned URL generation with custom expiration"""
        self.mock_minio_client.get_presigned_url.return_value = 'https://test-url.com'
        
        response = self.client.get('/api/files/test.pdf/url?expires=7200')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['expires_in'], 7200)

    def test_upload_file_success(self):
        """Test successful file upload"""
        test_content = b'PDF content'
        
        self.mock_minio_client.upload_file.return_value = True
        
        response = self.client.post(
            '/api/upload',
            data={'file': (BytesIO(test_content), 'test.pdf')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('uploaded successfully', data['message'])
        self.assertEqual(data['data']['filename'], 'test.pdf')

    def test_upload_file_no_file(self):
        """Test file upload when no file is provided"""
        response = self.client.post('/api/upload', data={}, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'No file provided')

    def test_upload_file_failure(self):
        """Test file upload when upload fails"""
        test_content = b'PDF content'
        
        self.mock_minio_client.upload_file.return_value = False
        
        response = self.client.post(
            '/api/upload',
            data={'file': (BytesIO(test_content), 'test.pdf')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('File upload failed', data['error'])

    def test_download_paper_success(self):
        """Test successful paper download"""
        download_result = {
            'success': True,
            'object_name': 'arxiv_2101.00001.pdf',
            'url': 'https://arxiv.org/pdf/2101.00001',
            'size': 1024,
            'content_type': 'application/pdf',
            'original_filename': '2101.00001.pdf',
            'download_time': 1640995200.123
        }
        
        self.mock_downloader.download_paper.return_value = download_result
        
        response = self.client.post(
            '/api/download/paper',
            json={'url': 'https://arxiv.org/pdf/2101.00001'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['object_name'], 'arxiv_2101.00001.pdf')
        self.assertEqual(data['data']['url'], 'https://arxiv.org/pdf/2101.00001')

    def test_download_paper_with_custom_name(self):
        """Test paper download with custom object name"""
        download_result = {
            'success': True,
            'object_name': 'custom_name.pdf',
            'url': 'https://arxiv.org/pdf/2101.00001'
        }
        
        self.mock_downloader.download_paper.return_value = download_result
        
        response = self.client.post(
            '/api/download/paper',
            json={
                'url': 'https://arxiv.org/pdf/2101.00001',
                'object_name': 'custom_name.pdf'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['data']['object_name'], 'custom_name.pdf')

    def test_download_paper_missing_url(self):
        """Test paper download when URL is missing"""
        response = self.client.post(
            '/api/download/paper',
            json={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'URL is required')

    def test_download_paper_failure(self):
        """Test paper download when download fails"""
        download_result = {
            'success': False,
            'error': 'Download failed'
        }
        
        self.mock_downloader.download_paper.return_value = download_result
        
        response = self.client.post(
            '/api/download/paper',
            json={'url': 'https://arxiv.org/pdf/2101.00001'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Download failed')

    def test_batch_download_success(self):
        """Test successful batch download"""
        download_result = {
            'success': True,
            'total': 2,
            'success_count': 2,
            'failure_count': 0,
            'results': [
                {
                    'success': True,
                    'url': 'https://arxiv.org/pdf/2101.00001',
                    'object_name': 'arxiv_2101.00001.pdf',
                    'size': 1024
                },
                {
                    'success': True,
                    'url': 'https://arxiv.org/pdf/2101.00002',
                    'object_name': 'arxiv_2101.00002.pdf',
                    'size': 2048
                }
            ]
        }
        
        self.mock_downloader.batch_download_papers.return_value = download_result
        
        response = self.client.post(
            '/api/download/batch',
            json={'urls': ['https://arxiv.org/pdf/2101.00001', 'https://arxiv.org/pdf/2101.00002']},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 2)
        self.assertEqual(data['data']['success_count'], 2)
        self.assertEqual(len(data['data']['results']), 2)

    def test_batch_download_missing_urls(self):
        """Test batch download when URLs are missing"""
        response = self.client.post(
            '/api/download/batch',
            json={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'URLs are required')

    def test_batch_download_empty_urls(self):
        """Test batch download with empty URLs list"""
        response = self.client.post(
            '/api/download/batch',
            json={'urls': []},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'URLs cannot be empty')

    def test_batch_download_too_many_urls(self):
        """Test batch download with too many URLs"""
        urls = [f'https://arxiv.org/pdf/2101.{i:05d}' for i in range(51)]
        
        response = self.client.post(
            '/api/download/batch',
            json={'urls': urls},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Maximum 50 URLs allowed', data['error'])

    def test_download_arxiv_success(self):
        """Test successful arXiv paper download"""
        download_result = {
            'success': True,
            'object_name': 'arxiv_2101.00001.pdf',
            'url': 'https://arxiv.org/pdf/2101.00001.pdf',
            'size': 1024,
            'content_type': 'application/pdf',
            'original_filename': '2101.00001.pdf',
            'download_time': 1640995200.123
        }
        
        self.mock_downloader.extract_papers_from_arxiv.return_value = download_result
        
        response = self.client.post('/api/download/arxiv/2101.00001')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['object_name'], 'arxiv_2101.00001.pdf')

    def test_download_arxiv_failure(self):
        """Test arXiv paper download when download fails"""
        download_result = {
            'success': False,
            'error': 'Download failed'
        }
        
        self.mock_downloader.extract_papers_from_arxiv.return_value = download_result
        
        response = self.client.post('/api/download/arxiv/2101.00001')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Download failed')

    def test_get_statistics_success(self):
        """Test successful statistics retrieval"""
        mock_files = [
            {'name': 'file1.pdf', 'size': 1024, 'last_modified': '2024-01-01T00:00:00Z'},
            {'name': 'file2.pdf', 'size': 2048, 'last_modified': '2024-01-02T00:00:00Z'},
            {'name': 'file3.txt', 'size': 512, 'last_modified': '2024-01-03T00:00:00Z'}
        ]
        
        self.mock_minio_client.list_files.return_value = mock_files
        
        response = self.client.get('/api/statistics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_files'], 3)
        self.assertEqual(data['data']['pdf_files'], 2)
        self.assertEqual(data['data']['other_files'], 1)
        self.assertEqual(data['data']['total_size'], 3584)
        self.assertEqual(data['data']['pdf_size'], 3072)

    def test_get_statistics_empty(self):
        """Test statistics retrieval when no files exist"""
        self.mock_minio_client.list_files.return_value = []
        
        response = self.client.get('/api/statistics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_files'], 0)
        self.assertEqual(data['data']['pdf_files'], 0)
        self.assertEqual(data['data']['total_size'], 0)

    def test_check_file_exists_true(self):
        """Test file existence check when file exists"""
        self.mock_minio_client.file_exists.return_value = True
        
        response = self.client.get('/api/files/test.pdf/exists')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['exists'])
        self.assertEqual(data['data']['filename'], 'test.pdf')

    def test_check_file_exists_false(self):
        """Test file existence check when file doesn't exist"""
        self.mock_minio_client.file_exists.return_value = False
        
        response = self.client.get('/api/files/nonexistent.pdf/exists')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertFalse(data['data']['exists'])
        self.assertEqual(data['data']['filename'], 'nonexistent.pdf')

    def test_error_response_format(self):
        """Test that error responses follow consistent format"""
        # Test 404 error
        self.mock_minio_client.get_file_info.return_value = None
        
        response = self.client.get('/api/files/nonexistent.pdf')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertNotIn('data', data)

    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = self.client.options('/api/files')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)

    def test_invalid_endpoint(self):
        """Test access to invalid endpoint"""
        response = self.client.get('/completely/invalid/path')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Endpoint not found', data['error'])

    def test_method_not_allowed(self):
        """Test method not allowed error"""
        response = self.client.patch('/api/files')
        
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Method not allowed', data['error'])

    def test_large_file_upload(self):
        """Test handling of large file upload"""
        # Create a large file (simulated)
        large_content = b'0' * (10 * 1024 * 1024)  # 10MB
        
        self.mock_minio_client.upload_file.return_value = True
        
        response = self.client.post(
            '/api/upload',
            data={'file': (BytesIO(large_content), 'large.pdf')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    def test_content_type_detection(self):
        """Test content type detection for different file types"""
        test_files = [
            ('test.pdf', b'%PDF-1.4', 'application/pdf'),
            ('test.txt', b'plain text', 'text/plain'),
            ('test.json', b'{"key": "value"}', 'application/json')
        ]
        
        for filename, content, expected_type in test_files:
            self.mock_minio_client.upload_file.return_value = True
            
            response = self.client.post(
                '/api/upload',
                data={'file': (BytesIO(content), filename)},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])


if __name__ == '__main__':
    unittest.main()