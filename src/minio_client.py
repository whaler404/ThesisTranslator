"""
MinIO Client Module
提供MinIO对象存储的客户端操作功能
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import hashlib
import mimetypes

# Import configuration loader
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
try:
    from config_loader import get_config
except ImportError:
    # Fallback if config_loader is not available
    get_config = None

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO对象存储客户端"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, 
                 bucket_name: str = "papers", secure: bool = False):
        """
        初始化MinIO客户端
        
        Args:
            endpoint (str): MinIO服务地址，如 'localhost:9000'
            access_key (str): 访问密钥
            secret_key (str): 秘密密钥
            bucket_name (str): 存储桶名称，默认为 'papers'
            secure (bool): 是否使用HTTPS，默认False
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        
        # 初始化MinIO客户端
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
        
        logger.info(f"MinIO客户端初始化成功: {endpoint}/{bucket_name}")
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"创建存储桶失败: {e}")
            raise
    
    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> bool:
        """
        上传文件到MinIO
        
        Args:
            file_path (str): 本地文件路径
            object_name (str): 对象名称，如果为None则使用文件名
            
        Returns:
            bool: 上传是否成功
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            if object_name is None:
                object_name = os.path.basename(file_path)
            
            # 获取文件MIME类型
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # 上传文件
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            
            logger.info(f"文件上传成功: {file_path} -> {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件上传失败: {e}")
            return False
    
    def upload_from_bytes(self, data: bytes, object_name: str, 
                         content_type: str = 'application/octet-stream') -> bool:
        """
        从字节数据上传到MinIO
        
        Args:
            data (bytes): 文件数据
            object_name (str): 对象名称
            content_type (str): 内容类型
            
        Returns:
            bool: 上传是否成功
        """
        try:
            data_stream = BytesIO(data)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            
            logger.info(f"字节数据上传成功: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"字节数据上传失败: {e}")
            return False
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        从MinIO下载文件
        
        Args:
            object_name (str): 对象名称
            file_path (str): 本地保存路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 下载文件
            self.client.fget_object(self.bucket_name, object_name, file_path)
            
            logger.info(f"文件下载成功: {object_name} -> {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"文件下载失败: {e}")
            return False
    
    def download_to_bytes(self, object_name: str) -> Optional[bytes]:
        """
        从MinIO下载到字节数据
        
        Args:
            object_name (str): 对象名称
            
        Returns:
            Optional[bytes]: 文件数据，失败返回None
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            return data
            
        except S3Error as e:
            logger.error(f"字节数据下载失败: {e}")
            return None
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """
        列出存储桶中的文件
        
        Args:
            prefix (str): 文件名前缀过滤
            
        Returns:
            List[Dict[str, Any]]: 文件信息列表
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            file_list = []
            
            for obj in objects:
                file_info = {
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'content_type': self._get_content_type(obj.object_name)
                }
                file_list.append(file_info)
            
            return file_list
            
        except S3Error as e:
            logger.error(f"列出文件失败: {e}")
            return []
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name (str): 对象名称
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name (str): 对象名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"文件删除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            object_name (str): 对象名称
            
        Returns:
            Optional[Dict[str, Any]]: 文件信息
        """
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                'name': object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': self._get_content_type(object_name)
            }
        except S3Error as e:
            logger.error(f"获取文件信息失败: {e}")
            return None
    
    def _get_content_type(self, object_name: str) -> str:
        """
        获取文件内容类型
        
        Args:
            object_name (str): 对象名称
            
        Returns:
            str: 内容类型
        """
        return mimetypes.guess_type(object_name)[0] or 'application/octet-stream'
    
    def generate_safe_filename(self, url: str, content_type: str = None) -> str:
        """
        生成安全的文件名
        
        Args:
            url (str): 原始URL
            content_type (str): 内容类型
            
        Returns:
            str: 安全的文件名
        """
        # 从URL中提取文件名
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # 如果没有文件名或扩展名，使用哈希值
        if not filename or '.' not in filename:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if content_type:
                extension = self._get_extension_from_content_type(content_type)
                filename = f"{url_hash}{extension}"
            else:
                filename = f"{url_hash}.pdf"
        
        # 清理文件名
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        return filename
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """
        根据内容类型获取文件扩展名
        
        Args:
            content_type (str): 内容类型
            
        Returns:
            str: 文件扩展名
        """
        content_type_map = {
            'application/pdf': '.pdf',
            'text/plain': '.txt',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/postscript': '.ps',
            'application/x-tex': '.tex'
        }
        
        return content_type_map.get(content_type.lower(), '.pdf')
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的临时访问URL
        
        Args:
            object_name (str): 对象名称
            expires (int): 过期时间（秒）
            
        Returns:
            Optional[str]: 临时访问URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"生成访问URL失败: {e}")
            return None
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的临时访问URL（别名方法，为了向后兼容）
        
        Args:
            object_name (str): 对象名称
            expires (int): 过期时间（秒）
            
        Returns:
            Optional[str]: 临时访问URL
        """
        return self.get_file_url(object_name, expires)
    
    def rename_file(self, old_object_name: str, new_object_name: str) -> bool:
        """
        重命名MinIO中的文件
        
        Args:
            old_object_name (str): 原对象名称
            new_object_name (str): 新对象名称
            
        Returns:
            bool: 重命名是否成功
        """
        try:
            # 检查源文件是否存在
            if not self.file_exists(old_object_name):
                logger.error(f"源文件不存在: {old_object_name}")
                return False
            
            # 检查目标文件是否已存在
            if self.file_exists(new_object_name):
                logger.error(f"目标文件已存在: {new_object_name}")
                return False
            
            # 复制文件到新名称
            source_data = self.download_to_bytes(old_object_name)
            if not source_data:
                logger.error(f"无法读取源文件: {old_object_name}")
                return False
            
            # 获取源文件的content type
            content_type = self._get_content_type(old_object_name)
            
            # 上传到新名称
            success = self.upload_from_bytes(source_data, new_object_name, content_type)
            if not success:
                logger.error(f"无法上传到新名称: {new_object_name}")
                return False
            
            # 删除原文件
            delete_success = self.delete_file(old_object_name)
            if not delete_success:
                logger.warning(f"重命名成功但删除原文件失败: {old_object_name}")
            
            logger.info(f"文件重命名成功: {old_object_name} -> {new_object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"文件重命名失败: {e}")
            return False


def create_minio_client_from_config() -> MinIOClient:
    """
    从配置文件创建MinIO客户端
    
    Returns:
        MinIOClient: MinIO客户端实例
    """
    try:
        if get_config is None:
            logger.warning("配置加载器不可用，回退到环境变量")
            return create_minio_client_from_env()
            
        config = get_config()
        minio_config = config.get_minio_config()
        
        endpoint = minio_config.get('endpoint', 'localhost:9000')
        access_key = minio_config.get('access_key', 'minioadmin')
        secret_key = minio_config.get('secret_key', 'minioadmin123')
        bucket_name = minio_config.get('bucket_name', 'papers')
        secure = minio_config.get('secure', False)
        
        return MinIOClient(endpoint, access_key, secret_key, bucket_name, secure)
    except Exception as e:
        logger.error(f"从配置创建MinIO客户端失败: {e}")
        # 回退到环境变量
        return create_minio_client_from_env()


def create_minio_client_from_env() -> MinIOClient:
    """
    从环境变量创建MinIO客户端（向后兼容）
    
    Returns:
        MinIOClient: MinIO客户端实例
    """
    endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
    bucket_name = os.getenv('MINIO_BUCKET_NAME', 'papers')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    
    return MinIOClient(endpoint, access_key, secret_key, bucket_name, secure)