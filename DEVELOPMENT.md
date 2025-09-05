# Development Guide

## Setup Development Environment

### 1. Install the Package

Choose one of the following methods:

#### Using uv (recommended):
```bash
# Install with development dependencies
uv pip install -e '.[dev,test]'

# Or just install the base package
uv pip install -e .
```

#### Using pip:
```bash
# Install with development dependencies
pip install -e '.[dev,test]'

# Or just install the base package
pip install -e .
```

#### Using the installation script:
```bash
./install.sh
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_minio_client.py

# Run specific test class
pytest tests/test_minio_client.py::TestMinIOClientConfig

# Run with verbose output
pytest -v
```

### 3. Code Quality

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with mypy
mypy src/

# Lint with flake8
flake8 src/ tests/
```

### 4. Start MinIO Service

```bash
# Start MinIO using the script
./start_minio.sh

# Or run the service directly
thesis-translator-service
```

### 5. Run the Main Application

```bash
# Run the translator
thesis-translator --help

# Translate a PDF
thesis-translator --input document.pdf --output translated.md

# Download a paper from URL
thesis-translator --download-paper "https://arxiv.org/pdf/1234.5678.pdf"

# List files in MinIO
thesis-translator --list-files
```

## Project Structure

```
ThesisTranslator/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Main application entry point
│   ├── minio_client.py    # MinIO client implementation
│   ├── minio_service.py   # HTTP service for MinIO operations
│   ├── minio_file_interface.py  # Interface between MinIO and PDF processing
│   ├── paper_downloader.py       # Paper downloading functionality
│   ├── pdf_parser.py      # PDF text extraction
│   ├── text_cleaner.py    # Text cleaning
│   ├── text_chunker.py    # Text chunking
│   ├── text_sorter.py     # Text sorting
│   ├── translator.py      # AI translation
│   └── markdown_generator.py  # Markdown output generation
├── config/                # Configuration files
│   ├── __init__.py
│   ├── config_loader.py   # Configuration loading utility
│   ├── minio_config.yaml  # MinIO configuration
│   └── settings.py        # Application settings
├── tests/                 # Test files
│   ├── __init__.py
│   ├── test_minio_client.py
│   ├── test_minio_service.py
│   ├── test_minio_file_interface.py
│   ├── test_paper_downloader.py
│   ├── test_config_loader.py
│   └── ... (other test files)
├── docs/                  # Documentation
├── logs/                  # Log files
├── output/                # Output files
├── temp/                  # Temporary files
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
├── pyproject.toml        # Modern Python project configuration
├── start_minio.sh        # MinIO startup script
├── stop_minio.sh         # MinIO stop script
├── install.sh           # Installation script
└── .gitignore           # Git ignore rules
```

## Configuration

The application uses YAML configuration files with environment variable overrides:

### Configuration Files

1. **`config/minio_config.yaml`** - Main configuration file
2. **Environment variables** - Override configuration values

### Key Configuration Sections

```yaml
minio:
  endpoint: "localhost:9000"
  access_key: "minioadmin"
  secret_key: "minioadmin123"
  bucket_name: "papers"
  secure: false

openai:
  api_key: "your-openai-api-key"
  model: "gpt-4"
  base_url: "https://api.openai.com/v1"

service:
  host: "0.0.0.0"
  port: 5000
  debug: false
```

## Development Workflow

1. **Setup**: Run `./install.sh` to install the package
2. **Start MinIO**: Run `./start_minio.sh` to start the MinIO service
3. **Code**: Make changes to the source code
4. **Test**: Run `pytest` to ensure tests pass
5. **Lint**: Run code quality tools (black, isort, mypy)
6. **Commit**: Commit your changes

## Troubleshooting

### Import Errors

If you encounter import errors like `ModuleNotFoundError: No module named 'src'`:

1. Install the package in development mode: `pip install -e .`
2. Make sure you're in the project root directory
3. Check that all `__init__.py` files exist

### MinIO Connection Issues

1. Ensure MinIO is running: `./start_minio.sh`
2. Check MinIO status: `docker ps | grep thesis-translator-minio`
3. Verify configuration in `config/minio_config.yaml`
4. Check network connectivity to `localhost:9000`

### Configuration Loading Issues

1. Verify `config/minio_config.yaml` exists
2. Check YAML syntax
3. Ensure environment variables are set correctly
4. Run config loader tests: `pytest tests/test_config_loader.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Run code quality tools
7. Submit a pull request

## Environment Variables

Key environment variables that override configuration:

```bash
# MinIO Configuration
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin123"
export MINIO_BUCKET_NAME="papers"

# OpenAI Configuration
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4"

# Service Configuration
export MINIO_SERVICE_HOST="0.0.0.0"
export MINIO_SERVICE_PORT="5000"
export MINIO_SERVICE_DEBUG="false"
```