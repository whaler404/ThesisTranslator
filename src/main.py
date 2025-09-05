import argparse
import logging
import os
import sys
from typing import Dict, Any, Optional, List
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import *
from src.pdf_parser import PDFTextExtractor, PDFProcessingError
from src.text_chunker import TextChunker
from src.text_cleaner import TextCleaner, TextCleaningError
from src.text_sorter import TextSorter, TextSortingError
from src.translator import AITranslator, TranslationError
from src.markdown_generator import MarkdownGenerator
from src.minio_client import MinIOClient, create_minio_client_from_config, create_minio_client_from_env
from src.minio_file_interface import MinIOFileInterface, create_minio_file_interface_from_env
from src.paper_downloader import PaperDownloader, create_paper_downloader_from_env

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ThesisTranslator:
    """论文翻译器主控制器"""
    
    def __init__(self, openai_api_key: str = None, **kwargs):
        """
        初始化论文翻译器
        
        Args:
            openai_api_key (str): OpenAI API密钥
            **kwargs: 配置参数
        """
        # 验证配置
        is_valid, error_msg = validate_settings()
        if not is_valid:
            logger.error(f"配置验证失败: {error_msg}")
            raise ValueError(f"配置错误: {error_msg}")
        
        # 使用传入的API密钥或配置中的API密钥
        self.api_key = openai_api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("未提供OpenAI API密钥")
        
        # 配置参数
        self.model = kwargs.get('model', OPENAI_MODEL)
        self.base_url = kwargs.get('base_url', OPENAI_BASE_URL)
        self.chunk_size = kwargs.get('chunk_size', CHUNK_SIZE)
        self.max_retries = kwargs.get('max_retries', MAX_RETRIES)
        self.temperature = kwargs.get('temperature', OPENAI_TEMPERATURE)
        self.max_tokens = kwargs.get('max_tokens', OPENAI_MAX_TOKENS)
        self.timeout = kwargs.get('timeout', OPENAI_TIMEOUT)
        self.include_toc = kwargs.get('include_toc', INCLUDE_TOC)
        self.include_metadata = kwargs.get('include_metadata', INCLUDE_METADATA)
        
        # 初始化各模块
        self.pdf_extractor = None
        self.minio_client = None
        self.minio_file_interface = None
        self.paper_downloader = None
        self.text_chunker = TextChunker(chunk_size=self.chunk_size)
        self.text_cleaner = TextCleaner(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            base_url=self.base_url
        )
        self.text_sorter = TextSorter(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            base_url=self.base_url
        )
        self.translator = AITranslator(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            base_url=self.base_url
        )
        self.markdown_generator = MarkdownGenerator()
        
        # 初始化MinIO相关模块（如果配置了MinIO）
        self._init_minio_modules()
        
        logger.info("论文翻译器初始化完成")
    
    def _init_minio_modules(self):
        """初始化MinIO相关模块"""
        try:
            # 优先使用配置文件，回退到环境变量
            self.minio_client = create_minio_client_from_config()
            self.minio_file_interface = create_minio_file_interface_from_env()  # 保持原样
            self.paper_downloader = create_paper_downloader_from_env()  # 保持原样
            logger.info("MinIO模块初始化成功")
        except Exception as e:
            logger.warning(f"MinIO模块初始化失败: {e}")
            self.minio_client = None
            self.minio_file_interface = None
            self.paper_downloader = None
    
    def translate_pdf(self, pdf_path: str, output_path: str) -> bool:
        """
        翻译PDF文件
        
        Args:
            pdf_path (str): 输入PDF文件路径或MinIO对象名称
            output_path (str): 输出Markdown文件路径
            
        Returns:
            bool: 翻译是否成功
        """
        start_time = time.time()
        logger.info(f"开始翻译PDF文件: {pdf_path}")
        
        # 检查是否为MinIO对象名称（不包含路径分隔符）
        is_minio_object = not os.path.exists(pdf_path) and '/' not in pdf_path and '\\' not in pdf_path
        
        if is_minio_object and self.minio_file_interface:
            # 从MinIO获取文件
            logger.info(f"从MinIO获取文件: {pdf_path}")
            actual_pdf_path = self.minio_file_interface.get_file_from_minio_to_temp(pdf_path, '.pdf')
            if not actual_pdf_path:
                logger.error(f"无法从MinIO获取文件: {pdf_path}")
                return False
            
            try:
                result = self._translate_pdf_file(actual_pdf_path, output_path, pdf_path)
                return result
            finally:
                # 清理临时文件
                if os.path.exists(actual_pdf_path):
                    os.remove(actual_pdf_path)
                    logger.debug(f"清理临时文件: {actual_pdf_path}")
        else:
            # 直接处理本地文件
            return self._translate_pdf_file(pdf_path, output_path, pdf_path)
    
    def _translate_pdf_file(self, actual_pdf_path: str, output_path: str, original_source: str) -> bool:
        """
        翻译PDF文件的内部实现
        
        Args:
            actual_pdf_path (str): 实际的PDF文件路径
            output_path (str): 输出Markdown文件路径
            original_source (str): 原始来源（用于日志）
            
        Returns:
            bool: 翻译是否成功
        """
        start_time = time.time()
        logger.info(f"开始处理PDF文件: {original_source}")
        
        try:
            # 1. PDF文本解析
            logger.info("步骤1: 解析PDF文本")
            with PDFTextExtractor(actual_pdf_path) as extractor:
                text_blocks = extractor.get_reading_order()
            
            if not text_blocks:
                logger.error("未提取到任何文本内容")
                return False
            
            logger.info(f"成功提取 {len(text_blocks)} 个文本块")
            
            # 2. 文本分块
            logger.info("步骤2: 文本分块")
            text_chunks = self.text_chunker.create_chunks(text_blocks)
            logger.info(f"创建了 {len(text_chunks)} 个文本块")
            
            # 3. 文本清洗
            logger.info("步骤3: 文本清洗")
            cleaned_chunks = self.text_cleaner.clean_text_chunks(text_chunks)
            
            # 处理清洗后的输出
            processed_chunks = []
            for chunk in cleaned_chunks:
                processed_chunk = self.text_cleaner.process_cleaned_output(chunk)
                processed_chunks.append(processed_chunk)
            
            # 4. 文本排序
            # logger.info("步骤4: 文本排序")
            # sorted_chunks = self.text_sorter.sort_text_chunks(processed_chunks)
            
            # 5. AI翻译
            logger.info("步骤5: AI翻译")
            # translated_chunks = self.translator.translate_chunks(sorted_chunks)
            translated_chunks = self.translator.translate_chunks(processed_chunks)
            
            # 6. Markdown生成
            logger.info("步骤6: 生成Markdown文档")
            markdown_content = self.markdown_generator.generate_markdown(translated_chunks)
            
            # 添加元数据
            if self.include_metadata:
                metadata = {
                    "title": "翻译论文",
                    "date": time.strftime("%Y-%m-%d"),
                    "source": os.path.basename(original_source),
                    "translator": "ThesisTranslator"
                }
                markdown_content = self.markdown_generator.add_metadata(markdown_content, metadata)
            
            # 添加目录
            if self.include_toc:
                markdown_content = self.markdown_generator.create_table_of_contents(markdown_content)
            
            # 验证Markdown格式
            validation_result = self.markdown_generator.validate_markdown(markdown_content)
            if not validation_result["is_valid"]:
                logger.warning(f"Markdown验证失败: {validation_result['errors']}")
            
            # 保存到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            processing_time = time.time() - start_time
            logger.info(f"翻译完成，耗时: {processing_time:.2f}秒，输出文件: {output_path}")
            
            # 输出统计信息
            translation_stats = self.translator.get_translation_statistics()
            cleaning_stats = self.text_cleaner.get_cleaning_statistics()
            sorting_stats = self.text_sorter.get_sorting_statistics()
            
            logger.info(f"翻译统计: {translation_stats}")
            logger.info(f"清洗统计: {cleaning_stats}")
            logger.info(f"排序统计: {sorting_stats}")
            
            return True
            
        except PDFProcessingError as e:
            logger.error(f"PDF处理错误: {e}")
            return False
        except TranslationError as e:
            logger.error(f"翻译错误: {e}")
            return False
        except Exception as e:
            logger.error(f"翻译过程中发生未知错误: {e}", exc_info=True)
            return False
    
    def process_with_error_handling(self, pdf_path: str, output_path: str) -> Dict[str, Any]:
        """
        带错误处理的处理流程
        
        Args:
            pdf_path (str): 输入PDF路径
            output_path (str): 输出路径
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        start_time = time.time()
        
        try:
            success = self.translate_pdf(pdf_path, output_path)
            
            processing_time = time.time() - start_time
            
            return {
                "success": success,
                "error_count": 0 if success else 1,
                "warning_count": 0,
                "processing_time": processing_time,
                "output_file": output_path if success else None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"处理过程中发生错误: {e}", exc_info=True)
            
            return {
                "success": False,
                "error_count": 1,
                "warning_count": 0,
                "processing_time": processing_time,
                "output_file": None,
                "error_message": str(e)
            }
    
    def get_progress(self) -> Dict[str, Any]:
        """
        获取处理进度
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        # 在当前实现中，我们没有实时进度跟踪
        return {
            "current_stage": "unknown",
            "progress_percentage": 0,
            "estimated_time_remaining": 0
        }
    
    def download_paper(self, url: str, object_name: str = None) -> Optional[Dict[str, Any]]:
        """
        下载论文到MinIO
        
        Args:
            url (str): 论文资源链接
            object_name (str): 自定义对象名称
            
        Returns:
            Optional[Dict[str, Any]]: 下载结果信息
        """
        if not self.paper_downloader:
            logger.error("论文下载器未初始化，请检查MinIO配置")
            return None
        
        return self.paper_downloader.download_paper(url, object_name)
    
    def batch_download_papers(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量下载论文到MinIO
        
        Args:
            urls (List[str]): 论文URL列表
            
        Returns:
            List[Dict[str, Any]]: 下载结果列表
        """
        if not self.paper_downloader:
            logger.error("论文下载器未初始化，请检查MinIO配置")
            return []
        
        return self.paper_downloader.batch_download_papers(urls)
    
    def list_minio_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """
        列出MinIO中的文件
        
        Args:
            prefix (str): 文件名前缀过滤
            
        Returns:
            List[Dict[str, Any]]: 文件信息列表
        """
        if not self.minio_client:
            logger.error("MinIO客户端未初始化，请检查MinIO配置")
            return []
        
        return self.minio_client.list_files(prefix)
    
    def translate_from_minio(self, object_name: str, output_path: str) -> bool:
        """
        从MinIO翻译PDF文件
        
        Args:
            object_name (str): MinIO中的对象名称
            output_path (str): 输出Markdown文件路径
            
        Returns:
            bool: 翻译是否成功
        """
        return self.translate_pdf(object_name, output_path)
    
    def get_minio_statistics(self) -> Dict[str, Any]:
        """
        获取MinIO统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.minio_file_interface:
            logger.error("MinIO文件接口未初始化，请检查MinIO配置")
            return {}
        
        return self.minio_file_interface.get_processing_statistics()
    
    def set_configuration(self, config: Dict[str, Any]):
        """
        设置配置参数
        
        Args:
            config (Dict[str, Any]): 配置参数字典
        """
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"更新配置: {key} = {value}")
    
    def get_logs(self, level: str = "INFO") -> list:
        """
        获取日志信息
        
        Args:
            level (str): 日志级别
            
        Returns:
            list: 日志条目列表
        """
        # 在当前实现中，日志直接写入文件，这里返回空列表
        return []

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="英文论文翻译器")
    parser.add_argument("input", nargs='?', help="输入PDF文件路径或MinIO对象名称")
    parser.add_argument("output", nargs='?', help="输出Markdown文件路径")
    parser.add_argument("--model", default=OPENAI_MODEL, help="OpenAI模型")
    parser.add_argument("--base-url", default=OPENAI_BASE_URL, help="OpenAI API基础URL")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="文本块大小")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES, help="最大重试次数")
    parser.add_argument("--temperature", type=float, default=OPENAI_TEMPERATURE, help="生成温度")
    parser.add_argument("--timeout", type=int, default=OPENAI_TIMEOUT, help="超时时间(秒)")
    parser.add_argument("--include-toc", action="store_true", default=INCLUDE_TOC, help="包含目录")
    parser.add_argument("--include-metadata", action="store_true", default=INCLUDE_METADATA, help="包含元数据")
    parser.add_argument("--download-paper", help="下载论文到MinIO")
    parser.add_argument("--batch-download", help="批量下载论文，提供URL文件路径")
    parser.add_argument("--list-files", action="store_true", help="列出MinIO中的文件")
    parser.add_argument("--from-minio", action="store_true", help="从MinIO获取文件")
    parser.add_argument("--start-service", action="store_true", help="启动MinIO HTTP服务")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 启动MinIO服务模式
        if args.start_service:
            from src.minio_service import create_minio_service_from_env
            
            service = create_minio_service_from_env()
            host = os.getenv('MINIO_SERVICE_HOST', '0.0.0.0')
            port = int(os.getenv('MINIO_SERVICE_PORT', '5000'))
            debug = os.getenv('MINIO_SERVICE_DEBUG', 'false').lower() == 'true'
            
            print(f"启动MinIO HTTP服务: {host}:{port}")
            service.run(host=host, port=port, debug=debug)
            return
        
        # 创建翻译器实例
        translator = ThesisTranslator(
            model=args.model,
            base_url=args.base_url,
            chunk_size=args.chunk_size,
            max_retries=args.max_retries,
            temperature=args.temperature,
            timeout=args.timeout,
            include_toc=args.include_toc,
            include_metadata=args.include_metadata
        )
        
        # 处理不同的操作模式
        if args.download_paper:
            # 下载论文模式
            result = translator.download_paper(args.download_paper)
            if result:
                print(f"论文下载成功: {result['object_name']}")
                sys.exit(0)
            else:
                print("论文下载失败")
                sys.exit(1)
                
        elif args.batch_download:
            # 批量下载模式
            with open(args.batch_download, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            results = translator.batch_download_papers(urls)
            success_count = len([r for r in results if r])
            print(f"批量下载完成: {success_count}/{len(urls)} 成功")
            sys.exit(0 if success_count > 0 else 1)
            
        elif args.list_files:
            # 列出文件模式
            files = translator.list_minio_files()
            print(f"MinIO中的文件 (共{len(files)}个):")
            for file in files:
                print(f"  - {file['name']} ({file['size']} bytes)")
            sys.exit(0)
            
        else:
            # 翻译模式
            if not args.input or not args.output:
                print("错误: 翻译模式需要指定输入和输出文件")
                parser.print_help()
                sys.exit(1)
            
            if args.from_minio:
                success = translator.translate_from_minio(args.input, args.output)
            else:
                success = translator.translate_pdf(args.input, args.output)
            
            if success:
                print(f"翻译完成: {args.output}")
                sys.exit(0)
            else:
                print("翻译失败，请查看日志了解详情")
                sys.exit(1)
            
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)
        print(f"程序执行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()