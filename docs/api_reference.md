# 英文论文翻译器 - API参考文档

## 概述

本文档详细描述了英文论文翻译器项目中各个模块的API接口、参数说明和使用示例。

## 核心数据结构

### TextBlock

```python
@dataclass
class TextBlock:
    """文本块数据结构"""
    text: str                                    # 文本内容
    bbox: Tuple[float, float, float, float]      # 边界框 (x0, y0, x1, y1)
    page_num: int                               # 页面编号
    block_num: int                              # 块编号
    font_info: Dict[str, Any]                   # 字体信息
    line_info: List[Dict]                       # 行信息
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.text.strip():
            raise ValueError("文本内容不能为空")
        if len(self.bbox) != 4:
            raise ValueError("边界框必须包含4个坐标值")
```

### TranslationResult

```python
@dataclass
class TranslationResult:
    """翻译结果数据结构"""
    original_text: str          # 原文
    translated_text: str        # 译文
    chunk_index: int           # 块索引
    processing_time: float     # 处理时间
    error_message: Optional[str] = None  # 错误信息
```

## PDF文本解析模块 (pdf_parser.py)

### PDFTextExtractor

```python
class PDFTextExtractor:
    """PDF文本提取器"""
    
    def __init__(self, pdf_path: str, **kwargs):
        """
        初始化PDF文本提取器
        
        Args:
            pdf_path (str): PDF文件路径
            **kwargs: 额外配置参数
                - extract_images (bool): 是否提取图片信息，默认False
                - preserve_layout (bool): 是否保持布局信息，默认True
                - text_flags (int): 文本提取标志，默认TEXT_PRESERVE_WHITESPACE
        
        Raises:
            FileNotFoundError: PDF文件不存在
            PermissionError: 文件权限不足
            ValueError: 文件格式错误
        """
        
    def extract_text_blocks(self) -> List[TextBlock]:
        """
        提取所有文本块
        
        Returns:
            List[TextBlock]: 文本块列表
            
        Raises:
            PDFProcessingError: PDF处理错误
            MemoryError: 内存不足
            
        Example:
            >>> extractor = PDFTextExtractor("paper.pdf")
            >>> blocks = extractor.extract_text_blocks()
            >>> print(f"提取了 {len(blocks)} 个文本块")
        """
        
    def get_reading_order(self) -> List[TextBlock]:
        """
        获取按阅读顺序排列的文本块
        
        Returns:
            List[TextBlock]: 按阅读顺序排列的文本块
            
        Example:
            >>> blocks = extractor.get_reading_order()
            >>> for block in blocks:
            >>>     print(f"页面{block.page_num}: {block.text[:50]}...")
        """
        
    def get_page_info(self, page_num: int) -> Dict[str, Any]:
        """
        获取指定页面信息
        
        Args:
            page_num (int): 页面编号(从0开始)
            
        Returns:
            Dict[str, Any]: 页面信息
                - width: 页面宽度
                - height: 页面高度
                - rotation: 旋转角度
                - blocks_count: 文本块数量
                
        Example:
            >>> info = extractor.get_page_info(0)
            >>> print(f"页面大小: {info['width']}x{info['height']}")
        """
        
    def extract_fonts(self) -> Dict[str, Dict]:
        """
        提取文档中使用的字体信息
        
        Returns:
            Dict[str, Dict]: 字体信息字典
                key: 字体名称
                value: 字体详细信息
        """
        
    def close(self):
        """关闭PDF文档，释放资源"""
```

### 异常类

```python
class PDFProcessingError(Exception):
    """PDF处理异常"""
    pass

class UnsupportedPDFFormat(PDFProcessingError):
    """不支持的PDF格式"""
    pass
```

## 文本分块模块 (text_chunker.py)

### TextChunker

```python
class TextChunker:
    """文本分块处理器"""
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 100):
        """
        初始化文本分块器
        
        Args:
            chunk_size (int): 每个块的最大字符数
            overlap_size (int): 块之间的重叠字符数
        """
        
    def create_chunks(self, text_blocks: List[TextBlock]) -> List[str]:
        """
        创建文本块
        
        Args:
            text_blocks (List[TextBlock]): 输入文本块列表
            
        Returns:
            List[str]: 分块后的文本字符串列表
            
        Example:
            >>> chunker = TextChunker(chunk_size=800)
            >>> chunks = chunker.create_chunks(text_blocks)
            >>> print(f"创建了 {len(chunks)} 个文本块")
        """
        
    def merge_blocks_to_string(self, blocks: List[TextBlock]) -> str:
        """
        将文本块合并为字符串
        
        Args:
            blocks (List[TextBlock]): 文本块列表
            
        Returns:
            str: 合并后的字符串
        """
        
    def get_chunk_statistics(self) -> Dict[str, Any]:
        """
        获取分块统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
                - total_chunks: 总块数
                - avg_chunk_size: 平均块大小
                - min_chunk_size: 最小块大小
                - max_chunk_size: 最大块大小
        """
```

## 文本清洗模块 (text_cleaner.py)

### TextCleaner

```python
class TextCleaner:
    """文本清洗处理器"""
    
    def __init__(self, openai_client, model: str = "gpt-4"):
        """
        初始化文本清洗器
        
        Args:
            openai_client: OpenAI客户端实例
            model (str): 使用的模型名称
        """
        
    def clean_text_chunk(self, text_chunk: str) -> str:
        """
        清洗单个文本块
        
        Args:
            text_chunk (str): 输入文本块
            
        Returns:
            str: 清洗后的文本
            
        Raises:
            APIError: API调用错误
            ValidationError: 文本验证错误
            
        Example:
            >>> cleaner = TextCleaner(openai_client)
            >>> cleaned = cleaner.clean_text_chunk(raw_text)
            >>> print(f"清洗前: {len(raw_text)} 字符")
            >>> print(f"清洗后: {len(cleaned)} 字符")
        """
        
    def clean_text_chunks(self, text_chunks: List[str]) -> List[str]:
        """
        批量清洗文本块
        
        Args:
            text_chunks (List[str]): 输入文本块列表
            
        Returns:
            List[str]: 清洗后的文本块列表
            
        Example:
            >>> cleaner = TextCleaner(openai_client)
            >>> cleaned_chunks = cleaner.clean_text_chunks(raw_chunks)
            >>> print(f"批量清洗了 {len(cleaned_chunks)} 个文本块")
        """
    
    def process_cleaned_output(self, cleaned_text: str) -> str:
        """
        处理清洗后的输出，转换标记
        
        Args:
            cleaned_text (str): 清洗后的文本
            
        Returns:
            str: 处理后的文本
        """
    
    def process_title_tags(self, text: str) -> str:
        """
        处理标题标签，将<Title>标签转换为Markdown格式
        
        Args:
            text (str): 包含<Title></Title>标签的文本
            
        Returns:
            str: 转换后的文本，<Title>标题</Title> -> \n## 标题\n
            
        Example:
            >>> text = "Some text <Title>Introduction</Title> more text"
            >>> result = cleaner.process_title_tags(text)
            >>> print(result)  # "Some text \n## Introduction\n more text"
        """
        
    def process_end_tags(self, text: str) -> str:
        """
        处理分段标签，将<End>标签转换为换行符
        
        Args:
            text (str): 包含<End>标签的文本
            
        Returns:
            str: 转换后的文本，<End> -> \n
            
        Example:
            >>> text = "Paragraph one.<End>Paragraph two."
            >>> result = cleaner.process_end_tags(text)
            >>> print(result)  # "Paragraph one.\nParagraph two."
        """
```

## 文本排序模块 (text_sorter.py)

### TextSorter

```python
class TextSorter:
    """文本语义排序处理器"""
    
    def __init__(self, openai_client, model: str = "gpt-4"):
        """
        初始化文本排序器
        
        Args:
            openai_client: OpenAI客户端实例
            model (str): 使用的模型名称
        """
    
    def sort_text_semantically(self, text_chunk: str) -> str:
        """
        对文本进行语义排序
        
        Args:
            text_chunk (str): 输入文本块
            
        Returns:
            str: 排序后的文本
            
        Example:
            >>> sorter = TextSorter(openai_client)
            >>> sorted_text = sorter.sort_text_semantically(messy_text)
            >>> print("文本已重新排序以提高连贯性")
        """
    
    def sort_text_chunks(self, text_chunks: List[str]) -> List[str]:
        """
        批量对文本块进行语义排序
        
        Args:
            text_chunks (List[str]): 输入文本块列表
            
        Returns:
            List[str]: 排序后的文本块列表
            
        Example:
            >>> sorter = TextSorter(openai_client)
            >>> sorted_chunks = sorter.sort_text_chunks(messy_chunks)
            >>> print(f"批量排序了 {len(sorted_chunks)} 个文本块")
        """
```

## AI翻译模块 (translator.py)

### AITranslator

```python
class AITranslator:
    """AI翻译器"""
    
    def __init__(self, openai_client, model: str = "gpt-4", **kwargs):
        """
        初始化AI翻译器
        
        Args:
            openai_client: OpenAI客户端实例
            model (str): 使用的模型名称
            **kwargs: 额外配置
                - temperature (float): 生成温度，默认0.3
                - max_tokens (int): 最大令牌数，默认2000
                - timeout (int): 超时时间，默认60秒
        """
    
    def translate_text(self, english_text: str) -> str:
        """
        翻译单个文本
        
        Args:
            english_text (str): 英文原文
            
        Returns:
            str: 中文翻译
            
        Raises:
            TranslationError: 翻译失败
            APIError: API调用错误
            
        Example:
            >>> translator = AITranslator(openai_client)
            >>> chinese = translator.translate_text("Machine learning is...")
            >>> print(f"翻译结果: {chinese}")
        """
        
    def translate_chunks(self, text_chunks: List[str]) -> List[TranslationResult]:
        """
        批量翻译文本块
        
        Args:
            text_chunks (List[str]): 文本块列表
            
        Returns:
            List[TranslationResult]: 翻译结果列表
            
        Example:
            >>> results = translator.translate_chunks(chunks)
            >>> for result in results:
            >>>     if result.error_message:
            >>>         print(f"翻译失败: {result.error_message}")
            >>>     else:
            >>>         print(f"翻译成功: {result.translated_text[:50]}...")
        """
        
    def translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        """
        带重试机制的翻译
        
        Args:
            text (str): 待翻译文本
            max_retries (int): 最大重试次数
            
        Returns:
            str: 翻译结果
        """
        
    def get_translation_statistics(self) -> Dict[str, Any]:
        """
        获取翻译统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
                - total_translations: 总翻译数
                - success_rate: 成功率
                - avg_processing_time: 平均处理时间
                - api_calls_count: API调用次数
        """
```

### 异常类

```python
class TranslationError(Exception):
    """翻译异常"""
    pass

class APIRateLimitError(TranslationError):
    """API频率限制异常"""
    pass

class TranslationQualityError(TranslationError):
    """翻译质量异常"""
    pass
```

## Markdown生成模块 (markdown_generator.py)

### MarkdownGenerator

```python
class MarkdownGenerator:
    """Markdown文档生成器"""
    
    def __init__(self, **kwargs):
        """
        初始化Markdown生成器
        
        Args:
            **kwargs: 配置参数
                - title_prefix (str): 标题前缀，默认"# "
                - code_block_lang (str): 代码块语言，默认""
                - line_break (str): 换行符，默认"\n"
        """
        
    def process_titles(self, text: str) -> str:
        """
        处理标题标记
        
        Args:
            text (str): 包含标题标记的文本
            
        Returns:
            str: 转换后的Markdown文本
            
        Example:
            >>> generator = MarkdownGenerator()
            >>> md_text = generator.process_titles(text_with_titles)
            >>> print("标题已转换为Markdown格式")
        """
        
    def process_paragraphs(self, text: str) -> str:
        """
        处理段落标记
        
        Args:
            text (str): 包含段落标记的文本
            
        Returns:
            str: 格式化后的文本
        """
        
    def generate_markdown(self, translated_chunks: List[str]) -> str:
        """
        生成完整的Markdown文档
        
        Args:
            translated_chunks (List[str]): 翻译后的文本块列表
            
        Returns:
            str: 完整的Markdown文档
            
        Example:
            >>> markdown_doc = generator.generate_markdown(translated_chunks)
            >>> with open("output.md", "w", encoding="utf-8") as f:
            >>>     f.write(markdown_doc)
        """
        
    def add_metadata(self, content: str, metadata: Dict[str, str]) -> str:
        """
        添加文档元数据
        
        Args:
            content (str): 文档内容
            metadata (Dict[str, str]): 元数据信息
            
        Returns:
            str: 包含元数据的Markdown文档
        """
        
    def format_formulas(self, text: str) -> str:
        """
        格式化数学公式
        
        Args:
            text (str): 包含公式的文本
            
        Returns:
            str: 格式化后的文本
        """
        
    def create_table_of_contents(self, content: str) -> str:
        """
        创建目录
        
        Args:
            content (str): Markdown内容
            
        Returns:
            str: 目录字符串
        """
        
    def validate_markdown(self, content: str) -> Dict[str, Any]:
        """
        验证Markdown格式
        
        Args:
            content (str): Markdown内容
            
        Returns:
            Dict[str, Any]: 验证结果
                - is_valid: 是否有效
                - errors: 错误列表
                - warnings: 警告列表
        """
```

## 主控制器 (main.py)

### ThesisTranslator

```python
class ThesisTranslator:
    """论文翻译器主控制器"""
    
    def __init__(self, openai_api_key: str, **kwargs):
        """
        初始化论文翻译器
        
        Args:
            openai_api_key (str): OpenAI API密钥
            **kwargs: 配置参数
                - model (str): 使用的模型，默认"gpt-4"
                - chunk_size (int): 文本块大小，默认1000
                - max_retries (int): 最大重试次数，默认3
                - output_format (str): 输出格式，默认"markdown"
        """
        
    def translate_pdf(self, pdf_path: str, output_path: str) -> bool:
        """
        翻译PDF文件
        
        Args:
            pdf_path (str): 输入PDF文件路径
            output_path (str): 输出Markdown文件路径
            
        Returns:
            bool: 翻译是否成功
            
        Raises:
            FileNotFoundError: 输入文件不存在
            PermissionError: 文件权限不足
            TranslationError: 翻译过程中出错
            
        Example:
            >>> translator = ThesisTranslator(api_key="sk-...")
            >>> success = translator.translate_pdf("paper.pdf", "output.md")
            >>> if success:
            >>>     print("翻译完成！")
            >>> else:
            >>>     print("翻译失败，请检查日志")
        """
        
    def process_with_error_handling(self, pdf_path: str, output_path: str) -> Dict[str, Any]:
        """
        带错误处理的处理流程
        
        Args:
            pdf_path (str): 输入PDF路径
            output_path (str): 输出路径
            
        Returns:
            Dict[str, Any]: 处理结果
                - success: 是否成功
                - error_count: 错误数量
                - warning_count: 警告数量
                - processing_time: 处理时间
                - output_file: 输出文件路径
        """
        
    def get_progress(self) -> Dict[str, Any]:
        """
        获取处理进度
        
        Returns:
            Dict[str, Any]: 进度信息
                - current_stage: 当前阶段
                - progress_percentage: 进度百分比
                - estimated_time_remaining: 预计剩余时间
        """
        
    def set_configuration(self, config: Dict[str, Any]):
        """
        设置配置参数
        
        Args:
            config (Dict[str, Any]): 配置参数字典
        """
        
    def get_logs(self, level: str = "INFO") -> List[str]:
        """
        获取日志信息
        
        Args:
            level (str): 日志级别
            
        Returns:
            List[str]: 日志条目列表
        """
```

## 配置管理

### Settings类

```python
class Settings:
    """配置管理器"""
    
    # OpenAI配置
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TIMEOUT: int = 60
    
    # 文本处理配置
    CHUNK_SIZE: int = 1000
    OVERLAP_SIZE: int = 100
    MAX_RETRIES: int = 3
    
    # 输出配置
    OUTPUT_FORMAT: str = "markdown"
    INCLUDE_METADATA: bool = True
    INCLUDE_TOC: bool = True
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/translator.log"
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Settings':
        """从配置文件加载设置"""
        
    @classmethod
    def from_env(cls) -> 'Settings':
        """从环境变量加载设置"""
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        
    def validate(self) -> bool:
        """验证配置有效性"""
```

## 使用示例

### 基本使用

```python
from src.main import ThesisTranslator
from config.settings import Settings

# 方式1: 直接使用
translator = ThesisTranslator(openai_api_key="your-api-key")
success = translator.translate_pdf("input.pdf", "output.md")

# 方式2: 使用配置文件
settings = Settings.from_file("config.json")
translator = ThesisTranslator(
    openai_api_key=settings.OPENAI_API_KEY,
    model=settings.OPENAI_MODEL,
    chunk_size=settings.CHUNK_SIZE
)
result = translator.process_with_error_handling("input.pdf", "output.md")
print(f"处理结果: {result}")
```

### 高级使用

```python
# 自定义配置
config = {
    "model": "gpt-4",
    "chunk_size": 800,
    "temperature": 0.2,
    "include_toc": True,
    "output_format": "markdown"
}

translator = ThesisTranslator(openai_api_key="your-key")
translator.set_configuration(config)

# 监控进度
import time
translator.translate_pdf("large_paper.pdf", "output.md")
while True:
    progress = translator.get_progress()
    print(f"当前进度: {progress['progress_percentage']}%")
    if progress['progress_percentage'] >= 100:
        break
    time.sleep(10)
```

## 错误码参考

| 错误码 | 错误类型 | 描述 |
|--------|----------|------|
| 1001 | FileError | PDF文件不存在或无法读取 |
| 1002 | FormatError | PDF格式不支持 |
| 2001 | APIError | OpenAI API调用失败 |
| 2002 | RateLimitError | API调用频率超限 |
| 3001 | ProcessingError | 文本处理错误 |
| 3002 | ValidationError | 数据验证失败 |
| 4001 | OutputError | 输出文件写入失败 |
| 5001 | ConfigError | 配置参数错误 |

## 性能建议

1. **并发处理**: 对于大文件，考虑使用 `concurrent.futures` 进行并行翻译
2. **缓存机制**: 实现翻译结果缓存避免重复翻译
3. **批量API调用**: 合并小文本块减少API调用次数
4. **内存管理**: 使用生成器处理大文件避免内存溢出
5. **错误恢复**: 实现断点续传功能支持大文件处理

## 版本兼容性

- Python: 3.8+
- PyMuPDF: 1.23.0+
- OpenAI: 1.0.0+
- 其他依赖详见 `requirements.txt`