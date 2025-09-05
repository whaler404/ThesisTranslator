# MinIO 设置和配置指南

## 环境要求

### 系统要求
- **操作系统**: Linux, macOS, Windows
- **Python**: 3.8+
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **存储**: 足够的磁盘空间用于存储论文文件

### 依赖要求
- MinIO 服务器 (版本 2023.3+)
- 网络连接 (用于下载论文和 API 调用)

## MinIO 服务器设置

### 方式一：使用 Docker (推荐)

```bash
# 1. 创建数据目录
mkdir -p ~/minio/data

# 2. 启动 MinIO 容器
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -v ~/minio/data:/data \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin123" \
  minio/minio server /data --console-address ":9001"
```

### 方式二：使用 Docker Compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin123
    volumes:
      - ./minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped

  thesis-translator:
    build: .
    container_name: thesis-translator
    depends_on:
      - minio
    environment:
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - MINIO_BUCKET_NAME=papers
      - MINIO_SECURE=false
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    restart: unless-stopped
```

启动服务：
```bash
docker-compose up -d
```

### 方式三：本地安装 MinIO

```bash
# 1. 下载 MinIO 二进制文件
wget https://dl.min.io/server/minio/release/linux-amd64/minio

# 2. 添加执行权限
chmod +x minio

# 3. 创建数据目录
mkdir -p ~/minio/data

# 4. 启动 MinIO
./minio server ~/minio/data --console-address ":9001"
```

## 环境变量配置

### 必需配置

创建 `.env` 文件：

```env
# MinIO 连接配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=papers
MINIO_SECURE=false

# MinIO 服务配置
MINIO_SERVICE_HOST=0.0.0.0
MINIO_SERVICE_PORT=5000
MINIO_SERVICE_DEBUG=false

# 下载配置
DOWNLOAD_TIMEOUT=30
DOWNLOAD_MAX_RETRIES=3

# OpenAI 配置 (保持原有配置)
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=
OPENAI_TIMEOUT=60
```

### 可选配置

```env
# 临时文件目录
TEMP_DIR=/tmp/thesis-translator

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/translator.log

# 下载器配置
DOWNLOAD_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
DOWNLOAD_BATCH_DELAY=1
DOWNLOAD_CHECK_ROBOTS=true

# 服务配置
MAX_UPLOAD_SIZE=104857600  # 100MB
CORS_ORIGINS=*
```

## 验证设置

### 1. 验证 MinIO 连接

```bash
# 安装 MinIO 客户端 (如果需要)
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
./mc alias set myminio http://localhost:9000 minioadmin minioadmin123

# 测试连接
./mc ls myminio

# 创建存储桶
./mc mb myminio/papers
```

### 2. 验证 ThesisTranslator 配置

```bash
# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export $(cat .env | xargs)

# 测试 MinIO 连接
python -c "
from src.minio_client import create_minio_client_from_env
client = create_minio_client_from_env()
files = client.list_files()
print(f'连接成功，存储桶中有 {len(files)} 个文件')
"

# 列出 MinIO 文件
python -m src.main --list-files
```

### 3. 验证 HTTP 服务

```bash
# 启动 HTTP 服务
python -m src.main --start-service &

# 测试健康检查
curl http://localhost:5000/api/health

# 测试文件列表
curl http://localhost:5000/api/files
```

## 存储桶设置

### 创建存储桶

```bash
# 使用 MinIO 客户端
./mc mb myminio/papers

# 使用 Python 脚本
python -c "
from src.minio_client import create_minio_client_from_env
client = create_minio_client_from_env()
# 存储桶会在初始化时自动创建
print('存储桶设置完成')
"
```

### 设置存储桶策略 (可选)

```bash
# 设置只读策略
./mc policy set download myminio/papers

# 设置读写策略
./mc policy set public myminio/papers
```

## 网络配置

### 防火墙设置

```bash
# Ubuntu/Debian
sudo ufw allow 9000/tcp  # MinIO API
sudo ufw allow 9001/tcp  # MinIO Console
sudo ufw allow 5000/tcp  # ThesisTranslator Service

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --permanent --add-port=9001/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### 反向代理配置 (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # MinIO Console
    location /minio-console/ {
        proxy_pass http://localhost:9001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ThesisTranslator API
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # MinIO API (直接访问)
    location /minio/ {
        proxy_pass http://localhost:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SSL/TLS 配置

### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 配置 Nginx 使用 SSL
sudo nano /etc/nginx/sites-available/your-domain.com
```

### MinIO SSL 配置

```bash
# 生成证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/minio.key \
  -out /etc/ssl/certs/minio.crt \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=your-domain.com"

# 启动 MinIO with SSL
./minio server \
  --certs-dir /etc/ssl/minio \
  ~/minio/data \
  --console-address ":9001"
```

## 性能优化

### MinIO 服务器优化

```bash
# 增加内存限制
export MINIO_MEMORY=4G

# 设置并发限制
export MINIO_MAX_CONNECTIONS=1000

# 启用压缩
export MINIO_COMPRESSION_ENABLE=on

# 启动优化后的 MinIO
./minio server ~/minio/data --console-address ":9001"
```

### ThesisTranslator 优化

```env
# 增加下载超时时间
DOWNLOAD_TIMEOUT=60

# 增加重试次数
DOWNLOAD_MAX_RETRIES=5

# 启用并发下载
DOWNLOAD_CONCURRENT=3

# 增加上传大小限制
MAX_UPLOAD_SIZE=524288000  # 500MB
```

## 监控和日志

### MinIO 监控

```bash
# 查看 MinIO 日志
docker logs minio

# 使用 MinIO Console
# 访问 http://localhost:9001
# 用户名: minioadmin
# 密码: minioadmin123
```

### ThesisTranslator 监控

```bash
# 查看应用日志
tail -f logs/translator.log

# 查看 HTTP 服务日志
curl http://localhost:5000/api/statistics
```

## 故障排除

### 常见问题

#### 1. 连接 MinIO 失败

```bash
# 检查 MinIO 服务状态
docker ps | grep minio

# 检查网络连接
telnet localhost 9000

# 检查环境变量
echo $MINIO_ENDPOINT
echo $MINIO_ACCESS_KEY
```

#### 2. 下载失败

```bash
# 检查网络连接
curl -I https://arxiv.org

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 检查磁盘空间
df -h
```

#### 3. 权限问题

```bash
# 检查目录权限
ls -la ~/minio/data

# 设置正确权限
chmod 755 ~/minio/data
chown -R $USER:$USER ~/minio/data
```

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 启用服务调试模式
export MINIO_SERVICE_DEBUG=true

# 启动调试服务
python -m src.main --start-service --verbose
```

## 备份和恢复

### 备份策略

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/minio_$DATE"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份 MinIO 数据
./mc cp --recursive myminio/papers $BACKUP_DIR/

# 备份配置文件
cp .env $BACKUP_DIR/

echo "备份完成: $BACKUP_DIR"
EOF

chmod +x backup.sh
```

### 自动备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

这个配置指南涵盖了从基础设置到高级配置的各个方面，用户可以根据自己的需求选择合适的配置方式。