"""
Test configuration constants for MinIO tests
"""

# MinIO configuration matching the actual config/minio_config.yaml
MINIO_TEST_CONFIG = {
    'endpoint': 'localhost:9000',
    'access_key': 'minioadmin',
    'secret_key': 'minioadmin123',
    'bucket_name': 'papers',
    'secure': False
}

# Test file paths
TEST_PDF_PATH = './downloads/ppo_in_rlhf.pdf'
TEST_OUTPUT_DIR = './test_output'
TEST_TEMP_DIR = './test_temp'

# Test object names
TEST_OBJECT_NAME = 'test_ppo_in_rlhf.pdf'
TEST_DOWNLOAD_OBJECT = 'downloaded_test.pdf'

# Environment variables for testing
TEST_ENV_VARS = {
    'MINIO_ENDPOINT': 'localhost:9000',
    'MINIO_ACCESS_KEY': 'minioadmin',
    'MINIO_SECRET_KEY': 'minioadmin123',
    'MINIO_BUCKET_NAME': 'papers',
    'MINIO_SECURE': 'false'
}

# Service configuration
SERVICE_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False
}