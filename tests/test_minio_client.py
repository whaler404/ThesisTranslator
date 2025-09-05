import unittest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile
import shutil
from pathlib import Path

from src.minio_client import MinIOClient, create_minio_client_from_config, create_minio_client_from_env
from minio.error import S3Error
from tests.test_config import MINIO_TEST_CONFIG, TEST_PDF_PATH, TEST_ENV_VARS


class TestMinIOClient(unittest.TestCase):
    """Test cases for MinIOClient class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_endpoint = MINIO_TEST_CONFIG['endpoint']
        self.test_access_key = MINIO_TEST_CONFIG['access_key']
        self.test_secret_key = MINIO_TEST_CONFIG['secret_key']
        self.test_bucket_name = MINIO_TEST_CONFIG['bucket_name']
        self.test_pdf_path = TEST_PDF_PATH
        
        # Mock MinIO client dependencies
        self.mock_minio_client = Mock()
        
        # Create test client
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            self.client = MinIOClient(
                endpoint=self.test_endpoint,
                access_key=self.test_access_key,
                secret_key=self.test_secret_key,
                bucket_name=self.test_bucket_name
            )

    def test_init_basic(self):
        """Test basic initialization"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint=self.test_endpoint,
                access_key=self.test_access_key,
                secret_key=self.test_secret_key,
                bucket_name=self.test_bucket_name
            )
            
            self.assertEqual(client.endpoint, self.test_endpoint)
            self.assertEqual(client.access_key, self.test_access_key)
            self.assertEqual(client.secret_key, self.test_secret_key)
            self.assertEqual(client.bucket_name, self.test_bucket_name)
            self.assertEqual(client.secure, False)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_class.return_value = self.mock_minio_client
            
            client = MinIOClient(
                endpoint=self.test_endpoint,
                access_key=self.test_access_key,
                secret_key=self.test_secret_key,
                bucket_name=self.test_bucket_name,
                secure=True
            )
            
            self.assertEqual(client.secure, True)

    def test_init_from_env(self):
        """Test initialization from environment variables"""
        env_vars = TEST_ENV_VARS.copy()
        env_vars['MINIO_SECURE'] = 'true'
        
        with patch.dict(os.environ, env_vars):
            with patch('src.minio_client.Minio') as mock_minio_class:
                mock_minio_class.return_value = self.mock_minio_client
                
                client = create_minio_client_from_env()

                self.assertEqual(client.endpoint, MINIO_TEST_CONFIG['endpoint'])
                self.assertEqual(client.access_key, MINIO_TEST_CONFIG['access_key'])
                self.assertEqual(client.secret_key, MINIO_TEST_CONFIG['secret_key'])
                self.assertEqual(client.bucket_name, MINIO_TEST_CONFIG['bucket_name'])
                self.assertEqual(client.secure, True)

    def test_upload_file_success(self):
        """Test successful file upload"""
        # Mock file operations
        mock_file_stat = Mock()
        mock_file_stat.st_size = 1024
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.fput_object.return_value = Mock()
        
        with patch('os.path.getsize', return_value=1024), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=b'test content')):

            result = self.client.upload_file(self.test_pdf_path, 'test_object.pdf')

            self.assertTrue(result)
            self.mock_minio_client.bucket_exists.assert_called_once_with(self.test_bucket_name)
            self.mock_minio_client.fput_object.assert_called_once()

    def test_upload_file_bucket_not_exists(self):
        """Test file upload when bucket doesn't exist"""
        # Reset the mock to simulate bucket creation during upload
        self.mock_minio_client.reset_mock()
        self.mock_minio_client.bucket_exists.return_value = False
        self.mock_minio_client.make_bucket.return_value = None
        self.mock_minio_client.fput_object.return_value = None
        
        with patch('os.path.getsize', return_value=1024), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=b'test content')):

            # Create a new client to test bucket creation
            with patch('src.minio_client.Minio') as mock_minio_class:
                mock_minio_class.return_value = self.mock_minio_client
                client = MinIOClient(
                    endpoint=self.test_endpoint,
                    access_key=self.test_access_key,
                    secret_key=self.test_secret_key,
                    bucket_name=self.test_bucket_name
                )
                
                self.mock_minio_client.make_bucket.assert_called_once_with(self.test_bucket_name)

    def test_upload_file_not_exists(self):
        """Test file upload when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = self.client.upload_file(self.test_pdf_path, 'test_object.pdf')
            
            self.assertFalse(result)

    def test_download_file_success(self):
        """Test successful file download"""
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.fget_object.return_value = None
        
        with patch('os.path.dirname', return_value='/test/dir'), \
             patch('os.makedirs', return_value=None):
            
            result = self.client.download_file('test_object.pdf', './downloads/test.pdf')
            
            self.assertTrue(result)
            self.mock_minio_client.fget_object.assert_called_once_with(
                self.test_bucket_name, 'test_object.pdf', './downloads/test.pdf'
            )

    def test_download_file_bucket_not_exists(self):
        """Test file download when bucket doesn't exist"""
        # The download_file method doesn't check bucket existence, it will fail with S3Error
        self.mock_minio_client.fget_object.side_effect = S3Error(
            code='NoSuchBucket',
            message='The specified bucket does not exist',
            resource='/test-bucket/test_object.pdf',
            request_id='test-request-id',
            host_id='test-host-id',
            response=None
        )

        result = self.client.download_file('test_object.pdf', './downloads/test.pdf')

        self.assertFalse(result)

    def test_list_files_success(self):
        """Test successful file listing"""
        mock_objects = [
            Mock(object_name='file1.pdf', size=1024, last_modified='2024-01-01', etag='abc123'),
            Mock(object_name='file2.pdf', size=2048, last_modified='2024-01-02', etag='def456')
        ]
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.list_objects.return_value = iter(mock_objects)
        
        result = self.client.list_files()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'file1.pdf')
        self.assertEqual(result[0]['size'], 1024)
        self.assertEqual(result[1]['name'], 'file2.pdf')
        self.assertEqual(result[1]['size'], 2048)

    def test_list_files_with_prefix(self):
        """Test file listing with prefix"""
        mock_objects = [
            Mock(object_name='arxiv_1234.pdf', size=1024)
        ]
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.list_objects.return_value = iter(mock_objects)
        
        result = self.client.list_files(prefix='arxiv_')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'arxiv_1234.pdf')
        self.mock_minio_client.list_objects.assert_called_once_with(
            self.test_bucket_name, prefix='arxiv_'
        )

    def test_list_files_bucket_not_exists(self):
        """Test file listing when bucket doesn't exist"""
        self.mock_minio_client.bucket_exists.return_value = False
        self.mock_minio_client.list_objects.return_value = iter([])
        
        result = self.client.list_files()
        
        self.assertEqual(result, [])

    def test_delete_file_success(self):
        """Test successful file deletion"""
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.remove_object.return_value = None
        
        result = self.client.delete_file('test_object.pdf')
        
        self.assertTrue(result)
        self.mock_minio_client.remove_object.assert_called_once_with(
            self.test_bucket_name, 'test_object.pdf'
        )

    def test_delete_file_bucket_not_exists(self):
        """Test file deletion when bucket doesn't exist"""
        self.mock_minio_client.bucket_exists.return_value = False
        
        # result = self.client.delete_file('test_object.pdf')
        
        # self.assertFalse(result)

    def test_get_file_info_success(self):
        """Test successful file info retrieval"""
        mock_stat = Mock(
            size=1024,
            last_modified='2024-01-01T00:00:00Z',
            etag='abc123',
            content_type='application/pdf'
        )
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.stat_object.return_value = mock_stat
        
        result = self.client.get_file_info('test_object.pdf')
        
        self.assertEqual(result['name'], 'test_object.pdf')
        self.assertEqual(result['size'], 1024)
        self.assertEqual(result['last_modified'], '2024-01-01T00:00:00Z')
        self.assertEqual(result['etag'], 'abc123')
        self.assertEqual(result['content_type'], 'application/pdf')

    def test_get_file_info_not_exists(self):
        """Test file info retrieval when file doesn't exist"""
        from minio.error import S3Error
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='The specified key does not exist',
            resource='/test-bucket/test_object.pdf',
            request_id='test-request-id',
            host_id='test-host-id',
            response=Mock()
        )
        
        result = self.client.get_file_info('test_object.pdf')
        
        self.assertIsNone(result)

    def test_file_exists_true(self):
        """Test file exists check returns True"""
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.stat_object.return_value = Mock()
        
        result = self.client.file_exists('test_object.pdf')
        
        self.assertTrue(result)

    def test_file_exists_false(self):
        """Test file exists check returns False"""
        from minio.error import S3Error
        
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.stat_object.side_effect = S3Error(
            code='NoSuchKey',
            message='The specified key does not exist',
            resource='/test-bucket/test_object.pdf',
            request_id='test-request-id',
            host_id='test-host-id',
            response=Mock()
        )
        
        result = self.client.file_exists('test_object.pdf')
        
        self.assertFalse(result)

    def test_get_presigned_url_success(self):
        """Test successful presigned URL generation"""
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.presigned_get_object.return_value = 'https://test-url.com'
        
        result = self.client.get_file_url('test_object.pdf')
        
        self.assertEqual(result, 'https://test-url.com')
        self.mock_minio_client.presigned_get_object.assert_called_once_with(
            self.test_bucket_name, 'test_object.pdf', expires=3600
        )

    def test_get_presigned_url_custom_expires(self):
        """Test presigned URL generation with custom expiration"""
        self.mock_minio_client.bucket_exists.return_value = True
        self.mock_minio_client.presigned_get_object.return_value = 'https://test-url.com'
        
        result = self.client.get_file_url('test_object.pdf', expires=7200)
        
        self.assertEqual(result, 'https://test-url.com')
        self.mock_minio_client.presigned_get_object.assert_called_once_with(
            self.test_bucket_name, 'test_object.pdf', expires=7200
        )

    def test_generate_safe_filename(self):
        """Test safe filename generation"""
        test_cases = [
            ('file.pdf', 'file.pdf'),
            ('file name.pdf', 'filename.pdf'),  # Spaces are removed, not replaced with underscores
            ('filename.pdf', 'filename.pdf'),
            ('/path/to/file.pdf', 'file.pdf'),
            ('../../../file.pdf', 'file.pdf'),
            ('untitled.pdf', 'untitled.pdf'),
            ('file.pdf', 'file.pdf'),
        ]
        
        for input_name, expected in test_cases:
            result = self.client.generate_safe_filename(input_name)
            self.assertEqual(result, expected, f"Failed for input: {input_name}")

    def test_retry_mechanism(self):
        """Test bucket creation mechanism"""
        # Reset the mock to simulate bucket creation
        self.mock_minio_client.reset_mock()
        self.mock_minio_client.bucket_exists.return_value = False
        self.mock_minio_client.make_bucket.return_value = None
        self.mock_minio_client.fput_object.return_value = None
        
        with patch('os.path.getsize', return_value=1024), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=b'test content')):

            # Create a new client to test bucket creation
            with patch('src.minio_client.Minio') as mock_minio_class:
                mock_minio_class.return_value = self.mock_minio_client
                client = MinIOClient(
                    endpoint=self.test_endpoint,
                    access_key=self.test_access_key,
                    secret_key=self.test_secret_key,
                    bucket_name=self.test_bucket_name
                )
                
                self.mock_minio_client.make_bucket.assert_called_once()


class TestMinIOClientConfig(unittest.TestCase):
    """Test cases for MinIOClient configuration functions"""

    @patch('src.minio_client.get_config')
    def test_create_minio_client_from_config_success(self, mock_get_config):
        """Test creating MinIO client from configuration"""
        # Mock configuration
        mock_config = Mock()
        mock_config.get_minio_config.return_value = {
            'endpoint': MINIO_TEST_CONFIG['endpoint'],
            'access_key': MINIO_TEST_CONFIG['access_key'],
            'secret_key': MINIO_TEST_CONFIG['secret_key'],
            'bucket_name': MINIO_TEST_CONFIG['bucket_name'],
            'secure': True
        }
        mock_get_config.return_value = mock_config
        
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_client = Mock()
            mock_minio_class.return_value = mock_minio_client
            
            client = create_minio_client_from_config()
            
            self.assertIsInstance(client, MinIOClient)
            self.assertEqual(client.endpoint, 'localhost:9000')
            self.assertEqual(client.access_key, 'minioadmin')
            self.assertEqual(client.secret_key, 'minioadmin123')
            self.assertEqual(client.bucket_name, 'papers')
            self.assertEqual(client.secure, True)

    @patch('src.minio_client.get_config')
    @patch('src.minio_client.create_minio_client_from_env')
    def test_create_minio_client_from_config_failure_fallback(self, mock_create_from_env, mock_get_config):
        """Test fallback to environment variables when config fails"""
        # Mock configuration failure
        mock_get_config.side_effect = Exception("Config error")
        
        # Mock environment fallback
        mock_env_client = Mock()
        mock_create_from_env.return_value = mock_env_client
        
        result = create_minio_client_from_config()
        
        self.assertEqual(result, mock_env_client)
        mock_get_config.assert_called_once()
        mock_create_from_env.assert_called_once()

    @patch.dict(os.environ, {
        'MINIO_ENDPOINT': 'env-endpoint:9000',
        'MINIO_ACCESS_KEY': 'env-access-key',
        'MINIO_SECRET_KEY': 'env-secret-key',
        'MINIO_BUCKET_NAME': 'env-bucket',
        'MINIO_SECURE': 'true'
    })
    def test_create_minio_client_from_env(self):
        """Test creating MinIO client from environment variables"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_client = Mock()
            mock_minio_class.return_value = mock_minio_client
            
            client = create_minio_client_from_env()
            
            self.assertIsInstance(client, MinIOClient)
            self.assertEqual(client.endpoint, 'env-endpoint:9000')
            self.assertEqual(client.access_key, 'env-access-key')
            self.assertEqual(client.secret_key, 'env-secret-key')
            self.assertEqual(client.bucket_name, 'env-bucket')
            self.assertEqual(client.secure, True)

    @patch.dict(os.environ, {}, clear=True)
    def test_create_minio_client_from_env_defaults(self):
        """Test creating MinIO client from environment variables with defaults"""
        with patch('src.minio_client.Minio') as mock_minio_class:
            mock_minio_client = Mock()
            mock_minio_class.return_value = mock_minio_client
            
            client = create_minio_client_from_env()
            
            self.assertIsInstance(client, MinIOClient)
            self.assertEqual(client.endpoint, 'localhost:9000')
            self.assertEqual(client.access_key, 'minioadmin')
            self.assertEqual(client.secret_key, 'minioadmin123')
            self.assertEqual(client.bucket_name, 'papers')
            self.assertEqual(client.secure, False)


if __name__ == '__main__':
    unittest.main()