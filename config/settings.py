import os
from typing import Optional, Tuple

# OpenAI配置
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL: Optional[str] = os.getenv('OPENAI_BASE_URL', None)
OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')
OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
OPENAI_TIMEOUT: int = int(os.getenv('OPENAI_TIMEOUT', '60'))

# 文本处理配置
CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '1000'))
OVERLAP_SIZE: int = int(os.getenv('OVERLAP_SIZE', '100'))
MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))

# 输出配置
OUTPUT_FORMAT: str = os.getenv('OUTPUT_FORMAT', 'markdown')
INCLUDE_TOC: bool = os.getenv('INCLUDE_TOC', 'True').lower() == 'true'
INCLUDE_METADATA: bool = os.getenv('INCLUDE_METADATA', 'True').lower() == 'true'

# 日志配置
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE: str = os.getenv('LOG_FILE', 'logs/translator.log')

# PDF处理配置
PDF_EXTRACT_IMAGES: bool = os.getenv('PDF_EXTRACT_IMAGES', 'False').lower() == 'true'
PDF_PRESERVE_LAYOUT: bool = os.getenv('PDF_PRESERVE_LAYOUT', 'True').lower() == 'true'


def validate_settings() -> tuple[bool, Optional[str]]:
    """
    验证配置设置的有效性
    
    Returns:
        tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not OPENAI_API_KEY:
        return False, "OPENAI_API_KEY 未设置"
    
    if CHUNK_SIZE <= 0:
        return False, "CHUNK_SIZE 必须大于0"
        
    if MAX_RETRIES < 0:
        return False, "MAX_RETRIES 不能为负数"
        
    if OPENAI_TEMPERATURE < 0 or OPENAI_TEMPERATURE > 1:
        return False, "OPENAI_TEMPERATURE 必须在0-1之间"
        
    return True, None