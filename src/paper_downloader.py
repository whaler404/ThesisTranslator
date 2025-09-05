"""
Paper Download Module
提供从资源链接自动下载论文的功能
"""

import os
import logging
import requests
import urllib.parse
from typing import List, Optional, Dict, Any
from pathlib import Path
import time
import hashlib
import mimetypes
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import re

from .minio_client import MinIOClient

logger = logging.getLogger(__name__)


class PaperDownloader:
    """论文下载器"""
    
    def __init__(self, minio_client: MinIOClient, user_agent: str = None,
                 timeout: int = 30, max_retries: int = 3):
        """
        初始化论文下载器
        
        Args:
            minio_client (MinIOClient): MinIO客户端实例
            user_agent (str): 用户代理字符串
            timeout (int): 下载超时时间（秒）
            max_retries (int): 最大重试次数
        """
        self.minio_client = minio_client
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 创建会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # 支持的文件类型
        self.supported_extensions = {'.pdf', '.ps', '.tex', '.txt', '.doc', '.docx'}
        self.supported_content_types = {
            'application/pdf',
            'application/postscript',
            'application/x-tex',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        logger.info("论文下载器初始化成功")
    
    def download_paper(self, url: str, object_name: str = None) -> Optional[Dict[str, Any]]:
        """
        下载论文并保存到MinIO
        
        Args:
            url (str): 论文资源链接
            object_name (str): 自定义对象名称
            
        Returns:
            Optional[Dict[str, Any]]: 下载结果信息
        """
        try:
            logger.info(f"开始下载论文: {url}")
            
            # 验证URL
            if not self._is_valid_url(url):
                logger.error(f"无效的URL: {url}")
                return None
            
            # 检查robots.txt
            if not self._check_robots_txt(url):
                logger.warning(f"robots.txt禁止访问: {url}")
                return None
            
            # 下载文件
            file_data, content_type, filename = self._download_with_retry(url)
            if not file_data:
                logger.error(f"下载失败: {url}")
                return None
            
            # 生成对象名称
            if object_name is None:
                object_name = self.minio_client.generate_safe_filename(url, content_type)
            
            # 上传到MinIO
            success = self.minio_client.upload_from_bytes(file_data, object_name, content_type)
            
            if success:
                result = {
                    'url': url,
                    'object_name': object_name,
                    'size': len(file_data),
                    'content_type': content_type,
                    'original_filename': filename,
                    'download_time': time.time()
                }
                logger.info(f"论文下载成功: {object_name}")
                return result
            else:
                logger.error(f"上传到MinIO失败: {object_name}")
                return None
                
        except Exception as e:
            logger.error(f"下载论文时发生错误: {e}")
            return None
    
    def batch_download_papers(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量下载论文
        
        Args:
            urls (List[str]): 论文URL列表
            
        Returns:
            List[Dict[str, Any]]: 下载结果列表
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"批量下载进度: {i+1}/{len(urls)} - {url}")
            
            result = self.download_paper(url)
            if result:
                results.append(result)
            
            # 添加延迟避免过于频繁的请求
            if i < len(urls) - 1:
                time.sleep(1)
        
        logger.info(f"批量下载完成: {len(results)}/{len(urls)} 成功")
        return results
    
    def extract_papers_from_arxiv(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        从arXiv下载论文
        
        Args:
            arxiv_id (str): arXiv论文ID，如 '2101.00001'
            
        Returns:
            Optional[Dict[str, Any]]: 下载结果
        """
        try:
            # 构建arXiv PDF下载链接
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            logger.info(f"从arXiv下载论文: {arxiv_id}")
            
            return self.download_paper(pdf_url, f"arxiv_{arxiv_id}.pdf")
            
        except Exception as e:
            logger.error(f"从arXiv下载失败: {e}")
            return None
    
    def extract_papers_from_springer(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        从Springer下载论文
        
        Args:
            doi (str): 论文DOI，如 '10.1007/s11276-021-02781-7'
            
        Returns:
            Optional[Dict[str, Any]]: 下载结果
        """
        try:
            # 构建Springer下载链接
            pdf_url = f"https://link.springer.com/content/pdf/{doi}.pdf"
            
            logger.info(f"从Springer下载论文: {doi}")
            
            return self.download_paper(pdf_url, f"springer_{doi.replace('/', '_')}.pdf")
            
        except Exception as e:
            logger.error(f"从Springer下载失败: {e}")
            return None
    
    def extract_papers_from_ieee(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        从IEEE下载论文
        
        Args:
            article_id (str): IEEE文章ID
            
        Returns:
            Optional[Dict[str, Any]]: 下载结果
        """
        try:
            # 构建IEEE下载链接
            pdf_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={article_id}"
            
            logger.info(f"从IEEE下载论文: {article_id}")
            
            return self.download_paper(pdf_url, f"ieee_{article_id}.pdf")
            
        except Exception as e:
            logger.error(f"从IEEE下载失败: {e}")
            return None
    
    def is_paper_already_downloaded(self, url: str) -> bool:
        """
        检查论文是否已经下载过
        
        Args:
            url (str): 论文URL
            
        Returns:
            bool: 是否已下载
        """
        try:
            # 生成预期的对象名称
            object_name = self.minio_client.generate_safe_filename(url)
            return self.minio_client.file_exists(object_name)
        except Exception as e:
            logger.error(f"检查下载状态失败: {e}")
            return False
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """
        获取下载统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            files = self.minio_client.list_files()
            
            total_files = len(files)
            total_size = sum(f['size'] for f in files)
            
            # 按文件类型统计
            type_stats = {}
            for file in files:
                ext = Path(file['name']).suffix.lower()
                type_stats[ext] = type_stats.get(ext, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'type_distribution': type_stats,
                'recent_downloads': sorted(files, key=lambda x: x['last_modified'], reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def _is_valid_url(self, url: str) -> bool:
        """
        验证URL是否有效
        
        Args:
            url (str): URL字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _check_robots_txt(self, url: str) -> bool:
        """
        检查robots.txt是否允许访问
        
        Args:
            url (str): URL字符串
            
        Returns:
            bool: 是否允许访问
        """
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(self.user_agent, url)
            
        except Exception as e:
            logger.warning(f"检查robots.txt失败: {e}")
            return True  # 如果无法检查，默认允许访问
    
    def _download_with_retry(self, url: str) -> tuple:
        """
        带重试机制的下载
        
        Args:
            url (str): 下载URL
            
        Returns:
            tuple: (data, content_type, filename)
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                # 获取文件名
                filename = self._extract_filename_from_response(response, url)
                
                # 检查内容类型
                content_type = response.headers.get('content-type', '').split(';')[0]
                if content_type not in self.supported_content_types:
                    logger.warning(f"不支持的内容类型: {content_type}")
                    return None, None, None
                
                # 读取数据
                data = response.content
                
                logger.info(f"下载成功: {url} ({len(data)} bytes)")
                return data, content_type, filename
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        return None, None, None
    
    def _extract_filename_from_response(self, response: requests.Response, url: str) -> str:
        """
        从响应中提取文件名
        
        Args:
            response (requests.Response): HTTP响应
            url (str): 原始URL
            
        Returns:
            str: 文件名
        """
        # 尝试从Content-Disposition头获取文件名
        content_disposition = response.headers.get('content-disposition', '')
        if content_disposition:
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                return filename_match.group(1)
        
        # 从URL中提取文件名
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # 如果没有扩展名，添加默认扩展名
        if '.' not in filename:
            content_type = response.headers.get('content-type', '').split(';')[0]
            extension = self._get_extension_from_content_type(content_type)
            filename += extension
        
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


def create_paper_downloader_from_env() -> PaperDownloader:
    """
    从环境变量创建论文下载器
    
    Returns:
        PaperDownloader: 论文下载器实例
    """
    from .minio_client import create_minio_client_from_env
    
    minio_client = create_minio_client_from_env()
    timeout = int(os.getenv('DOWNLOAD_TIMEOUT', '30'))
    max_retries = int(os.getenv('DOWNLOAD_MAX_RETRIES', '3'))
    
    return PaperDownloader(minio_client, timeout=timeout, max_retries=max_retries)