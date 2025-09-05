# MinIO API 参考文档

## 概述

ThesisTranslator 提供了完整的 REST API 接口，用于管理 MinIO 中的文件和论文下载功能。所有 API 都返回 JSON 格式的响应。

## 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **字符编码**: `UTF-8`

## 响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "error_code": "ERROR_CODE"
}
```

## API 接口

### 1. 健康检查

检查服务状态和 MinIO 连接。

**端点**: `GET /api/health`

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "status": "healthy",
  "service": "MinIO File Service",
  "bucket": "papers"
}
```

### 2. 获取文件列表

获取存储桶中的文件列表。

**端点**: `GET /api/files`

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| prefix | string | 否 | 文件名前缀过滤 |

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "name": "arxiv_2101.00001.pdf",
      "size": 1234567,
      "last_modified": "2024-01-01T12:00:00Z",
      "etag": "abc123",
      "content_type": "application/pdf"
    }
  ],
  "count": 1
}
```

### 3. 获取文件信息

获取指定文件的详细信息。

**端点**: `GET /api/files/<filename>`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "name": "arxiv_2101.00001.pdf",
    "size": 1234567,
    "last_modified": "2024-01-01T12:00:00Z",
    "etag": "abc123",
    "content_type": "application/pdf"
  }
}
```

**错误响应** (404):
```json
{
  "success": false,
  "error": "文件不存在"
}
```

### 4. 删除文件

删除指定的文件。

**端点**: `DELETE /api/files/<filename>`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**响应示例**:
```json
{
  "success": true,
  "message": "文件 arxiv_2101.00001.pdf 删除成功"
}
```

### 5. 下载文件

下载指定的文件。

**端点**: `GET /api/files/<filename>/download`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**响应**: 文件二进制流

**错误响应**:
```json
{
  "success": false,
  "error": "文件下载失败"
}
```

### 6. 获取文件访问 URL

获取文件的临时访问 URL。

**端点**: `GET /api/files/<filename>/url`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**查询参数**:
| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| expires | int | 否 | 3600 | URL 过期时间（秒） |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "url": "http://localhost:9000/papers/arxiv_2101.00001.pdf?X-Amz-Algorithm=...",
    "expires_in": 3600
  }
}
```

### 7. 上传文件

上传文件到 MinIO。

**端点**: `POST /api/upload`

**请求格式**: `multipart/form-data`

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| file | file | 是 | 要上传的文件 |

**响应示例**:
```json
{
  "success": true,
  "message": "文件 example.pdf 上传成功",
  "data": {
    "filename": "example.pdf",
    "size": 1234567
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "没有找到文件"
}
```

### 8. 下载论文

从 URL 下载论文到 MinIO。

**端点**: `POST /api/download/paper`

**请求格式**: `application/json`

**请求体**:
```json
{
  "url": "https://arxiv.org/pdf/2101.00001",
  "object_name": "custom_name.pdf"
}
```

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| url | string | 是 | 论文 URL |
| object_name | string | 否 | 自定义对象名称 |

**响应示例**:
```json
{
  "success": true,
  "message": "论文下载成功",
  "data": {
    "url": "https://arxiv.org/pdf/2101.00001",
    "object_name": "arxiv_2101.00001.pdf",
    "size": 1234567,
    "content_type": "application/pdf",
    "original_filename": "2101.00001.pdf",
    "download_time": 1640995200.123
  }
}
```

### 9. 批量下载论文

批量下载多个论文到 MinIO。

**端点**: `POST /api/download/batch`

**请求格式**: `application/json`

**请求体**:
```json
{
  "urls": [
    "https://arxiv.org/pdf/2101.00001",
    "https://arxiv.org/pdf/2101.00002"
  ]
}
```

**请求参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| urls | array | 是 | 论文 URL 数组 |

**响应示例**:
```json
{
  "success": true,
  "message": "批量下载完成: 2/2 成功",
  "data": {
    "total": 2,
    "success": 2,
    "results": [
      {
        "url": "https://arxiv.org/pdf/2101.00001",
        "object_name": "arxiv_2101.00001.pdf",
        "size": 1234567
      },
      {
        "url": "https://arxiv.org/pdf/2101.00002",
        "object_name": "arxiv_2101.00002.pdf",
        "size": 2345678
      }
    ]
  }
}
```

### 10. 下载 arXiv 论文

从 arXiv 下载论文。

**端点**: `POST /api/download/arxiv/<arxiv_id>`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| arxiv_id | string | 是 | arXiv 论文 ID |

**响应示例**:
```json
{
  "success": true,
  "message": "arXiv 论文 2101.00001 下载成功",
  "data": {
    "url": "https://arxiv.org/pdf/2101.00001.pdf",
    "object_name": "arxiv_2101.00001.pdf",
    "size": 1234567,
    "content_type": "application/pdf",
    "original_filename": "2101.00001.pdf",
    "download_time": 1640995200.123
  }
}
```

### 11. 获取统计信息

获取下载和处理统计信息。

**端点**: `GET /api/statistics`

**请求参数**: 无

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_files": 25,
    "pdf_files": 20,
    "other_files": 5,
    "total_size": 45678901,
    "pdf_size": 44567890,
    "recent_files": [
      {
        "name": "arxiv_2101.00001.pdf",
        "size": 1234567,
        "last_modified": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

### 12. 检查文件存在性

检查文件是否存在。

**端点**: `GET /api/files/<filename>/exists`

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| filename | string | 是 | 文件名 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "filename": "arxiv_2101.00001.pdf",
    "exists": true
  }
}
```

## 错误码

| HTTP 状态码 | 错误码 | 描述 |
|-------------|--------|------|
| 200 | - | 成功 |
| 400 | INVALID_REQUEST | 请求参数无效 |
| 404 | FILE_NOT_FOUND | 文件不存在 |
| 404 | ENDPOINT_NOT_FOUND | 接口不存在 |
| 413 | FILE_TOO_LARGE | 文件大小超过限制 |
| 500 | MINIO_ERROR | MinIO 操作错误 |
| 500 | DOWNLOAD_ERROR | 下载失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

## 速率限制

- **API 调用**: 无限制
- **文件上传**: 最大 100MB
- **下载请求**: 每分钟最多 60 次
- **批量下载**: 每次最多 50 个 URL

## 认证和授权

当前版本不需要认证，但建议在生产环境中添加：

```bash
# API 密钥认证
export API_KEY=your-secret-key

# 请求头
Authorization: Bearer your-secret-key
```

## 使用示例

### cURL 示例

```bash
# 1. 下载论文
curl -X POST http://localhost:5000/api/download/paper \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/pdf/2101.00001"}'

# 2. 获取文件列表
curl http://localhost:5000/api/files

# 3. 上传文件
curl -X POST \
  -F "file=@/path/to/local.pdf" \
  http://localhost:5000/api/upload

# 4. 批量下载
curl -X POST http://localhost:5000/api/download/batch \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://arxiv.org/pdf/2101.00001", "https://arxiv.org/pdf/2101.00002"]}'

# 5. 获取统计信息
curl http://localhost:5000/api/statistics
```

### Python 示例

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:5000"

# 下载论文
def download_paper(url):
    response = requests.post(
        f"{BASE_URL}/api/download/paper",
        json={"url": url}
    )
    return response.json()

# 获取文件列表
def list_files():
    response = requests.get(f"{BASE_URL}/api/files")
    return response.json()

# 上传文件
def upload_file(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    return response.json()

# 使用示例
result = download_paper("https://arxiv.org/pdf/2101.00001")
print(result)

files = list_files()
print(files)
```

### JavaScript 示例

```javascript
// 配置
const BASE_URL = 'http://localhost:5000';

// 下载论文
async function downloadPaper(url) {
    const response = await fetch(`${BASE_URL}/api/download/paper`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
    });
    return await response.json();
}

// 获取文件列表
async function listFiles() {
    const response = await fetch(`${BASE_URL}/api/files`);
    return await response.json();
}

// 使用示例
downloadPaper('https://arxiv.org/pdf/2101.00001')
    .then(result => console.log(result));

listFiles()
    .then(files => console.log(files));
```

## WebSocket 支持

当前版本不支持 WebSocket，但可以通过轮询获取状态：

```javascript
// 轮询检查下载状态
function checkDownloadStatus(filename) {
    setInterval(async () => {
        const response = await fetch(`${BASE_URL}/api/files/${filename}/exists`);
        const result = await response.json();
        
        if (result.data.exists) {
            console.log('文件下载完成');
            clearInterval(interval);
        }
    }, 5000);
}
```

## 最佳实践

1. **错误处理**: 始终检查响应的 `success` 字段
2. **重试机制**: 对失败的请求实现指数退避重试
3. **批量操作**: 使用批量接口减少 API 调用次数
4. **文件大小**: 检查文件大小避免上传过大的文件
5. **超时设置**: 为网络请求设置合理的超时时间

## 版本兼容性

- **API 版本**: v1
- **向后兼容**: 是
- **弃用政策**: 提前 30 天通知重大变更