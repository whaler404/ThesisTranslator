#!/bin/bash

# ThesisTranslator Installation Script
# This script installs the ThesisTranslator package in development mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ThesisTranslator Installation Script ===${NC}"
echo

# Check if uv is available
if command -v uv &> /dev/null; then
    echo -e "${YELLOW}Using uv package manager...${NC}"
    INSTALL_CMD="uv pip install -e ."
    DEV_INSTALL_CMD="uv pip install -e '.[dev,test]'"
elif command -v pip &> /dev/null; then
    echo -e "${YELLOW}Using pip package manager...${NC}"
    INSTALL_CMD="pip install -e ."
    DEV_INSTALL_CMD="pip install -e '.[dev,test]'"
else
    echo -e "${RED}Error: Neither uv nor pip is available${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed${NC}"
    exit 1
fi

# Show Python version
PYTHON_VERSION=$(python --version)
echo -e "${BLUE}Python version: $PYTHON_VERSION${NC}"
echo

# Install base package
echo -e "${YELLOW}Installing ThesisTranslator package...${NC}"
$INSTALL_CMD
echo -e "${GREEN}✓ Base package installed${NC}"
echo

# Ask if user wants to install development dependencies
read -p "Do you want to install development dependencies? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    $DEV_INSTALL_CMD
    echo -e "${GREEN}✓ Development dependencies installed${NC}"
fi

echo
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo
echo -e "${BLUE}You can now use the following commands:${NC}"
echo "  - thesis-translator: Run the main translator"
echo "  - thesis-translator-service: Start the MinIO service"
echo
echo -e "${BLUE}To run tests:${NC}"
echo "  - pytest: Run all tests"
echo "  - pytest tests/test_minio_client.py: Run specific test"
echo
echo -e "${GREEN}Happy translating! 🎉${NC}"