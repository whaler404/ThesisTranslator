# ThesisTranslator - 英文论文翻译器

## 项目简介

ThesisTranslator 是一个从0到1实现的英文论文翻译器，能够从PDF文件中提取文本，保留排版结构，通过大模型翻译成中文，最终输出为Markdown格式。现已集成MinIO对象存储，支持论文自动下载、存储和管理。

## 核心功能

### 基础翻译功能
- **PDF文本提取**: 使用PyMuPDF从PDF中解析文本和位置信息
- **智能文本处理**: 逐段合并翻译，保持语义连贯性
- **公式识别**: 自动识别数学公式并转换为LaTeX格式
- **标题识别**: 识别不同级别的章节并转换为多级标题
- **AI翻译**: 使用OpenAI API进行高质量英中翻译
- **Markdown输出**: 生成格式规范的Markdown文档

### MinIO 集成功能
- **论文自动下载**: 从arXiv、Springer、IEEE等学术网站自动下载论文
- **对象存储管理**: 使用MinIO进行论文文件的存储和管理
- **HTTP API服务**: 提供完整的REST API接口进行文件操作
- **批量处理**: 支持批量下载和翻译多篇论文
- **多源支持**: 支持从多种学术资源网站下载论文

## 技术栈

### 核心技术
- **语言**: Python 3.8+
- **PDF解析**: PyMuPDF (fitz)
- **AI翻译**: OpenAI API
- **项目管理**: Git

### MinIO 集成
- **对象存储**: MinIO
- **HTTP服务**: Flask + Flask-CORS
- **文件下载**: requests + urllib
- **批量处理**: concurrent.futures

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

### 环境配置

```bash
# OpenAI 配置
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4"

# MinIO 配置 (可选)
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin123
export MINIO_BUCKET_NAME=papers
```

### 基础翻译功能

```bash
# 翻译本地PDF文件
python -m src.main input.pdf output.md

# 指定模型和块大小
python -m src.main input.pdf output.md --model gpt-4 --chunk-size 800

# 使用自定义API端点
python -m src.main input.pdf output.md --base-url https://your-custom-api-endpoint.com/v1
```

### MinIO 集成功能

#### 1. 论文下载

```bash
# 下载单篇论文
python -m src.main --download-paper "https://arxiv.org/pdf/2101.00001"

# 批量下载论文
echo "https://arxiv.org/pdf/2101.00001" > urls.txt
echo "https://arxiv.org/pdf/2101.00002" >> urls.txt
python -m src.main --batch-download urls.txt

# 列出MinIO中的文件
python -m src.main --list-files
```

#### 2. 从MinIO翻译

```bash
# 从MinIO翻译PDF
python -m src.main paper_object_name output.md --from-minio
```

#### 3. HTTP API服务

```bash
# 启动HTTP服务
python -m src.main --start-service

# 服务启动后，可以通过API访问：
# http://localhost:5000/api/health
# http://localhost:5000/api/files
# http://localhost:5000/api/download/paper
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
│   ├── minio_client.py          # MinIO客户端模块
│   ├── paper_downloader.py     # 论文下载模块
│   ├── minio_file_interface.py # MinIO文件接口
│   ├── minio_service.py        # HTTP API服务
│   └── main.py                 # 主程序（已增强）
├── tests/
│   ├── __init__.py
│   └── test_integration.py
├── docs/
│   ├── project_design.md
│   ├── test_plan.md
│   ├── api_reference.md
│   ├── user_guide.md
│   ├── workflow_diagram.md
│   ├── minio_overview.md        # MinIO功能概述
│   ├── minio_setup.md          # MinIO设置指南
│   ├── minio_api_reference.md  # MinIO API参考
│   └── minio_usage_examples.md # MinIO使用示例
├── logs/
└── output/
```

## 配置说明

### 环境变量配置

```bash
# OpenAI 配置 (必需)
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_MODEL="gpt-4"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# MinIO 配置 (可选，启用MinIO功能时必需)
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin123"
export MINIO_BUCKET_NAME="papers"
export MINIO_SECURE="false"

# HTTP 服务配置 (可选)
export MINIO_SERVICE_HOST="0.0.0.0"
export MINIO_SERVICE_PORT="5000"
export MINIO_SERVICE_DEBUG="false"

# 下载配置 (可选)
export DOWNLOAD_TIMEOUT="30"
export DOWNLOAD_MAX_RETRIES="3"

# 文本处理配置
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

## MinIO 快速开始

### 1. 启动 MinIO 服务

```bash
# 使用 Docker 启动 MinIO
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin123" \
  minio/minio server /data --console-address ":9001"
```

### 2. 配置环境变量

```bash
# 设置 MinIO 配置
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin123
export MINIO_BUCKET_NAME=papers

# 设置 OpenAI 配置
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. 下载和翻译论文

```bash
# 下载论文
python -m src.main --download-paper "https://arxiv.org/pdf/2101.00001"

# 从 MinIO 翻译
python -m src.main arxiv_2101.00001.pdf output.md --from-minio

# 启动 HTTP 服务
python -m src.main --start-service
```

## 文档

详细文档请查看 `docs/` 目录：

- **[MinIO 功能概述](docs/minio_overview.md)** - 了解 MinIO 集成的核心功能
- **[MinIO 设置指南](docs/minio_setup.md)** - 完整的安装和配置指南
- **[MinIO API 参考](docs/minio_api_reference.md)** - HTTP API 接口文档
- **[MinIO 使用示例](docs/minio_usage_examples.md)** - 详细的使用示例和教程

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