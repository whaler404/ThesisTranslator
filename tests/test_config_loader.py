import unittest
import tempfile
import os
import yaml
from unittest.mock import patch

from config.config_loader import ConfigLoader, get_config, load_config
from tests.test_config import MINIO_TEST_CONFIG, TEST_ENV_VARS


class TestConfigLoader(unittest.TestCase):
    """Test cases for configuration loader"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        os.rmdir(self.temp_dir)

    def test_config_loader_with_file(self):
        """Test configuration loader with YAML file"""
        test_config = {
            'minio': {
                'endpoint': MINIO_TEST_CONFIG['endpoint'],
                'access_key': MINIO_TEST_CONFIG['access_key'],
                'secret_key': MINIO_TEST_CONFIG['secret_key'],
                'bucket_name': MINIO_TEST_CONFIG['bucket_name'],
                'secure': True
            },
            'service': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            }
        }

        # Write test configuration
        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Test configuration loading
        config = ConfigLoader(self.test_config_file)
        
        self.assertEqual(config.get('minio.endpoint'), MINIO_TEST_CONFIG['endpoint'])
        self.assertEqual(config.get('minio.access_key'), MINIO_TEST_CONFIG['access_key'])
        self.assertEqual(config.get('minio.secret_key'), MINIO_TEST_CONFIG['secret_key'])
        self.assertEqual(config.get('minio.bucket_name'), MINIO_TEST_CONFIG['bucket_name'])
        self.assertEqual(config.get('minio.secure'), True)
        self.assertEqual(config.get('service.port'), 5000)

    def test_config_loader_with_env_vars(self):
        """Test configuration loader with environment variables"""
        test_config = {
            'minio': {
                'endpoint': 'file-endpoint:9000',
                'access_key': 'file-access-key',
                'secret_key': 'file-secret-key',
                'bucket_name': 'file-bucket',
                'secure': False
            }
        }

        # Write test configuration
        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Set environment variables
        env_vars = TEST_ENV_VARS.copy()
        env_vars['MINIO_ENDPOINT'] = 'env-endpoint:9000'
        env_vars['MINIO_ACCESS_KEY'] = 'env-access-key'
        env_vars['MINIO_SECRET_KEY'] = 'env-secret-key'
        env_vars['MINIO_BUCKET_NAME'] = 'env-bucket'
        env_vars['MINIO_SECURE'] = 'true'
        env_vars['MINIO_SERVICE_PORT'] = '8080'

        with patch.dict(os.environ, env_vars):
            config = ConfigLoader(self.test_config_file)
            
            # Environment variables should override file values
            self.assertEqual(config.get('minio.endpoint'), 'env-endpoint:9000')
            self.assertEqual(config.get('minio.access_key'), 'env-access-key')
            self.assertEqual(config.get('minio.secret_key'), 'env-secret-key')
            self.assertEqual(config.get('minio.bucket_name'), 'env-bucket')
            self.assertEqual(config.get('minio.secure'), True)
            self.assertEqual(config.get('service.port'), 8080)

    def test_config_loader_no_file(self):
        """Test configuration loader without YAML file"""
        env_vars = TEST_ENV_VARS.copy()
        env_vars['MINIO_ENDPOINT'] = 'env-endpoint:9000'
        env_vars['MINIO_ACCESS_KEY'] = 'env-access-key'
        env_vars['MINIO_SECRET_KEY'] = 'env-secret-key'
        env_vars['MINIO_BUCKET_NAME'] = 'env-bucket'
        
        with patch.dict(os.environ, env_vars):
            config = ConfigLoader('/non/existent/file.yaml')
            
            self.assertEqual(config.get('minio.endpoint'), 'env-endpoint:9000')
            self.assertEqual(config.get('minio.access_key'), 'env-access-key')
            self.assertEqual(config.get('minio.secret_key'), 'env-secret-key')
            self.assertEqual(config.get('minio.bucket_name'), 'env-bucket')
            self.assertEqual(config.get('minio.secure'), False)

    def test_config_loader_defaults(self):
        """Test configuration loader defaults"""
        config = ConfigLoader('/non/existent/file.yaml')
        
        # Test default values
        self.assertEqual(config.get('minio.endpoint'), MINIO_TEST_CONFIG['endpoint'])
        self.assertEqual(config.get('minio.access_key'), MINIO_TEST_CONFIG['access_key'])
        self.assertEqual(config.get('minio.secret_key'), MINIO_TEST_CONFIG['secret_key'])
        self.assertEqual(config.get('minio.bucket_name'), MINIO_TEST_CONFIG['bucket_name'])
        self.assertEqual(config.get('minio.secure'), MINIO_TEST_CONFIG['secure'])
        self.assertEqual(config.get('service.port'), 5000)

    def test_get_minio_config(self):
        """Test getting MinIO configuration"""
        test_config = {
            'minio': {
                'endpoint': MINIO_TEST_CONFIG['endpoint'],
                'access_key': MINIO_TEST_CONFIG['access_key'],
                'secret_key': MINIO_TEST_CONFIG['secret_key'],
                'bucket_name': MINIO_TEST_CONFIG['bucket_name'],
                'secure': True
            }
        }

        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        config = ConfigLoader(self.test_config_file)
        minio_config = config.get_minio_config()
        
        self.assertEqual(minio_config['endpoint'], MINIO_TEST_CONFIG['endpoint'])
        self.assertEqual(minio_config['access_key'], MINIO_TEST_CONFIG['access_key'])
        self.assertEqual(minio_config['secret_key'], MINIO_TEST_CONFIG['secret_key'])
        self.assertEqual(minio_config['bucket_name'], MINIO_TEST_CONFIG['bucket_name'])
        self.assertEqual(minio_config['secure'], True)

    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        test_config = {
            'minio': {
                'endpoint': MINIO_TEST_CONFIG['endpoint'],
                'access_key': MINIO_TEST_CONFIG['access_key'],
                'secret_key': MINIO_TEST_CONFIG['secret_key'],
                'bucket_name': MINIO_TEST_CONFIG['bucket_name'],
                'secure': MINIO_TEST_CONFIG['secure']
            },
            'openai': {
                'api_key': 'test-api-key'
            },
            'service': {
                'port': 5000
            },
            'download': {
                'timeout': 30
            }
        }

        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        config = ConfigLoader(self.test_config_file)
        self.assertTrue(config.validate_config())

    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        test_config = {
            'minio': {
                'endpoint': '',  # Missing required field
                'access_key': 'test-access-key',
                'secret_key': 'test-secret-key',
                'bucket_name': 'test-bucket'
            }
        }

        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        config = ConfigLoader(self.test_config_file)
        self.assertFalse(config.validate_config())

    def test_global_config_instance(self):
        """Test global configuration instance"""
        # Clear global config
        import config.config_loader
        config.config_loader._config = None
        
        test_config = {
            'minio': {
                'endpoint': MINIO_TEST_CONFIG['endpoint'],
                'access_key': MINIO_TEST_CONFIG['access_key'],
                'secret_key': MINIO_TEST_CONFIG['secret_key'],
                'bucket_name': MINIO_TEST_CONFIG['bucket_name']
            }
        }

        with open(self.test_config_file, 'w') as f:
            yaml.dump(test_config, f)

        # Test global config functions
        config1 = get_config()
        config2 = get_config()
        
        # Should be the same instance
        self.assertIs(config1, config2)
        self.assertEqual(config1.get('minio.endpoint'), MINIO_TEST_CONFIG['endpoint'])

        # Test load_config function
        config3 = load_config(self.test_config_file)
        config4 = get_config()
        
        # Should be the same instance after reload
        self.assertIs(config3, config4)
        self.assertEqual(config3.get('minio.endpoint'), 'global-endpoint:9000')


if __name__ == '__main__':
    unittest.main()