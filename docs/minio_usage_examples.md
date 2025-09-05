# MinIO 使用示例和教程

## 目录

1. [快速开始](#快速开始)
2. [命令行使用](#命令行使用)
3. [Python API 使用](#python-api-使用)
4. [HTTP API 使用](#http-api-使用)
5. [批量处理示例](#批量处理示例)
6. [集成到现有工作流](#集成到现有工作流)
7. [高级用法](#高级用法)
8. [故障排除](#故障排除)

## 快速开始

### 1. 环境准备

```bash
# 设置环境变量
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=minioadmin
export MINIO_SECRET_KEY=minioadmin123
export MINIO_BUCKET_NAME=papers
export OPENAI_API_KEY=your-openai-api-key

# 启动 MinIO 服务 (如果还没有运行)
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin123" \
  minio/minio server /data --console-address ":9001"
```

### 2. 下载第一篇论文

```bash
# 下载 arXiv 论文
python -m src.main --download-paper "https://arxiv.org/pdf/2101.00001"

# 查看下载的文件
python -m src.main --list-files
```

### 3. 翻译论文

```bash
# 从 MinIO 翻译论文
python -m src.main arxiv_2101.00001.pdf output.md --from-minio

# 或者启动 HTTP 服务
python -m src.main --start-service
```

## 命令行使用

### 基本操作

#### 1. 下载论文

```bash
# 下载单个论文
python -m src.main --download-paper "https://arxiv.org/pdf/2101.00001"

# 下载并指定对象名称
python -m src.main --download-paper "https://arxiv.org/pdf/2101.00001" --output "my_paper.pdf"

# 下载 Springer 论文
python -m src.main --download-paper "https://link.springer.com/content/pdf/10.1007/s11276-021-02781-7.pdf"
```

#### 2. 批量下载

创建 `urls.txt` 文件：
```
https://arxiv.org/pdf/2101.00001
https://arxiv.org/pdf/2101.00002
https://arxiv.org/pdf/2101.00003
```

批量下载：
```bash
python -m src.main --batch-download urls.txt
```

#### 3. 文件管理

```bash
# 列出所有文件
python -m src.main --list-files

# 列出特定前缀的文件
python -m src.main --list-files --prefix "arxiv"

# 从 MinIO 翻译论文
python -m src.main arxiv_2101.00001.pdf output.md --from-minio
```

#### 4. 启动服务

```bash
# 启动 HTTP 服务
python -m src.main --start-service

# 启动调试模式服务
python -m src.main --start-service --verbose
```

### 高级用法

#### 1. 使用专用下载源

```bash
# 直接下载 arXiv 论文 (通过论文 ID)
python -c "
from src.paper_downloader import create_paper_downloader_from_env
downloader = create_paper_downloader_from_env()
result = downloader.extract_papers_from_arxiv('2101.00001')
print(result)
"

# 下载 IEEE 论文
python -c "
from src.paper_downloader import create_paper_downloader_from_env
downloader = create_paper_downloader_from_env()
result = downloader.extract_papers_from_ieee('1234567')
print(result)
"
```

#### 2. 获取统计信息

```bash
# 获取下载统计
python -c "
from src.paper_downloader import create_paper_downloader_from_env
downloader = create_paper_downloader_from_env()
stats = downloader.get_download_statistics()
print(f'总文件数: {stats[\"total_files\"]}')
print(f'PDF文件数: {stats[\"pdf_files\"]}')
print(f'总大小: {stats[\"total_size\"]} bytes')
"
```

## Python API 使用

### 1. 基本操作

```python
import os
from src.main import ThesisTranslator
from src.minio_client import create_minio_client_from_env
from src.paper_downloader import create_paper_downloader_from_env

# 初始化
translator = ThesisTranslator(openai_api_key="your-api-key")
minio_client = create_minio_client_from_env()
downloader = create_paper_downloader_from_env()

# 下载论文
result = downloader.download_paper("https://arxiv.org/pdf/2101.00001")
if result:
    print(f"下载成功: {result['object_name']}")
    
    # 从 MinIO 翻译
    success = translator.translate_from_minio(result['object_name'], "output.md")
    print(f"翻译成功: {success}")
```

### 2. 批量处理

```python
def batch_download_and_translate(urls):
    """批量下载并翻译论文"""
    translator = ThesisTranslator(openai_api_key="your-api-key")
    downloader = create_paper_downloader_from_env()
    
    # 批量下载
    results = downloader.batch_download_papers(urls)
    
    # 翻译每个论文
    for result in results:
        if result:
            object_name = result['object_name']
            output_file = f"translated_{object_name}.md"
            
            print(f"翻译: {object_name}")
            success = translator.translate_from_minio(object_name, output_file)
            
            if success:
                print(f"✓ 完成: {output_file}")
            else:
                print(f"✗ 失败: {object_name}")

# 使用示例
urls = [
    "https://arxiv.org/pdf/2101.00001",
    "https://arxiv.org/pdf/2101.00002",
    "https://arxiv.org/pdf/2101.00003"
]

batch_download_and_translate(urls)
```

### 3. 自定义下载器

```python
from src.paper_downloader import PaperDownloader
from src.minio_client import create_minio_client_from_env

class CustomPaperDownloader(PaperDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_headers = {
            'User-Agent': 'My Custom Downloader/1.0'
        }
    
    def download_with_custom_settings(self, url, timeout=60):
        """使用自定义设置下载"""
        original_timeout = self.timeout
        self.timeout = timeout
        
        try:
            result = self.download_paper(url)
            return result
        finally:
            self.timeout = original_timeout

# 使用自定义下载器
minio_client = create_minio_client_from_env()
custom_downloader = CustomPaperDownloader(minio_client)

result = custom_downloader.download_with_custom_settings(
    "https://arxiv.org/pdf/2101.00001",
    timeout=120
)
```

### 4. 文件管理

```python
from src.minio_client import create_minio_client_from_env
from src.minio_file_interface import create_minio_file_interface_from_env

def manage_files():
    """文件管理示例"""
    client = create_minio_client_from_env()
    interface = create_minio_file_interface_from_env()
    
    # 上传本地文件
    client.upload_file("local_paper.pdf", "uploaded_paper.pdf")
    
    # 列出文件
    files = client.list_files()
    print(f"存储桶中有 {len(files)} 个文件")
    
    # 获取文件信息
    file_info = client.get_file_info("uploaded_paper.pdf")
    if file_info:
        print(f"文件大小: {file_info['size']} bytes")
    
    # 生成访问 URL
    url = client.get_file_url("uploaded_paper.pdf", expires=3600)
    print(f"访问 URL: {url}")
    
    # 删除文件
    client.delete_file("uploaded_paper.pdf")

manage_files()
```

## HTTP API 使用

### 1. 使用 requests 库

```python
import requests
import json

class MinIOAPIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def download_paper(self, url):
        """下载论文"""
        response = requests.post(
            f"{self.base_url}/api/download/paper",
            json={"url": url}
        )
        return response.json()
    
    def batch_download(self, urls):
        """批量下载"""
        response = requests.post(
            f"{self.base_url}/api/download/batch",
            json={"urls": urls}
        )
        return response.json()
    
    def list_files(self, prefix=""):
        """列出文件"""
        params = {"prefix": prefix} if prefix else {}
        response = requests.get(f"{self.base_url}/api/files", params=params)
        return response.json()
    
    def upload_file(self, file_path):
        """上传文件"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/api/upload", files=files)
        return response.json()
    
    def get_statistics(self):
        """获取统计信息"""
        response = requests.get(f"{self.base_url}/api/statistics")
        return response.json()

# 使用示例
client = MinIOAPIClient()

# 下载论文
result = client.download_paper("https://arxiv.org/pdf/2101.00001")
print(result)

# 批量下载
urls = ["https://arxiv.org/pdf/2101.00001", "https://arxiv.org/pdf/2101.00002"]
batch_result = client.batch_download(urls)
print(batch_result)

# 获取文件列表
files = client.list_files()
print(files)
```

### 2. 使用 JavaScript (Node.js)

```javascript
const axios = require('axios');

class MinIOAPIClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
    }

    async downloadPaper(url) {
        const response = await axios.post(`${this.baseUrl}/api/download/paper`, {
            url: url
        });
        return response.data;
    }

    async batchDownload(urls) {
        const response = await axios.post(`${this.baseUrl}/api/download/batch`, {
            urls: urls
        });
        return response.data;
    }

    async listFiles(prefix = '') {
        const params = prefix ? { prefix } : {};
        const response = await axios.get(`${this.baseUrl}/api/files`, { params });
        return response.data;
    }

    async getStatistics() {
        const response = await axios.get(`${this.baseUrl}/api/statistics`);
        return response.data;
    }
}

// 使用示例
async function main() {
    const client = new MinIOAPIClient();
    
    // 下载论文
    const result = await client.downloadPaper('https://arxiv.org/pdf/2101.00001');
    console.log(result);
    
    // 获取统计信息
    const stats = await client.getStatistics();
    console.log('统计信息:', stats);
}

main();
```

### 3. 使用 curl 脚本

```bash
#!/bin/bash

# MinIO API 操作脚本

BASE_URL="http://localhost:5000"

# 下载论文
download_paper() {
    local url=$1
    curl -X POST "$BASE_URL/api/download/paper" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$url\"}"
}

# 批量下载
batch_download() {
    local urls_file=$1
    curl -X POST "$BASE_URL/api/download/batch" \
        -H "Content-Type: application/json" \
        -d "{\"urls\": $(cat $urls_file | jq -R -s 'split("\n") | map(select(. != ""))')}"
}

# 列出文件
list_files() {
    curl "$BASE_URL/api/files"
}

# 获取统计信息
get_statistics() {
    curl "$BASE_URL/api/statistics"
}

# 使用示例
echo "下载论文..."
download_paper "https://arxiv.org/pdf/2101.00001"

echo -e "\n列出文件..."
list_files

echo -e "\n获取统计信息..."
get_statistics
```

## 批量处理示例

### 1. 研究论文批量处理

```python
import os
import time
from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

class ResearchPaperProcessor:
    def __init__(self, api_key):
        self.translator = ThesisTranslator(openai_api_key=api_key)
        self.downloader = create_paper_downloader_from_env()
    
    def process_research_topic(self, topic_urls, output_dir):
        """处理特定研究主题的论文"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 下载论文
        print(f"下载 {len(topic_urls)} 篇论文...")
        download_results = self.downloader.batch_download_papers(topic_urls)
        
        successful_downloads = [r for r in download_results if r]
        print(f"成功下载 {len(successful_downloads)} 篇论文")
        
        # 翻译论文
        translation_results = []
        for result in successful_downloads:
            object_name = result['object_name']
            output_file = os.path.join(output_dir, f"{object_name}.md")
            
            print(f"翻译: {object_name}")
            success = self.translator.translate_from_minio(object_name, output_file)
            
            translation_results.append({
                'object_name': object_name,
                'success': success,
                'output_file': output_file
            })
        
        # 生成报告
        self.generate_report(translation_results, output_dir)
        
        return translation_results
    
    def generate_report(self, results, output_dir):
        """生成处理报告"""
        report_file = os.path.join(output_dir, "processing_report.md")
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 论文处理报告\n\n")
            f.write(f"**处理时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**总计**: {len(results)} 篇论文\n")
            f.write(f"**成功**: {len(successful)} 篇\n")
            f.write(f"**失败**: {len(failed)} 篇\n\n")
            
            f.write("## 成功处理的论文\n\n")
            for result in successful:
                f.write(f"- {result['object_name']} → {result['output_file']}\n")
            
            if failed:
                f.write("\n## 处理失败的论文\n\n")
                for result in failed:
                    f.write(f"- {result['object_name']}\n")
        
        print(f"报告已生成: {report_file}")

# 使用示例
if __name__ == "__main__":
    processor = ResearchPaperProcessor("your-openai-api-key")
    
    # 机器学习论文 URLs
    ml_papers = [
        "https://arxiv.org/pdf/2101.00001",
        "https://arxiv.org/pdf/2101.00002",
        "https://arxiv.org/pdf/2101.00003"
    ]
    
    # 处理论文
    results = processor.process_research_topic(ml_papers, "output/ml_papers")
    
    print(f"处理完成: {len([r for r in results if r['success']])}/{len(results)} 成功")
```

### 2. 定时任务示例

```python
import schedule
import time
from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

class ScheduledPaperProcessor:
    def __init__(self, api_key):
        self.translator = ThesisTranslator(openai_api_key=api_key)
        self.downloader = create_paper_downloader_from_env()
    
    def check_new_papers(self, keywords):
        """检查新论文"""
        # 这里可以集成 arXiv API 或其他学术搜索引擎
        print(f"检查包含关键词的新论文: {keywords}")
        # 模拟找到新论文
        new_papers = [
            "https://arxiv.org/pdf/2101.00001",
            "https://arxiv.org/pdf/2101.00002"
        ]
        
        if new_papers:
            self.process_new_papers(new_papers)
    
    def process_new_papers(self, urls):
        """处理新论文"""
        print(f"处理 {len(urls)} 篇新论文")
        
        # 下载论文
        results = self.downloader.batch_download_papers(urls)
        
        # 翻译论文
        for result in results:
            if result:
                object_name = result['object_name']
                output_file = f"new_papers/{object_name}.md"
                
                success = self.translator.translate_from_minio(object_name, output_file)
                print(f"翻译 {object_name}: {'成功' if success else '失败'}")
    
    def cleanup_old_files(self, days=30):
        """清理旧文件"""
        print(f"清理 {days} 天前的文件")
        # 实现清理逻辑
        pass
    
    def start_scheduler(self):
        """启动定时任务"""
        # 每天检查新论文
        schedule.every().day.at("09:00").do(
            self.check_new_papers, 
            keywords=["machine learning", "deep learning"]
        )
        
        # 每周清理旧文件
        schedule.every().week.do(self.cleanup_old_files, days=30)
        
        print("定时任务已启动")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

# 使用示例
if __name__ == "__main__":
    processor = ScheduledPaperProcessor("your-openai-api-key")
    processor.start_scheduler()
```

## 集成到现有工作流

### 1. Jupyter Notebook 集成

```python
# 在 Jupyter Notebook 中使用
import sys
sys.path.append('/path/to/ThesisTranslator')

from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

# 初始化
translator = ThesisTranslator(openai_api_key="your-api-key")
downloader = create_paper_downloader_from_env()

# 下载论文
result = downloader.download_paper("https://arxiv.org/pdf/2101.00001")

# 翻译论文
if result:
    success = translator.translate_from_minio(result['object_name'], "output.md")
    
    # 显示翻译结果
    if success:
        with open("output.md", "r", encoding="utf-8") as f:
            content = f.read()
            from IPython.display import display, Markdown
            display(Markdown(content[:1000] + "..."))
```

### 2. Web 应用集成

```python
# Flask 应用示例
from flask import Flask, request, jsonify
from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

app = Flask(__name__)

# 初始化
translator = ThesisTranslator(openai_api_key="your-api-key")
downloader = create_paper_downloader_from_env()

@app.route('/api/translate', methods=['POST'])
def translate_paper():
    """翻译论文接口"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    
    # 下载论文
    result = downloader.download_paper(url)
    if not result:
        return jsonify({'error': 'Download failed'}), 500
    
    # 翻译论文
    output_file = f"temp/{result['object_name']}.md"
    success = translator.translate_from_minio(result['object_name'], output_file)
    
    if success:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'metadata': result
        })
    else:
        return jsonify({'error': 'Translation failed'}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### 3. CI/CD 集成

```yaml
# GitHub Actions 示例
name: Paper Processing Pipeline

on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一早上9点
  workflow_dispatch:

jobs:
  process-papers:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Download and process papers
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        MINIO_ENDPOINT: ${{ secrets.MINIO_ENDPOINT }}
        MINIO_ACCESS_KEY: ${{ secrets.MINIO_ACCESS_KEY }}
        MINIO_SECRET_KEY: ${{ secrets.MINIO_SECRET_KEY }}
      run: |
        python -c "
        from src.main import ThesisTranslator
        from src.paper_downloader import create_paper_downloader_from_env
        
        # 要处理的论文列表
        papers = [
            'https://arxiv.org/pdf/2101.00001',
            'https://arxiv.org/pdf/2101.00002'
        ]
        
        translator = ThesisTranslator()
        downloader = create_paper_downloader_from_env()
        
        # 批量下载和翻译
        results = downloader.batch_download_papers(papers)
        
        for result in results:
            if result:
                object_name = result['object_name']
                output_file = f'output/{object_name}.md'
                translator.translate_from_minio(object_name, output_file)
        "
    
    - name: Commit results
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add output/
        git commit -m "Add processed papers" || exit 0
        git push
```

## 高级用法

### 1. 自定义下载源

```python
from src.paper_downloader import PaperDownloader
from urllib.parse import urljoin

class CustomSourceDownloader(PaperDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_sources = {
            'nature': 'https://www.nature.com/articles/',
            'science': 'https://www.science.org/doi/'
        }
    
    def download_from_nature(self, article_id):
        """从 Nature 下载论文"""
        url = f"https://www.nature.com/articles/{article_id}.pdf"
        return self.download_paper(url)
    
    def download_from_science(self, doi):
        """从 Science 下载论文"""
        url = f"https://www.science.org/doi/pdf/{doi}"
        return self.download_paper(url)

# 使用示例
downloader = CustomSourceDownloader(minio_client)
result = downloader.download_from_nature("s41586-021-03619-y")
```

### 2. 并发处理

```python
import concurrent.futures
import threading
from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

class ConcurrentProcessor:
    def __init__(self, api_key, max_workers=3):
        self.translator = ThesisTranslator(openai_api_key=api_key)
        self.downloader = create_paper_downloader_from_env()
        self.max_workers = max_workers
        self.lock = threading.Lock()
    
    def process_single_paper(self, url):
        """处理单个论文"""
        try:
            # 下载论文
            result = self.downloader.download_paper(url)
            if not result:
                return {'url': url, 'success': False, 'error': 'Download failed'}
            
            # 翻译论文
            output_file = f"concurrent_output/{result['object_name']}.md"
            success = self.translator.translate_from_minio(
                result['object_name'], 
                output_file
            )
            
            return {
                'url': url,
                'success': success,
                'object_name': result['object_name'],
                'output_file': output_file
            }
            
        except Exception as e:
            return {'url': url, 'success': False, 'error': str(e)}
    
    def process_concurrent(self, urls):
        """并发处理多个论文"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_url = {
                executor.submit(self.process_single_paper, url): url 
                for url in urls
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.lock:
                        print(f"完成: {url} - {'成功' if result['success'] else '失败'}")
                        
                except Exception as e:
                    results.append({'url': url, 'success': False, 'error': str(e)})
        
        return results

# 使用示例
processor = ConcurrentProcessor("your-api-key", max_workers=5)

urls = [
    "https://arxiv.org/pdf/2101.00001",
    "https://arxiv.org/pdf/2101.00002",
    "https://arxiv.org/pdf/2101.00003",
    "https://arxiv.org/pdf/2101.00004",
    "https://arxiv.org/pdf/2101.00005"
]

results = processor.process_concurrent(urls)
successful = len([r for r in results if r['success']])
print(f"并发处理完成: {successful}/{len(urls)} 成功")
```

### 3. 错误恢复和重试

```python
import time
from src.main import ThesisTranslator
from src.paper_downloader import create_paper_downloader_from_env

class RobustProcessor:
    def __init__(self, api_key, max_retries=3, retry_delay=5):
        self.translator = ThesisTranslator(openai_api_key=api_key)
        self.downloader = create_paper_downloader_from_env()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def download_with_retry(self, url):
        """带重试的下载"""
        for attempt in range(self.max_retries):
            try:
                result = self.downloader.download_paper(url)
                if result:
                    return result
                print(f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {url}")
            except Exception as e:
                print(f"下载异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
        
        return None
    
    def translate_with_retry(self, object_name, output_file):
        """带重试的翻译"""
        for attempt in range(self.max_retries):
            try:
                success = self.translator.translate_from_minio(object_name, output_file)
                if success:
                    return True
                print(f"翻译失败 (尝试 {attempt + 1}/{self.max_retries}): {object_name}")
            except Exception as e:
                print(f"翻译异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    def process_robust(self, urls):
        """健壮的处理流程"""
        results = []
        
        for url in urls:
            print(f"处理: {url}")
            
            # 下载论文
            result = self.download_with_retry(url)
            if not result:
                results.append({'url': url, 'success': False, 'error': 'Download failed'})
                continue
            
            # 翻译论文
            output_file = f"robust_output/{result['object_name']}.md"
            success = self.translate_with_retry(result['object_name'], output_file)
            
            results.append({
                'url': url,
                'success': success,
                'object_name': result['object_name'],
                'output_file': output_file if success else None
            })
        
        return results

# 使用示例
processor = RobustProcessor("your-api-key", max_retries=3, retry_delay=5)

urls = [
    "https://arxiv.org/pdf/2101.00001",
    "https://arxiv.org/pdf/2101.00002"
]

results = processor.process_robust(urls)
print(f"健壮处理完成: {len([r for r in results if r['success']])}/{len(urls)} 成功")
```

## 故障排除

### 常见问题及解决方案

#### 1. 连接 MinIO 失败

```python
# 检查连接
from src.minio_client import create_minio_client_from_env

try:
    client = create_minio_client_from_env()
    files = client.list_files()
    print(f"连接成功，找到 {len(files)} 个文件")
except Exception as e:
    print(f"连接失败: {e}")
    print("请检查:")
    print("1. MinIO 服务是否运行")
    print("2. 环境变量是否正确设置")
    print("3. 网络连接是否正常")
```

#### 2. 下载失败

```python
# 调试下载
from src.paper_downloader import create_paper_downloader_from_env

downloader = create_paper_downloader_from_env()

# 检查 URL 有效性
def check_url(url):
    import requests
    try:
        response = requests.head(url, timeout=10)
        print(f"URL 状态: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        return response.status_code == 200
    except Exception as e:
        print(f"URL 检查失败: {e}")
        return False

# 测试下载
url = "https://arxiv.org/pdf/2101.00001"
if check_url(url):
    result = downloader.download_paper(url)
    print(f"下载结果: {result}")
else:
    print("URL 无效或无法访问")
```

#### 3. 翻译失败

```python
# 调试翻译
from src.main import ThesisTranslator

translator = ThesisTranslator(openai_api_key="your-api-key")

# 检查 OpenAI 连接
try:
    # 尝试简单的翻译测试
    test_result = translator.translator.translate_text("Hello, world!")
    print(f"翻译测试成功: {test_result}")
except Exception as e:
    print(f"翻译测试失败: {e}")
    print("请检查:")
    print("1. OpenAI API 密钥是否正确")
    print("2. 网络连接是否正常")
    print("3. API 配额是否充足")
```

#### 4. 内存不足

```python
# 处理大文件时的内存优化
from src.main import ThesisTranslator

def process_large_paper(object_name, output_file):
    """处理大文件的优化方法"""
    translator = ThesisTranslator(openai_api_key="your-api-key")
    
    # 使用较小的块大小
    translator.set_configuration({
        'chunk_size': 500,  # 减小块大小
        'max_retries': 5     # 增加重试次数
    })
    
    # 处理文件
    success = translator.translate_from_minio(object_name, output_file)
    
    if success:
        print("大文件处理完成")
    else:
        print("大文件处理失败")
    
    return success
```

### 日志分析

```python
import logging
from src.main import ThesisTranslator

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 运行处理
translator = ThesisTranslator(openai_api_key="your-api-key")
success = translator.translate_from_minio("paper.pdf", "output.md")

# 分析日志
def analyze_logs(log_file='debug.log'):
    """分析日志文件"""
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    errors = [line for line in lines if 'ERROR' in line]
    warnings = [line for line in lines if 'WARNING' in line]
    
    print(f"发现 {len(errors)} 个错误")
    print(f"发现 {len(warnings)} 个警告")
    
    if errors:
        print("\n错误信息:")
        for error in errors[-5:]:  # 显示最后5个错误
            print(error.strip())

analyze_logs()
```

这个使用示例和教程涵盖了从基础使用到高级应用的各种场景，可以帮助用户快速上手并充分利用 MinIO 集成功能。