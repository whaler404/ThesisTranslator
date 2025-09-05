#!/bin/bash

# MinIO stop script for ThesisTranslator
# This script stops the MinIO container

set -e

# Configuration
MINIO_CONTAINER_NAME="thesis-translator-minio"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MinIO Stop Script for ThesisTranslator ===${NC}"
echo

# Check if container exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^$MINIO_CONTAINER_NAME$"; then
    echo -e "${YELLOW}Stopping MinIO container...${NC}"
    docker stop "$MINIO_CONTAINER_NAME" >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ Container stopped${NC}"
    
    # Ask if user wants to remove the container
    read -p "Do you want to remove the container permanently? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing container...${NC}"
        docker rm "$MINIO_CONTAINER_NAME" >/dev/null 2>&1 || true
        echo -e "${GREEN}✓ Container removed${NC}"
    fi
else
    echo -e "${YELLOW}Container '$MINIO_CONTAINER_NAME' not found.${NC}"
    echo "It may have been already stopped or removed."
fi

echo
echo -e "${GREEN}MinIO stopped successfully! 👋${NC}"