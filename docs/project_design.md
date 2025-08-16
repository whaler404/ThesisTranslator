# 英文论文翻译器 - 项目设计文档

## 项目概述

本项目旨在实现一个从0到1的英文论文翻译器，能够从PDF文件中提取文本，保留排版结构，通过大模型翻译成中文，最终输出为Markdown格式。

## 技术栈

- **语言**: Python 3.8+
- **PDF解析**: PyMuPDF (fitz)
- **AI翻译**: OpenAI API
- **项目管理**: Git
- **依赖管理**: pip + requirements.txt + uv + venv

## 系统架构

```
输入PDF文件
    ↓
阶段1: PDF文本解析
    ↓
阶段2: 文本分块
    ↓
阶段3: 文本清洗与结构化
    ↓
阶段4: AI翻译与格式转换
    ↓
输出Markdown文件
```

## 核心功能模块

### 1. PDF文本解析模块 (`pdf_parser.py`)

**功能**: 使用PyMuPDF从PDF中解析出所有文本和位置信息

**主要类和方法**:
```python
class PDFTextExtractor:
    def __init__(self, pdf_path: str)
    def extract_text_blocks(self) -> List[TextBlock]
    def get_reading_order(self) -> List[TextBlock]
```

**核心数据结构**:
```python
@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int
    block_num: int
    font_info: Dict[str, Any]
    line_info: List[Dict]
```

**实现要点**:
- 使用 `page.get_text("dict")` 获取详细的文本结构信息
- 按照PyMuPDF的几何位置推理和排序获取阅读顺序
- 保存字体、位置、页面等完整信息

### 2. 文本分块模块 (`text_chunker.py`)

**功能**: 将提取的文本按照指定窗口大小进行分割

**主要类和方法**:
```python
class TextChunker:
    def __init__(self, chunk_size: int = 1000)
    def create_chunks(self, text_blocks: List[TextBlock]) -> List[str]
    def merge_blocks_to_string(self, blocks: List[TextBlock]) -> str
```

**实现要点**:
- 按序拼接文本块，使用空格分隔
- 控制每个chunk不超过1000字符
- 保持文本的连续性和完整性

### 3. 文本清洗模块 (`text_cleaner.py`)

**功能**: 使用大模型识别和清洗文本内容

**主要类和方法**:
```python
class TextCleaner:
    def __init__(self, openai_client)
    def clean_text_chunk(self, text_chunk: str) -> str
    def process_cleaned_output(self, cleaned_text: str) -> str
```

**清洗规则**:
- **公式识别**: 转换为LaTeX格式，用 `$$` 包裹
- **标题识别**: 用 `<Title></Title>` 包裹
- **段落分割**: 用 `<End>` 标记
- **内容过滤**: 移除作者信息、邮箱、参考文献、页码、注脚等

**LLM提示词模板**:
```
你是一个专业的学术论文文本清洗助手。请对以下英文论文文本进行清洗和结构化：

1. 识别数学公式，转换为LaTeX格式并用$$包裹
2. 识别标题，用<Title></Title>包裹
3. 识别段落结束，用<End>标记
4. 移除无关内容：作者姓名、邮箱、参考文献、页码、注脚等

输入文本：{text_chunk}

请输出清洗后的文本：
```

### 4. 文本排序模块 (`text_sorter.py`)

**功能**: 使用LLM对清洗后的文本进行语义排序

**主要类和方法**:
```python
class TextSorter:
    def __init__(self, openai_client)
    def sort_text_semantically(self, text_chunk: str) -> str
    def check_sentence_order(self, text: str) -> bool
```

**排序策略**:
- 分析句子之间的逻辑关系
- 识别段落内部的语义连贯性
- 重新排列不合理的句子顺序
- 保持学术论文的逻辑结构

**LLM提示词模板**:
```
你是一个专业的学术文本排序专家。请分析以下文本的句子顺序，如果存在语义不连贯的问题，请重新排列句子顺序：

要求：
1. 保持学术论文的逻辑结构
2. 确保句子之间的语义连贯
3. 保留所有原始内容，只调整顺序
4. 如果顺序正确，直接输出原文

输入文本：{text_chunk}

请输出排序后的文本：
```

### 5. 翻译模块 (`translator.py`)

**功能**: 使用OpenAI API进行英中翻译

**主要类和方法**:
```python
class AITranslator:
    def __init__(self, openai_client, model: str = "gpt-4")
    def translate_text(self, english_text: str) -> str
    def translate_chunks(self, text_chunks: List[str]) -> List[str]
```

**翻译提示词模板**:
```
你是一个专业的学术论文翻译专家。请将以下英文学术论文文本翻译成中文：

要求：
1. 保持学术性和准确性
2. 保留LaTeX公式格式
3. 保持标题和段落结构
4. 使用准确的学术术语

英文原文：{english_text}

请输出中文翻译：
```

### 6. Markdown输出模块 (`markdown_generator.py`)

**功能**: 将翻译后的文本转换为Markdown格式

**主要类和方法**:
```python
class MarkdownGenerator:
    def __init__(self)
    def process_titles(self, text: str) -> str
    def process_paragraphs(self, text: str) -> str
    def generate_markdown(self, translated_chunks: List[str]) -> str
```

**格式转换规则**:
- `<Title></Title>` → `# 标题` (根据层级调整井号数量)
- `<End>` → 换行符
- 合并所有翻译块
- 生成完整的Markdown文档

### 7. 主控制器 (`main.py`)

**功能**: 协调各个模块完成完整的翻译流程

**主要类和方法**:
```python
class ThesisTranslator:
    def __init__(self, openai_api_key: str)
    def translate_pdf(self, pdf_path: str, output_path: str) -> bool
    def process_with_error_handling(self) -> bool
```

**完整处理流程**:
1. PDF文本解析 → 2. 文本分块 → 3. 文本清洗 → 4. 文本排序 → 5. AI翻译 → 6. Markdown生成

## 配置管理

### 配置文件 (`config/settings.py`)
```python
# OpenAI配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-4'

# 文本处理配置
CHUNK_SIZE = 1000
MAX_RETRIES = 3
TIMEOUT = 60

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/translator.log'
```

## 错误处理策略

1. **网络错误**: 重试机制，最多3次
2. **API限制**: 指数退避策略
3. **文件IO错误**: 记录日志，继续处理其他部分
4. **文本解析错误**: 跳过问题块，继续处理
5. **所有错误**: 使用try-catch包装，记录日志但不中断程序

## 项目结构

```
ThesisTranslator/
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── pdf_parser.py
│   ├── text_chunker.py
│   ├── text_cleaner.py
│   ├── text_sorter.py
│   ├── translator.py
│   ├── markdown_generator.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_pdf_parser.py
│   ├── test_text_chunker.py
│   ├── test_text_cleaner.py
│   ├── test_text_sorter.py
│   ├── test_translator.py
│   ├── test_markdown_generator.py
│   └── test_integration.py
├── docs/
│   ├── project_design.md
│   ├── api_reference.md
│   └── user_guide.md
├── examples/
│   ├── sample_input.pdf
│   └── sample_output.md
├── logs/
└── output/
```

## 性能优化

1. **批量处理**: 合并小的文本块减少API调用
2. **缓存机制**: 缓存翻译结果避免重复调用
3. **并发处理**: 对独立的文本块进行并发翻译
4. **内存管理**: 流式处理大文件，避免内存溢出

## 质量保证

1. **单元测试**: 每个模块都有对应的测试用例
2. **集成测试**: 端到端的完整流程测试
3. **代码质量**: 使用pylint、black进行代码检查和格式化
4. **文档完整**: 完善的API文档和用户指南

## 部署和使用

### 安装依赖
```bash
pip install -r requirements.txt
```

### 环境配置
```bash
export OPENAI_API_KEY="your-api-key"
```

### 使用示例
```python
from src.main import ThesisTranslator

translator = ThesisTranslator(api_key="your-key")
success = translator.translate_pdf("input.pdf", "output.md")
```

## 扩展性考虑

1. **多语言支持**: 框架设计支持其他语言对的翻译
2. **多AI模型**: 支持切换不同的AI服务提供商
3. **自定义清洗规则**: 可配置的文本清洗规则
4. **输出格式**: 支持多种输出格式(HTML、Word等)