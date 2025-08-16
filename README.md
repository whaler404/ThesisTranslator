# ThesisTranslator - 英文论文翻译器

## 项目简介

ThesisTranslator 是一个从0到1实现的英文论文翻译器，能够从PDF文件中提取文本，保留排版结构，通过大模型翻译成中文，最终输出为Markdown格式。

## 核心功能

- **PDF文本提取**: 使用PyMuPDF从PDF中解析文本和位置信息
- **智能文本处理**: 逐段合并翻译，保持语义连贯性
- **公式识别**: 自动识别数学公式并转换为LaTeX格式
- **标题识别**: 识别不同级别的章节并转换为多级标题
- **AI翻译**: 使用OpenAI API进行高质量英中翻译
- **Markdown输出**: 生成格式规范的Markdown文档

## 技术栈

- **语言**: Python 3.8+
- **PDF解析**: PyMuPDF (fitz)
- **AI翻译**: OpenAI API
- **项目管理**: Git

## 安装指南

```bash
# 克隆项目
git clone https://github.com/your-repo/ThesisTranslator.git
cd ThesisTranslator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```bash
# 设置OpenAI API密钥
export OPENAI_API_KEY="your-openai-api-key"

# 翻译PDF文件
python -m src.main input.pdf output.md
```

### 高级选项

```bash
# 指定模型和块大小
python -m src.main input.pdf output.md --model gpt-4 --chunk-size 800
python -m src.main test.pdf output.md --model qwen-flash --chunk-size 800

# 使用自定义API端点（如Azure OpenAI）
python -m src.main input.pdf output.md --base-url https://your-custom-api-endpoint.com/v1

# 启用详细输出
python -m src.main input.pdf output.md --verbose
```

### 支持的API端点

- **OpenAI官方API**: 默认配置，无需设置base_url
- **Azure OpenAI**: 设置为Azure部署的端点URL
- **本地部署的模型**: 兼容OpenAI API格式的本地服务
- **其他兼容服务**: 任何实现OpenAI API格式的第三方服务

## 项目结构

```
ThesisTranslator/
├── README.md
├── requirements.txt
├── config/
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
│   └── test_integration.py
├── docs/
│   ├── project_design.md
│   ├── test_plan.md
│   ├── api_reference.md
│   ├── user_guide.md
│   └── workflow_diagram.md
├── logs/
└── output/
```

## 配置说明

### 环境变量配置

```bash
# 必需配置
export OPENAI_API_KEY="your-openai-api-key"

# 可选配置
export OPENAI_BASE_URL="https://your-custom-api-endpoint.com/v1"  # 自定义API端点
export OPENAI_MODEL="gpt-4"
export CHUNK_SIZE="1000"
export MAX_RETRIES="3"
export OPENAI_TIMEOUT="60"
export LOG_LEVEL="INFO"
```

### 配置文件示例

`config/settings.py`:

```python
import os
from typing import Optional

# OpenAI配置
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL: Optional[str] = os.getenv('OPENAI_BASE_URL', None)  # 自定义API端点
OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4')

# 文本处理配置
CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '1000'))
MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
OPENAI_TIMEOUT: int = int(os.getenv('OPENAI_TIMEOUT', '60'))

# 日志配置
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行集成测试
pytest tests/test_integration.py -v
```

### 代码质量

```bash
# 代码检查
pylint src/

# 格式化代码
black src/
```

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

本项目采用 MIT 许可证。