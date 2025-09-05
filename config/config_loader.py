"""
Configuration loader for MinIO integration.
Loads configuration from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Configuration loader for ThesisTranslator MinIO integration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to configuration YAML file. If None, uses default path.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        return os.path.join(os.path.dirname(__file__), 'minio_config.yaml')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and environment variables."""
        config = {}
        
        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_path}: {e}")
                config = {}
        
        # Override with environment variables
        config = self._override_with_env_vars(config)
        
        return config
    
    def _override_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        
        # MinIO settings
        if 'minio' not in config:
            config['minio'] = {}
        
        config['minio']['endpoint'] = os.getenv('MINIO_ENDPOINT', config['minio'].get('endpoint', 'localhost:9000'))
        config['minio']['access_key'] = os.getenv('MINIO_ACCESS_KEY', config['minio'].get('access_key', 'minioadmin'))
        config['minio']['secret_key'] = os.getenv('MINIO_SECRET_KEY', config['minio'].get('secret_key', 'minioadmin123'))
        config['minio']['bucket_name'] = os.getenv('MINIO_BUCKET_NAME', config['minio'].get('bucket_name', 'papers'))
        config['minio']['secure'] = os.getenv('MINIO_SECURE', str(config['minio'].get('secure', False))).lower() == 'true'
        
        # Service settings
        if 'service' not in config:
            config['service'] = {}
        
        config['service']['host'] = os.getenv('MINIO_SERVICE_HOST', config['service'].get('host', '0.0.0.0'))
        config['service']['port'] = int(os.getenv('MINIO_SERVICE_PORT', config['service'].get('port', '5000')))
        config['service']['debug'] = os.getenv('MINIO_SERVICE_DEBUG', str(config['service'].get('debug', False))).lower() == 'true'
        
        # Download settings
        if 'download' not in config:
            config['download'] = {}
        
        config['download']['timeout'] = int(os.getenv('DOWNLOAD_TIMEOUT', config['download'].get('timeout', '30')))
        config['download']['max_retries'] = int(os.getenv('DOWNLOAD_MAX_RETRIES', config['download'].get('max_retries', '3')))
        config['download']['user_agent'] = os.getenv('DOWNLOAD_USER_AGENT', config['download'].get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'))
        
        # OpenAI settings
        if 'openai' not in config:
            config['openai'] = {}
        
        config['openai']['api_key'] = os.getenv('OPENAI_API_KEY', config['openai'].get('api_key', ''))
        config['openai']['model'] = os.getenv('OPENAI_MODEL', config['openai'].get('model', 'gpt-4'))
        config['openai']['base_url'] = os.getenv('OPENAI_BASE_URL', config['openai'].get('base_url', 'https://api.openai.com/v1'))
        
        # Text processing settings
        if 'text_processing' not in config:
            config['text_processing'] = {}
        
        config['text_processing']['chunk_size'] = int(os.getenv('CHUNK_SIZE', config['text_processing'].get('chunk_size', '1000')))
        config['text_processing']['max_retries'] = int(os.getenv('MAX_RETRIES', config['text_processing'].get('max_retries', '3')))
        config['text_processing']['timeout'] = int(os.getenv('OPENAI_TIMEOUT', config['text_processing'].get('timeout', '60')))
        
        # Logging settings
        if 'logging' not in config:
            config['logging'] = {}
        
        config['logging']['level'] = os.getenv('LOG_LEVEL', config['logging'].get('level', 'INFO'))
        config['logging']['file'] = os.getenv('LOG_FILE', config['logging'].get('file', 'logs/translator.log'))
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'minio.endpoint')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_minio_config(self) -> Dict[str, Any]:
        """Get MinIO configuration."""
        return self.get('minio', {})
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration."""
        return self.get('service', {})
    
    def get_download_config(self) -> Dict[str, Any]:
        """Get download configuration."""
        return self.get('download', {})
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return self.get('openai', {})
    
    def get_text_processing_config(self) -> Dict[str, Any]:
        """Get text processing configuration."""
        return self.get('text_processing', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.get('storage', {})
    
    def create_directories(self):
        """Create necessary directories based on configuration."""
        directories = [
            self.get('minio.data_directory', './minio/data'),
            self.get('minio.config_directory', './minio/config'),
            self.get('minio.backup_directory', './minio/backup'),
            self.get('logging.file', 'logs/translator.log').rsplit('/', 1)[0],
            'output',
            'temp'
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"Created directory: {directory}")
    
    def validate_config(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Check required MinIO settings
        minio_config = self.get_minio_config()
        if not minio_config.get('endpoint'):
            errors.append("MinIO endpoint is required")
        if not minio_config.get('access_key'):
            errors.append("MinIO access key is required")
        if not minio_config.get('secret_key'):
            errors.append("MinIO secret key is required")
        if not minio_config.get('bucket_name'):
            errors.append("MinIO bucket name is required")
        
        # Check OpenAI settings
        openai_config = self.get_openai_config()
        if not openai_config.get('api_key'):
            errors.append("OpenAI API key is required")
        
        # Check service settings
        service_config = self.get_service_config()
        port = service_config.get('port')
        if port and not (1 <= port <= 65535):
            errors.append(f"Invalid service port: {port}")
        
        # Check download settings
        download_config = self.get_download_config()
        timeout = download_config.get('timeout')
        if timeout and timeout <= 0:
            errors.append(f"Invalid download timeout: {timeout}")
        
        if errors:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return yaml.dump(self.config, default_flow_style=False, indent=2)


# Global configuration instance
_config = None


def get_config() -> ConfigLoader:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config


def load_config(config_path: Optional[str] = None) -> ConfigLoader:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration loader instance
    """
    global _config
    _config = ConfigLoader(config_path)
    return _config


def reload_config():
    """Reload global configuration."""
    global _config
    if _config is not None:
        _config = ConfigLoader(_config.config_path)


# Convenience functions
def get_minio_endpoint() -> str:
    """Get MinIO endpoint."""
    return get_config().get('minio.endpoint', 'localhost:9000')


def get_minio_bucket_name() -> str:
    """Get MinIO bucket name."""
    return get_config().get('minio.bucket_name', 'papers')


def get_service_port() -> int:
    """Get service port."""
    return get_config().get('service.port', 5000)


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return get_config().get('openai.api_key', '')


if __name__ == '__main__':
    # Test configuration loading
    config = get_config()
    print("Configuration loaded successfully:")
    print(f"MinIO endpoint: {config.get_minio_config()}")
    print(f"Service port: {config.get_service_config()}")
    print(f"OpenAI model: {config.get_openai_config()}")
    
    # Create directories
    config.create_directories()
    
    # Validate configuration
    if config.validate_config():
        print("Configuration is valid")
    else:
        print("Configuration has errors")