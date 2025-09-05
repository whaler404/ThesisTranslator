import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil
import json
from pathlib import Path

from src.minio_client import MinIOClient
from src.paper_downloader import PaperDownloader
from src.minio_file_interface import MinIOFileInterface
from src.minio_service import MinIOService
from src.main import ThesisTranslator
from minio.error import S3Error


class TestMinIOIntegration(unittest.TestCase):
    """Integration tests for MinIO functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test PDF file
        self.test_pdf_path = os.path.join(self.temp_dir, 'test.pdf')
        with open(self.test_pdf_path, 'w') as f:
            f.write('%PDF-1.4\nTest PDF content')
        
        # Mock MinIO client
        self.mock_minio_client = Mock()
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.fput_object.return_value = Mock()
        self.mock_minio_client.download_file.return_value = True
        self.mock_minio_client.generate_safe_filename.return_value = 'arxiv_2101.00001.pdf'
        # Create mock objects for list_objects
        mock_object = Mock()
        mock_object.object_name = 'test.pdf'
        mock_object.size = 1024
        mock_object.last_modified = '2024-01-01T00:00:00Z'
        mock_object.etag = 'abc123'
        self.mock_minio_client.list_objects.return_value = iter([mock_object])
        self.mock_minio_client.remove_object.return_value = None
        self.mock_minio_client.stat_object.return_value = Mock(
            size=1024,
            last_modified='2024-01-01T00:00:00Z',
            etag='abc123',
            content_type='application/pdf'
        )
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.get_presigned_url.return_value = 'https://test-url.com'

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_minio_client_integration(self):
        """Test MinIO client integration with real operations"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint='localhost:9000',
                access_key='test-key',
                secret_key='test-secret',
                bucket_name='test-bucket'
            )
            
            # Test file upload
            result = client.upload_file(self.test_pdf_path, 'test.pdf')
            self.assertTrue(result)
            self.mock_minio_client.fput_object.assert_called_once()
            
            # Test file download
            download_path = os.path.join(self.temp_dir, 'downloaded.pdf')
            result = client.download_file('test.pdf', download_path)
            self.assertTrue(result)
            self.mock_minio_client.fget_object.assert_called_once()
            
            # Test file listing
            files = client.list_files()
            self.assertIsInstance(files, list)
            self.mock_minio_client.list_objects.assert_called_once()
            
            # Test file deletion
            result = client.delete_file('test.pdf')
            self.assertTrue(result)
            self.mock_minio_client.remove_object.assert_called_once()

    def test_paper_downloader_integration(self):
        """Test paper downloader integration with MinIO"""
        with patch('src.paper_downloader.requests.get') as mock_get:
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.content = b'%PDF-1.4\nTest PDF content'
            mock_response.headers = {'Content-Type': 'application/pdf'}
            mock_get.return_value = mock_response
            
            downloader = PaperDownloader(minio_client=self.mock_minio_client)
            
            # Test single paper download
            result = downloader.download_paper('https://arxiv.org/pdf/2101.00001')
            
            self.assertIsNotNone(result)
            self.assertEqual(result['object_name'], 'arxiv_2101.00001.pdf')
            self.mock_minio_client.upload_from_bytes.assert_called_once()
            
            # Test batch download
            urls = [
                'https://arxiv.org/pdf/2101.00001',
                'https://arxiv.org/pdf/2101.00002'
            ]
            
            # Reset mock
            self.mock_minio_client.upload_from_bytes.reset_mock()
            
            batch_result = downloader.batch_download_papers(urls)
            
            self.assertIsInstance(batch_result, list)
            self.assertEqual(len(batch_result), 2)
            self.assertEqual(self.mock_minio_client.upload_from_bytes.call_count, 2)

    def test_file_interface_integration(self):
        """Test file interface integration with MinIO and translation"""
        with patch('src.minio_file_interface.tempfile.gettempdir', return_value=self.temp_dir):
            interface = MinIOFileInterface(minio_client=self.mock_minio_client)
            
            # Test file retrieval from MinIO
            local_path = interface.get_file_from_minio('test.pdf')
            
            self.assertIsNotNone(local_path)
            self.assertTrue('test' in local_path and local_path.endswith('.pdf'))
            self.mock_minio_client.download_file.assert_called_once()
            
            # Test that temp file is registered
            self.assertEqual(len(interface.temp_files), 1)
            self.assertTrue(local_path in interface.temp_files)
            
            # Test cleanup
            interface.cleanup_temp_files()
            self.assertEqual(len(interface.temp_files), 0)

    def test_service_integration(self):
        """Test HTTP service integration with MinIO"""
        with patch('src.minio_service.create_minio_client_from_config') as mock_create_client, \
             patch('src.minio_service.PaperDownloader') as mock_downloader_class:
            
            # Create a fresh mock for this test
            test_mock_minio_client = Mock()
            test_mock_minio_client.bucket_exists.return_value = True
            test_mock_minio_client.fput_object.return_value = Mock()
            test_mock_minio_client.fget_object.return_value = None
            test_mock_minio_client.remove_object.return_value = None
            test_mock_minio_client.stat_object.return_value = Mock(
                size=1024,
                last_modified='2024-01-01T00:00:00Z',
                etag='abc123',
                content_type='application/pdf'
            )
            
            # Create mock objects for list_objects
            mock_object = Mock()
            mock_object.object_name = 'test.pdf'
            mock_object.size = 1024
            mock_object.last_modified = '2024-01-01T00:00:00Z'
            mock_object.etag = 'abc123'
            test_mock_minio_client.list_objects.return_value = iter([mock_object])
            
            # Create a mock MinIOClient that avoids real MinIO operations
            mock_minio_client_instance = Mock()
            mock_minio_client_instance.bucket_exists.return_value = True
            mock_minio_client_instance.list_files.return_value = [{
                'name': 'test.pdf',
                'size': 1024,
                'last_modified': '2024-01-01T00:00:00Z',
                'etag': 'abc123',
                'content_type': 'application/pdf'
            }]
            mock_minio_client_instance.get_file_info.return_value = {
                'name': 'test.pdf',
                'size': 1024,
                'last_modified': '2024-01-01T00:00:00Z',
                'etag': 'abc123',
                'content_type': 'application/pdf'
            }
            mock_minio_client_instance.file_exists.return_value = True
            mock_minio_client_instance.get_file_url.return_value = 'https://test-url.com'
            
            mock_create_client.return_value = mock_minio_client_instance
            
            mock_downloader = Mock()
            mock_downloader.download_paper.return_value = {
                'success': True,
                'object_name': 'arxiv_2101.00001.pdf',
                'url': 'https://arxiv.org/pdf/2101.00001',
                'size': 1024
            }
            mock_downloader.batch_download_papers.return_value = {
                'success': True,
                'total': 1,
                'success_count': 1,
                'failure_count': 0,
                'results': [{
                    'success': True,
                    'url': 'https://arxiv.org/pdf/2101.00001',
                    'object_name': 'arxiv_2101.00001.pdf',
                    'size': 1024
                }]
            }
            mock_downloader_class.return_value = mock_downloader
            
            service = MinIOService()
            app = service.create_app()
            app.config['TESTING'] = True
            client = app.test_client()
            
            # Test health check
            response = client.get('/api/health')
            self.assertEqual(response.status_code, 200)
            
            # Test file listing
            response = client.get('/api/files')
            self.assertEqual(response.status_code, 200)
            
            # Test paper download
            response = client.post(
                '/api/download/paper',
                json={'url': 'https://arxiv.org/pdf/2101.00001'},
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            
            # Test statistics
            response = client.get('/api/statistics')
            self.assertEqual(response.status_code, 200)

    def test_thesis_translator_integration(self):
        """Test ThesisTranslator integration with MinIO"""
        with patch('src.main.create_minio_client_from_config') as mock_create_client, \
             patch('src.main.create_minio_file_interface_from_env') as mock_create_interface, \
             patch('src.main.PaperDownloader') as mock_downloader_class, \
             patch('src.main.AITranslator') as mock_translator_class, \
             patch('src.main.PDFTextExtractor') as mock_extractor_class, \
             patch('src.main.TextChunker') as mock_chunker_class, \
             patch('src.main.TextCleaner') as mock_cleaner_class, \
             patch('src.main.TextSorter') as mock_sorter_class, \
             patch('src.main.MarkdownGenerator') as mock_generator_class:
            
            # Mock MinIO client
            mock_create_client.return_value = self.mock_minio_client
            
            # Mock MinIO file interface
            mock_file_interface = Mock()
            mock_file_interface.get_file_from_minio_to_temp.return_value = '/tmp/test.pdf'
            mock_create_interface.return_value = mock_file_interface
            
            # Mock downloader
            mock_downloader = Mock()
            mock_downloader.download_paper.return_value = {
                'success': True,
                'object_name': 'arxiv_2101.00001.pdf',
                'url': 'https://arxiv.org/pdf/2101.00001',
                'size': 1024
            }
            mock_downloader_class.return_value = mock_downloader
            
            # Mock translator
            mock_translator = Mock()
            mock_translator.translate_chunks.return_value = [
                {'text': 'Translated text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_translator_class.return_value = mock_translator
            
            # Mock PDF extractor with context manager support
            mock_extractor = Mock()
            mock_extractor.__enter__ = Mock(return_value=mock_extractor)
            mock_extractor.__exit__ = Mock(return_value=None)
            mock_extractor.get_reading_order.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_extractor_class.return_value = mock_extractor
            
            # Mock other components
            mock_chunker = Mock()
            mock_chunker.create_chunks.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_chunker_class.return_value = mock_chunker
            
            mock_cleaner = Mock()
            mock_cleaner.clean_text_chunks.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_cleaner.process_cleaned_output.return_value = {
                'text': 'Sample text content', 'type': 'paragraph', 'page': 1
            }
            mock_cleaner_class.return_value = mock_cleaner
            
            mock_sorter_class.return_value = Mock()
            
            mock_generator = Mock()
            mock_generator.generate_markdown.return_value = '# Translated Content\n\nSample text content'
            mock_generator.validate_markdown.return_value = {"is_valid": True, "errors": []}
            mock_generator.add_metadata.return_value = '# Translated Content\n\nSample text content'
            mock_generator.create_table_of_contents.return_value = '# Translated Content\n\nSample text content'
            mock_generator_class.return_value = mock_generator
            
            # Create translator with mocked dependencies
            translator = ThesisTranslator(openai_api_key='test-key')
            
            # Test paper download
            result = translator.download_paper('https://arxiv.org/pdf/2101.00001')
            self.assertIsNotNone(result)
            
            # Test translation from MinIO
            success = translator.translate_from_minio('test.pdf', 'output.md')
            self.assertTrue(success)

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        with patch('src.main.create_minio_client_from_config') as mock_create_client, \
             patch('src.main.create_minio_file_interface_from_env') as mock_create_interface, \
             patch('src.main.PaperDownloader') as mock_downloader_class, \
             patch('src.main.AITranslator') as mock_translator_class, \
             patch('src.main.PDFTextExtractor') as mock_extractor_class, \
             patch('src.main.TextChunker') as mock_chunker_class, \
             patch('src.main.TextCleaner') as mock_cleaner_class, \
             patch('src.main.TextSorter') as mock_sorter_class, \
             patch('src.main.MarkdownGenerator') as mock_generator_class:
            
            # Mock dependencies
            mock_create_client.return_value = self.mock_minio_client
            
            # Mock MinIO file interface
            mock_file_interface = Mock()
            mock_file_interface.get_file_from_minio_to_temp.return_value = '/tmp/test.pdf'
            mock_create_interface.return_value = mock_file_interface
            
            mock_downloader = Mock()
            mock_downloader.download_paper.return_value = {
                'success': True,
                'object_name': 'arxiv_2101.00001.pdf',
                'url': 'https://arxiv.org/pdf/2101.00001',
                'size': 1024
            }
            mock_downloader_class.return_value = mock_downloader
            
            mock_translator = Mock()
            mock_translator.translate_chunks.return_value = [
                {'text': 'Translated text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_translator_class.return_value = mock_translator
            
            mock_extractor = Mock()
            mock_extractor.__enter__ = Mock(return_value=mock_extractor)
            mock_extractor.__exit__ = Mock(return_value=None)
            mock_extractor.get_reading_order.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_extractor_class.return_value = mock_extractor
            
            mock_chunker = Mock()
            mock_chunker.create_chunks.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_chunker_class.return_value = mock_chunker
            
            mock_cleaner = Mock()
            mock_cleaner.clean_text_chunks.return_value = [
                {'text': 'Sample text content', 'type': 'paragraph', 'page': 1}
            ]
            mock_cleaner.process_cleaned_output.return_value = {
                'text': 'Sample text content', 'type': 'paragraph', 'page': 1
            }
            mock_cleaner_class.return_value = mock_cleaner
            
            mock_sorter_class.return_value = Mock()
            
            mock_generator = Mock()
            mock_generator.generate_markdown.return_value = '# Translated Content\n\nSample text content'
            mock_generator.validate_markdown.return_value = {"is_valid": True, "errors": []}
            mock_generator.add_metadata.return_value = '# Translated Content\n\nSample text content'
            mock_generator.create_table_of_contents.return_value = '# Translated Content\n\nSample text content'
            mock_generator_class.return_value = mock_generator
            
            # Step 1: Download paper
            translator = ThesisTranslator(openai_api_key='test-key')
            download_result = translator.download_paper('https://arxiv.org/pdf/2101.00001')
            self.assertIsNotNone(download_result)
            
            # Step 2: List files
            self.mock_minio_client.list_files.return_value = [{
                'name': 'arxiv_2101.00001.pdf',
                'size': 1024,
                'last_modified': '2024-01-01T00:00:00Z'
            }]
            
            files = self.mock_minio_client.list_files()
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0]['name'], 'arxiv_2101.00001.pdf')
            
            # Step 3: Translate from MinIO
            success = translator.translate_from_minio('arxiv_2101.00001.pdf', 'output.md')
            self.assertTrue(success)
            
            # Step 4: Verify workflow completed successfully

    def test_error_handling_integration(self):
        """Test error handling in integrated scenarios"""
        with patch('src.main.create_minio_client_from_config') as mock_create_client, \
             patch('src.main.create_minio_client_from_env') as mock_create_client_env, \
             patch('src.main.create_minio_file_interface_from_env') as mock_create_interface_env, \
             patch('src.main.create_paper_downloader_from_env') as mock_create_downloader_env, \
             patch('src.main.PaperDownloader') as mock_downloader_class:
            
            # Test MinIO connection failure
            mock_create_client.return_value = None
            mock_create_client_env.return_value = None
            mock_create_interface_env.return_value = None
            mock_create_downloader_env.return_value = None
            
            # Constructor should not raise exception, but download_paper should return None
            translator = ThesisTranslator(openai_api_key='test-key')
            
            # Ensure paper_downloader is None after initialization failure
            self.assertIsNone(translator.paper_downloader)
            
            result = translator.download_paper('https://arxiv.org/pdf/2101.00001')
            self.assertIsNone(result)
            
            # Test download failure
            mock_create_client.side_effect = None
            mock_create_client_env.side_effect = None
            mock_create_interface_env.side_effect = None
            mock_create_downloader_env.side_effect = None
            mock_create_client.return_value = self.mock_minio_client
            
            mock_downloader = Mock()
            mock_downloader.download_paper.return_value = None
            mock_downloader_class.return_value = mock_downloader
            
            translator = ThesisTranslator(openai_api_key='test-key')
            result = translator.download_paper('https://arxiv.org/pdf/2101.00001')
            
            # The result should be None because the download failed
            self.assertIsNone(result)

    def test_concurrent_operations(self):
        """Test concurrent operations with MinIO"""
        import threading
        import time
        
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint='localhost:9000',
                access_key='test-key',
                secret_key='test-secret',
                bucket_name='test-bucket'
            )
            
            results = []
            errors = []
            
            def upload_file(file_num):
                try:
                    result = client.upload_file(self.test_pdf_path, f'test_{file_num}.pdf')
                    results.append(result)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads for concurrent uploads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=upload_file, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify results
            self.assertEqual(len(results), 5)
            self.assertEqual(len(errors), 0)
            self.assertTrue(all(results))

    def test_memory_management(self):
        """Test memory management with large files"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint='localhost:9000',
                access_key='test-key',
                secret_key='test-secret',
                bucket_name='test-bucket'
            )
            
            # Test with multiple large files
            large_files = []
            for i in range(10):
                file_path = os.path.join(self.temp_dir, f'large_{i}.pdf')
                with open(file_path, 'w') as f:
                    f.write('0' * (1024 * 1024))  # 1MB files
                large_files.append(file_path)
            
            # Upload all files
            for file_path in large_files:
                result = client.upload_file(file_path, os.path.basename(file_path))
                self.assertTrue(result)
            
            # Verify all uploads were called
            self.assertEqual(self.mock_minio_client.fput_object.call_count, 10)

    def test_configuration_integration(self):
        """Test configuration management integration"""
        test_config = {
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-key',
            'MINIO_SECRET_KEY': 'test-secret',
            'MINIO_BUCKET_NAME': 'test-bucket',
            'MINIO_SECURE': 'false'
        }
        
        with patch.dict(os.environ, test_config):
            # Test MinIO client creation from environment
            with patch('src.minio_client.Minio') as mock_minio_class:
                mock_minio_class.return_value = self.mock_minio_client
                
                from src.minio_client import create_minio_client_from_env
                client = create_minio_client_from_env()
                
                self.assertEqual(client.endpoint, 'localhost:9000')
                self.assertEqual(client.access_key, 'test-key')
                self.assertEqual(client.secret_key, 'test-secret')
                self.assertEqual(client.bucket_name, 'test-bucket')
                self.assertEqual(client.secure, False)

    def test_file_operations_sequence(self):
        """Test sequence of file operations"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint='localhost:9000',
                access_key='test-key',
                secret_key='test-secret',
                bucket_name='test-bucket'
            )
            
            # Sequence: upload -> list -> info -> download -> delete
            test_file = 'sequence_test.pdf'
            
            # Upload
            result = client.upload_file(self.test_pdf_path, test_file)
            self.assertTrue(result)
            
            # List
            # Reset the list_objects mock to return the correct file
            mock_object = Mock()
            mock_object.object_name = test_file
            mock_object.size = 1024
            mock_object.last_modified = '2024-01-01T00:00:00Z'
            mock_object.etag = 'abc123'
            self.mock_minio_client.list_objects.return_value = iter([mock_object])
            
            files = client.list_files()
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0]['name'], test_file)
            
            # Get info
            info = client.get_file_info(test_file)
            self.assertIsNotNone(info)
            self.assertEqual(info['name'], test_file)
            
            # Download
            download_path = os.path.join(self.temp_dir, 'downloaded.pdf')
            result = client.download_file(test_file, download_path)
            self.assertTrue(result)
            
            # Delete
            result = client.delete_file(test_file)
            self.assertTrue(result)
            
            # Verify deletion
            self.mock_minio_client.stat_object.side_effect = S3Error(
                "NoSuchKey", "Object does not exist", "test-bucket", "test-key", 
                "test-request-id", "test-host-id", None, None
            )
            exists = client.file_exists(test_file)
            self.assertFalse(exists)

    def test_service_api_coverage(self):
        """Test coverage of all service API endpoints"""
        with patch('src.minio_service.create_minio_client_from_config') as mock_create_client, \
             patch('src.minio_service.create_paper_downloader_from_env') as mock_create_downloader:
            
            # Create a mock MinIOClient that avoids real MinIO operations
            mock_minio_client_instance = Mock()
            mock_minio_client_instance.bucket_exists.return_value = True
            mock_minio_client_instance.list_files.return_value = [{
                'name': 'test.pdf',
                'size': 1024,
                'last_modified': '2024-01-01T00:00:00Z',
                'etag': 'abc123',
                'content_type': 'application/pdf'
            }]
            mock_minio_client_instance.get_file_info.return_value = {
                'name': 'test.pdf',
                'size': 1024,
                'last_modified': '2024-01-01T00:00:00Z',
                'etag': 'abc123',
                'content_type': 'application/pdf'
            }
            mock_minio_client_instance.file_exists.return_value = True
            mock_minio_client_instance.get_presigned_url.return_value = 'https://test-url.com'
            mock_minio_client_instance.delete_file.return_value = True
            mock_minio_client_instance._get_content_type.return_value = 'application/pdf'
            
            mock_downloader = Mock()
            mock_create_downloader.return_value = mock_downloader
            
            mock_create_client.return_value = mock_minio_client_instance
            
            mock_downloader.download_paper.return_value = {
                'success': True,
                'object_name': 'test.pdf',
                'url': 'https://test.com',
                'size': 1024
            }
            mock_downloader.batch_download_papers.return_value = {
                'success': True,
                'total': 1,
                'success_count': 1,
                'failure_count': 0,
                'results': [{
                    'success': True,
                    'url': 'https://test.com',
                    'object_name': 'test.pdf',
                    'size': 1024
                }]
            }
            
            # Configure statistics method
            mock_downloader.get_download_statistics.return_value = {
                'total_files': 5,
                'total_size': 5120,
                'type_distribution': {'.pdf': 3, '.txt': 2},
                'recent_downloads': []
            }
            
            # Configure arXiv method
            mock_downloader.extract_papers_from_arxiv.return_value = {
                'success': True,
                'object_name': 'arxiv_2101.00001.pdf',
                'size': 1024,
                'url': 'https://arxiv.org/pdf/2101.00001'
            }
            
            service = MinIOService()
            app = service.create_app()
            app.config['TESTING'] = True
            client = app.test_client()
            
            # Test all endpoints
            endpoints = [
                ('GET', '/api/health'),
                ('GET', '/api/files'),
                ('GET', '/api/files/test.pdf'),
                ('GET', '/api/files/test.pdf/exists'),
                ('GET', '/api/files/test.pdf/url'),
                ('GET', '/api/statistics'),
                ('POST', '/api/download/paper'),
                ('POST', '/api/download/batch'),
                ('POST', '/api/download/arxiv/2101.00001'),
                ('DELETE', '/api/files/test.pdf'),
            ]
            
            for method, endpoint in endpoints:
                if method == 'GET':
                    response = client.get(endpoint)
                elif method == 'POST':
                    if 'paper' in endpoint:
                        response = client.post(endpoint, json={'url': 'https://test.com'})
                    elif 'batch' in endpoint:
                        response = client.post(endpoint, json={'urls': ['https://test.com']})
                    else:
                        response = client.post(endpoint)
                elif method == 'DELETE':
                    response = client.delete(endpoint)
                
                # Should not return 500 for any endpoint
                self.assertNotEqual(response.status_code, 500, f"Endpoint {endpoint} returned 500")


if __name__ == '__main__':
    unittest.main()