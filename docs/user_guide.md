# 英文论文翻译器 - 用户指南

## 目录

1. [快速开始](#快速开始)
2. [安装指南](#安装指南)
3. [基本使用](#基本使用)
4. [高级功能](#高级功能)
5. [配置说明](#配置说明)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)

## 快速开始

### 一分钟体验

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/ThesisTranslator.git
cd ThesisTranslator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置API密钥
export OPENAI_API_KEY="your-openai-api-key"

# 4. 运行翻译
python -m src.main input.pdf output.md
```

## 安装指南

### 系统要求

- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python版本**: 3.8 或更高
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **存储**: 500MB 可用空间
- **网络**: 稳定的互联网连接 (用于API调用)

### 方式一：pip安装 (推荐)

```bash
# 创建虚拟环境
python -m venv thesis-translator
source thesis-translator/bin/activate  # Linux/macOS
# thesis-translator\Scripts\activate   # Windows

# 安装项目
pip install thesis-translator

# 或从源码安装
pip install git+https://github.com/your-repo/ThesisTranslator.git
```

### 方式二：从源码安装

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/ThesisTranslator.git
cd ThesisTranslator

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装项目
pip install -e .
```

### 方式三：使用uv (快速安装)

```bash
# 安装uv
pip install uv

# 使用uv安装依赖
uv pip install -r requirements.txt
```

### 验证安装

```bash
# 检查版本
python -c "from src.main import ThesisTranslator; print('安装成功！')"

# 运行测试
python -m pytest tests/ -v
```

## 基本使用

### 设置API密钥

#### 方式一：环境变量

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-api-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

#### 方式二：配置文件

创建 `config/settings.json`:

```json
{
    "openai_api_key": "sk-your-api-key-here",
    "openai_model": "gpt-4",
    "chunk_size": 1000,
    "max_retries": 3
}
```

#### 方式三：.env文件

创建 `.env` 文件:

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4
CHUNK_SIZE=1000
MAX_RETRIES=3
```

### 命令行使用

#### 基本命令

```bash
# 翻译单个文件
python -m src.main input.pdf output.md

# 指定模型
python -m src.main input.pdf output.md --model gpt-4

# 设置块大小
python -m src.main input.pdf output.md --chunk-size 800

# 启用详细输出
python -m src.main input.pdf output.md --verbose
```

#### 批量处理

```bash
# 翻译目录中的所有PDF
python -m src.main --batch input_dir/ output_dir/

# 使用通配符
python -m src.main --batch "papers/*.pdf" translated/
```

#### 高级选项

```bash
# 完整命令示例
python -m src.main input.pdf output.md \
    --model gpt-4 \
    --chunk-size 1000 \
    --max-retries 3 \
    --timeout 60 \
    --include-toc \
    --include-metadata \
    --log-level INFO \
    --config config/settings.json
```

### Python代码使用

#### 基本使用

```python
from src.main import ThesisTranslator

# 创建翻译器实例
translator = ThesisTranslator(openai_api_key="your-api-key")

# 翻译PDF文件
success = translator.translate_pdf("input.pdf", "output.md")

if success:
    print("翻译完成！")
else:
    print("翻译失败，请检查日志")
```

#### 带错误处理

```python
from src.main import ThesisTranslator
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

try:
    translator = ThesisTranslator(openai_api_key="your-api-key")
    result = translator.process_with_error_handling("input.pdf", "output.md")
    
    print(f"处理结果: {result}")
    print(f"成功: {result['success']}")
    print(f"错误数: {result['error_count']}")
    print(f"处理时间: {result['processing_time']:.2f}秒")
    
except Exception as e:
    print(f"发生错误: {e}")
```

#### 自定义配置

```python
from src.main import ThesisTranslator

# 自定义配置
config = {
    "model": "gpt-4",
    "chunk_size": 800,
    "max_retries": 5,
    "temperature": 0.2,
    "include_toc": True,
    "include_metadata": True
}

translator = ThesisTranslator(openai_api_key="your-key")
translator.set_configuration(config)

# 开始翻译
translator.translate_pdf("research_paper.pdf", "translated.md")
```

### 进度监控

```python
import time
from src.main import ThesisTranslator

translator = ThesisTranslator(openai_api_key="your-key")

# 异步开始翻译 (示例，实际需要实现异步版本)
# translator.translate_pdf_async("large_paper.pdf", "output.md")

# 监控进度
while True:
    progress = translator.get_progress()
    print(f"当前阶段: {progress['current_stage']}")
    print(f"进度: {progress['progress_percentage']:.1f}%")
    
    if progress['progress_percentage'] >= 100:
        print("翻译完成！")
        break
        
    time.sleep(10)  # 每10秒检查一次
```

## 高级功能

### 批量处理

```python
import os
from src.main import ThesisTranslator

def batch_translate(input_dir, output_dir):
    """批量翻译目录中的PDF文件"""
    translator = ThesisTranslator(openai_api_key="your-key")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历所有PDF文件
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace('.pdf', '.md'))
            
            print(f"正在翻译: {filename}")
            success = translator.translate_pdf(input_path, output_path)
            
            if success:
                print(f"✓ 完成: {filename}")
            else:
                print(f"✗ 失败: {filename}")

# 使用示例
batch_translate("papers/", "translated/")
```

### 自定义翻译提示词

```python
from src.translator import AITranslator

class CustomTranslator(AITranslator):
    def get_translation_prompt(self, text):
        """自定义翻译提示词"""
        return f"""
        你是一个专业的学术论文翻译专家，专门翻译{self.field}领域的论文。
        
        请将以下英文文本翻译成中文：
        1. 保持学术性和准确性
        2. 使用{self.field}领域的专业术语
        3. 保留LaTeX公式格式
        4. 保持段落结构
        
        英文原文：
        {text}
        
        中文翻译：
        """

# 使用自定义翻译器
custom_translator = CustomTranslator(
    openai_client=client,
    field="机器学习"  # 指定专业领域
)
```

不需要质量控制环节

### 缓存机制

```python
import hashlib
import pickle
from pathlib import Path

class CachedTranslator(ThesisTranslator):
    def __init__(self, *args, cache_dir="cache/", **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, text):
        """生成缓存键"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def translate_with_cache(self, text):
        """带缓存的翻译"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # 检查缓存
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # 翻译并缓存
        result = self.translator.translate_text(text)
        
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
            
        return result
```

## 配置说明

### 完整配置示例

```json
{
    "openai": {
        "api_key": "sk-your-api-key",
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout": 60
    },
    "processing": {
        "chunk_size": 1000,
        "overlap_size": 100,
        "max_retries": 3,
        "retry_delay": 1
    },
    "output": {
        "format": "markdown",
        "include_toc": true,
        "include_metadata": true,
        "title_prefix": "# ",
        "code_block_lang": ""
    },
    "logging": {
        "level": "INFO",
        "file": "logs/translator.log",
        "max_size": "10MB",
        "backup_count": 5
    },
    "pdf": {
        "extract_images": false,
        "preserve_layout": true,
        "text_flags": 3
    }
}
```

### 配置项说明

#### OpenAI配置
- `api_key`: OpenAI API密钥
- `model`: 使用的模型 (gpt-4, gpt-3.5-turbo)
- `temperature`: 生成温度 (0.0-1.0)
- `max_tokens`: 最大令牌数
- `timeout`: 请求超时时间(秒)

#### 处理配置
- `chunk_size`: 文本块大小(字符数)
- `overlap_size`: 块重叠大小
- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟(秒)

#### 输出配置
- `format`: 输出格式 (markdown, html)
- `include_toc`: 是否包含目录
- `include_metadata`: 是否包含元数据
- `title_prefix`: 标题前缀
- `code_block_lang`: 代码块语言

不需要输出图片

## 故障排除

### 常见错误及解决方案

#### 1. API密钥错误

**错误信息**:
```
AuthenticationError: Incorrect API key provided
```

**解决方案**:
- 检查API密钥是否正确
- 确认API密钥有效期
- 检查环境变量设置

```bash
# 验证API密钥
echo $OPENAI_API_KEY

# 重新设置
export OPENAI_API_KEY="sk-your-correct-key"
```

#### 2. PDF文件损坏

**错误信息**:
```
PDFProcessingError: Cannot open PDF file
```

**解决方案**:
- 检查PDF文件是否完整
- 尝试用其他PDF阅读器打开
- 使用PDF修复工具

```python
# 检查PDF文件
import fitz
try:
    doc = fitz.open("problem.pdf")
    print(f"PDF页数: {len(doc)}")
    doc.close()
except Exception as e:
    print(f"PDF错误: {e}")
```

#### 3. 内存不足

**错误信息**:
```
MemoryError: Unable to allocate memory
```

**解决方案**:
- 减小chunk_size参数
- 分批处理大文件
- 增加系统内存

```python
# 使用较小的块大小
translator = ThesisTranslator(
    openai_api_key="your-key",
    chunk_size=500  # 减小块大小
)
```

#### 4. 网络连接问题

**错误信息**:
```
ConnectionError: Failed to connect to OpenAI API
```

**解决方案**:
- 检查网络连接
- 配置代理设置
- 增加超时时间

```python
# 配置代理
import os
os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
os.environ['HTTPS_PROXY'] = 'https://proxy.company.com:8080'

# 增加超时时间
translator = ThesisTranslator(
    openai_api_key="your-key",
    timeout=120  # 2分钟超时
)
```

#### 5. API速率限制

**错误信息**:
```
RateLimitError: Rate limit exceeded
```

**解决方案**:
- 增加重试延迟
- 升级API套餐
- 实现指数退避

```python
# 配置重试策略
translator = ThesisTranslator(
    openai_api_key="your-key",
    max_retries=5,
    retry_delay=2  # 2秒延迟
)
```

### 调试技巧

#### 启用详细日志

```python
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 或者设置到文件
logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 保存中间结果

```python
# 保存每个阶段的结果
translator = ThesisTranslator(openai_api_key="your-key")

# 手动执行各个步骤
blocks = translator.pdf_extractor.extract_text_blocks()
with open('debug_blocks.json', 'w') as f:
    json.dump([block.__dict__ for block in blocks], f, indent=2)

chunks = translator.text_chunker.create_chunks(blocks)
with open('debug_chunks.txt', 'w') as f:
    for i, chunk in enumerate(chunks):
        f.write(f"=== Chunk {i} ===\n{chunk}\n\n")
```

#### 测试单个模块

```python
# 测试PDF解析
from src.pdf_parser import PDFTextExtractor

extractor = PDFTextExtractor("test.pdf")
blocks = extractor.extract_text_blocks()
print(f"提取了 {len(blocks)} 个文本块")

# 测试翻译
from src.translator import AITranslator

translator = AITranslator(openai_client)
result = translator.translate_text("This is a test.")
print(f"翻译结果: {result}")
```

## 最佳实践

### 1. 文件组织

```
project/
├── papers/           # 原始PDF文件
├── translated/       # 翻译结果
├── logs/            # 日志文件
├── cache/           # 缓存文件
└── config/          # 配置文件
```

### 2. 批量处理策略

```python
def smart_batch_process(input_dir, output_dir):
    """智能批量处理"""
    translator = ThesisTranslator(openai_api_key="your-key")
    
    # 按文件大小排序，先处理小文件
    pdf_files = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            path = os.path.join(input_dir, filename)
            size = os.path.getsize(path)
            pdf_files.append((size, filename, path))
    
    pdf_files.sort()  # 按大小排序
    
    for size, filename, input_path in pdf_files:
        output_path = os.path.join(output_dir, filename.replace('.pdf', '.md'))
        
        # 跳过已处理的文件
        if os.path.exists(output_path):
            print(f"跳过已存在文件: {filename}")
            continue
            
        print(f"处理文件: {filename} ({size/1024/1024:.1f}MB)")
        
        try:
            success = translator.translate_pdf(input_path, output_path)
            if success:
                print(f"✓ 完成: {filename}")
            else:
                print(f"✗ 失败: {filename}")
        except Exception as e:
            print(f"✗ 错误: {filename} - {e}")
            continue
```

### 3. 质量控制

```python
def validate_output(markdown_file):
    """验证输出质量"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查基本结构
    checks = {
        'has_content': len(content.strip()) > 100,
        'has_titles': '##' in content or '#' in content,
        'has_chinese': any('\u4e00' <= c <= '\u9fff' for c in content),
        'no_error_markers': '[ERROR]' not in content,
        'proper_formulas': content.count('$$') % 2 == 0
    }
    
    return all(checks.values()), checks
```

### 4. 错误恢复

```python
def robust_translate(pdf_path, output_path, max_attempts=3):
    """带错误恢复的翻译"""
    for attempt in range(max_attempts):
        try:
            translator = ThesisTranslator(openai_api_key="your-key")
            success = translator.translate_pdf(pdf_path, output_path)
            
            if success:
                # 验证输出质量
                is_valid, checks = validate_output(output_path)
                if is_valid:
                    return True
                else:
                    print(f"质量检查失败: {checks}")
                    
        except Exception as e:
            print(f"尝试 {attempt + 1} 失败: {e}")
            time.sleep(5)  # 等待5秒后重试
    
    return False
```

### 5. 性能优化

```python
# 1. 使用缓存避免重复翻译
# 2. 合理设置chunk_size
# 3. 并发处理独立的文本块
# 4. 使用更快的模型进行预处理

import concurrent.futures

def parallel_translate_chunks(chunks):
    """并行翻译文本块"""
    translator = AITranslator(openai_client)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(translator.translate_text, chunk) for chunk in chunks]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    return results
```

不需要没有意义的 QA

## 技术支持

### 获取帮助

- **文档**: [项目文档](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/ThesisTranslator/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-repo/ThesisTranslator/discussions)
- **邮箱**: support@example.com

### 贡献代码

欢迎贡献代码和改进建议：

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 发起 Pull Request

### 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。