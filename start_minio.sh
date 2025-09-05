#!/bin/bash

# MinIO startup script for ThesisTranslator
# This script starts MinIO as a standalone service with proper directory mapping

set -e

# Configuration
MINIO_CONTAINER_NAME="thesis-translator-minio"
MINIO_IMAGE="minio/minio:latest"
MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="minioadmin123"
MINIO_CONSOLE_PORT="9001"
MINIO_API_PORT="9000"

# User directory for MinIO data
MINIO_USER_DIR="$HOME/minio-thesis-translate"
MINIO_DATA_DIR="$MINIO_USER_DIR/data"
MINIO_CONFIG_DIR="$MINIO_USER_DIR/config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MinIO Startup Script for ThesisTranslator ===${NC}"
echo

# Create user directories if they don't exist
echo -e "${YELLOW}Creating MinIO directories...${NC}"
mkdir -p "$MINIO_DATA_DIR"
mkdir -p "$MINIO_CONFIG_DIR"
echo -e "${GREEN}✓ Created directories:${NC}"
echo "  Data: $MINIO_DATA_DIR"
echo "  Config: $MINIO_CONFIG_DIR"
echo

# Check if container already exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^$MINIO_CONTAINER_NAME$"; then
    echo -e "${YELLOW}Container '$MINIO_CONTAINER_NAME' already exists.${NC}"
    
    # Ask if user wants to remove existing container
    read -p "Do you want to remove the existing container? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing container...${NC}"
        docker stop "$MINIO_CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$MINIO_CONTAINER_NAME" >/dev/null 2>&1 || true
        echo -e "${GREEN}✓ Container removed${NC}"
    else
        echo -e "${YELLOW}Starting existing container...${NC}"
        docker start "$MINIO_CONTAINER_NAME"
        echo -e "${GREEN}✓ Container started${NC}"
        echo
        echo -e "${GREEN}=== MinIO Access Information ===${NC}"
        echo "API Endpoint: http://localhost:$MINIO_API_PORT"
        echo "Console URL: http://localhost:$MINIO_CONSOLE_PORT"
        echo "Username: $MINIO_ROOT_USER"
        echo "Password: $MINIO_ROOT_PASSWORD"
        echo
        exit 0
    fi
fi

# Pull MinIO image
echo -e "${YELLOW}Pulling MinIO image...${NC}"
docker pull "$MINIO_IMAGE"
echo -e "${GREEN}✓ Image pulled${NC}"
echo

# Start MinIO container
echo -e "${YELLOW}Starting MinIO container...${NC}"
docker run -d \
    --name "$MINIO_CONTAINER_NAME" \
    -p "$MINIO_API_PORT:9000" \
    -p "$MINIO_CONSOLE_PORT:9001" \
    -v "$MINIO_DATA_DIR:/data" \
    -v "$MINIO_CONFIG_DIR:/root/.minio" \
    -e "MINIO_ROOT_USER=$MINIO_ROOT_USER" \
    -e "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" \
    --restart unless-stopped \
    "$MINIO_IMAGE" server /data --console-address ":9001"

echo -e "${GREEN}✓ Container started${NC}"
echo

# Wait for container to be ready
echo -e "${YELLOW}Waiting for MinIO to be ready...${NC}"
for i in {1..30}; do
    if curl -s "http://localhost:$MINIO_API_PORT/minio/health/live" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ MinIO is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ MinIO failed to start within 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

echo
echo -e "${GREEN}=== MinIO Access Information ===${NC}"
echo "API Endpoint: http://localhost:$MINIO_API_PORT"
echo "Console URL: http://localhost:$MINIO_CONSOLE_PORT"
echo "Username: $MINIO_ROOT_USER"
echo "Password: $MINIO_ROOT_PASSWORD"
echo
echo -e "${GREEN}=== Directory Mapping ===${NC}"
echo "Data Directory: $MINIO_DATA_DIR"
echo "Config Directory: $MINIO_CONFIG_DIR"
echo
echo -e "${YELLOW}=== Useful Commands ===${NC}"
echo "View logs: docker logs -f $MINIO_CONTAINER_NAME"
echo "Stop container: docker stop $MINIO_CONTAINER_NAME"
echo "Start container: docker start $MINIO_CONTAINER_NAME"
echo "Remove container: docker rm -f $MINIO_CONTAINER_NAME"
echo
echo -e "${GREEN}MinIO setup complete! 🎉${NC}"