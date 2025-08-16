import argparse
import logging
import os
import sys
from typing import Dict, Any
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
        
        logger.info("论文翻译器初始化完成")
    
    def translate_pdf(self, pdf_path: str, output_path: str) -> bool:
        """
        翻译PDF文件
        
        Args:
            pdf_path (str): 输入PDF文件路径
            output_path (str): 输出Markdown文件路径
            
        Returns:
            bool: 翻译是否成功
        """
        start_time = time.time()
        logger.info(f"开始翻译PDF文件: {pdf_path}")
        
        try:
            # 1. PDF文本解析
            logger.info("步骤1: 解析PDF文本")
            with PDFTextExtractor(pdf_path) as extractor:
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
                    "source": os.path.basename(pdf_path),
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
    parser.add_argument("input", help="输入PDF文件路径")
    parser.add_argument("output", help="输出Markdown文件路径")
    parser.add_argument("--model", default=OPENAI_MODEL, help="OpenAI模型")
    parser.add_argument("--base-url", default=OPENAI_BASE_URL, help="OpenAI API基础URL")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE, help="文本块大小")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES, help="最大重试次数")
    parser.add_argument("--temperature", type=float, default=OPENAI_TEMPERATURE, help="生成温度")
    parser.add_argument("--timeout", type=int, default=OPENAI_TIMEOUT, help="超时时间(秒)")
    parser.add_argument("--include-toc", action="store_true", default=INCLUDE_TOC, help="包含目录")
    parser.add_argument("--include-metadata", action="store_true", default=INCLUDE_METADATA, help="包含元数据")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
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
        
        # 执行翻译
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