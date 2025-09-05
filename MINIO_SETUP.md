# MinIO Setup for ThesisTranslator

This directory contains scripts to set up MinIO as a standalone service for the ThesisTranslator project.

## Quick Start

### 1. Start MinIO Service
```bash
./start_minio.sh
```

This script will:
- Create necessary directories in `~/minio-thesis-translate/`
- Pull the MinIO Docker image
- Start MinIO with proper port and directory mappings
- Provide access information

### 2. Stop MinIO Service
```bash
./stop_minio.sh
```

This script will:
- Stop the MinIO container
- Optionally remove the container permanently

## Access Information

After starting MinIO, you can access it at:

- **API Endpoint**: `http://localhost:9000`
- **Console URL**: `http://localhost:9001`
- **Username**: `minioadmin`
- **Password**: `minioadmin123`

## Directory Structure

MinIO data will be stored in your user directory:
```
~/minio-thesis-translate/
├── data/          # MinIO data files
└── config/        # MinIO configuration files
```

## Configuration

The MinIO service is configured to work with the ThesisTranslator project using the following settings:

- **Bucket name**: `papers`
- **Access key**: `minioadmin`
- **Secret key**: `minioadmin123`
- **Endpoint**: `localhost:9000`

These settings are already configured in `config/minio_config.yaml`.

## Prerequisites

- Docker installed and running
- Docker daemon accessible to the current user

## Useful Commands

```bash
# View MinIO logs
docker logs -f thesis-translator-minio

# Check container status
docker ps | grep thesis-translator-minio

# Restart container
docker restart thesis-translator-minio

# Remove container completely
docker rm -f thesis-translator-minio
```

## Integration with ThesisTranslator

Once MinIO is running, the ThesisTranslator project will automatically use it for:
- Storing downloaded papers
- Managing file uploads and downloads
- Providing persistent storage for translated documents

The project configuration in `config/minio_config.yaml` is already set up to work with this MinIO setup.