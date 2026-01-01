# xtotext - AI-Ready Document Conversion System

A powerful document conversion system that transforms any document into AI-friendly text formats, designed for seamless integration with Large Language Models and AI workflows, with document storage and management capabilities.

## Features

- **Universal Document Conversion**: Transform documents (PDF, DOCX, LaTeX, Markdown, etc.) into AI-optimized text formats
- **AI-Ready Output**: Structured text output specifically formatted for LLM consumption and analysis
- **Document Storage**: Securely store and manage documents in Azure Data Lake Storage Gen2
- **Permission-Based Access**: Fine-grained user permissions for document access and conversion
- **LaTeX to PDF Conversion**: Convert LaTeX documents to PDF format with error handling
- **Repository Integration**: Batch convert entire project documentation into single AI-friendly files
- **Smart Context Preservation**: Maintain document structure and relationships for better AI understanding
- **API-First Design**: RESTful API designed for AI tool integration and automation workflows
- **Proper Package Structure**: Follows Python packaging best practices
- **Type Hints**: Full type annotation support
- **CLI Interface**: Easy-to-use command-line tool
- **Modular Design**: Separate core, utils, and workflow modules

## Project Structure

```
xtox/
├── xtox/                    # Main package
│   ├── __init__.py         # Package initialization
│   ├── core/               # Core conversion functionality
│   │   ├── __init__.py
│   │   ├── document_converter.py  # Main converter class
│   │   ├── markdown_to_latex.py   # Markdown to LaTeX conversion
│   │   └── latex_to_pdf.py        # LaTeX to PDF conversion
│   ├── utils/              # Utility functions
│   │   ├── __init__.py
│   │   └── image_handler.py
│   ├── workflows/          # High-level workflows
│   │   ├── __init__.py
│   │   └── md_to_pdf.py
│   ├── cli/                # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py
│   ├── api/                # API routes
│   ├── backend/            # Backend services
│   ├── azure-functions/    # Azure Functions
│   └── frontend/           # React frontend
├── tests/                  # Test files
├── infra/                  # Infrastructure code
├── setup.py               # Package setup
├── pyproject.toml         # Modern Python project config
├── requirements.txt       # Dependencies
├── Makefile              # Development tasks
└── README.md             # This file
```

## Architecture

This project consists of:

1. **Backend**: Azure Functions for serverless document processing, storage, retrieval, and conversion
2. **Frontend**: React application with AI-focused conversion interfaces
3. **Storage**: Azure Data Lake Storage Gen2 for document and converted text storage
4. **Database**: MongoDB for metadata, conversion history, and AI context mapping
5. **AI Conversion Engine**: Specialized pipeline for creating LLM-optimized text outputs
6. **Repository Processor**: Batch conversion system for entire codebases and documentation sets

## Prerequisites

- Azure subscription (for cloud deployment)
- Azure CLI or PowerShell Az module
- Node.js 14+
- MongoDB
- Python 3.9+
- AI conversion dependencies (transformers, tiktoken, etc.)

## Installation

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd xtox

# Install in development mode with all dependencies
make setup

# Or manually:
pip install -e ".[dev,azure,api]"
```

### Production Installation

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Convert Markdown to PDF
xtotext input.md -o output_dir -r 2

# Convert LaTeX to PDF
xtotext document.tex -o output_dir

# Show help
xtotext --help
```

### Python API

```python
from xtox.core import DocumentConverter

# Initialize converter
converter = DocumentConverter(output_dir="./output")

# Convert Markdown to PDF
result = converter.markdown_to_pdf(
    "document.md", 
    refinement_level=2
)

# Convert LaTeX to PDF
pdf_path = converter.latex_to_pdf("document.tex")
```

### Using Workflows

```python
from xtox.workflows import process_markdown_to_pdf

result = process_markdown_to_pdf(
    "document.md",
    output_dir="./output",
    refinement_level=1
)
```

## API Endpoints

### AI-Focused Conversion
- `POST /api/ai/convert` - Convert document for AI consumption
- `POST /api/ai/repository` - Process entire repository for AI
- `GET /api/ai/context/{id}` - Get document with full context
- `POST /api/ai/optimize` - Optimize existing text for specific AI models

### Document Management
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - List documents available to the user
- `GET /api/documents/{id}` - Get document metadata
- `GET /api/documents/{id}/download` - Download document
- `POST /api/documents/{id}/permissions` - Update document permissions
- `DELETE /api/documents/{id}` - Delete a document

### Document Conversion
- `POST /api/convert` - Convert LaTeX to PDF
- `GET /api/conversion/{id}` - Get conversion result
- `GET /api/download/{id}` - Download converted PDF
- `GET /api/documents/{id}/ai-text` - Get AI-optimized text output
- `POST /api/batch/repository` - Repository-wide batch conversion

## Usage Examples

### Single Document for AI
```python
import requests

# Convert document for AI consumption
with open('technical_doc.pdf', 'rb') as f:
    response = requests.post(
        'https://yourfunctionapp.azurewebsites.net/api/ai/convert',
        files={'file': f},
        json={
            'target_model': 'gpt-4',
            'preserve_structure': True,
            'include_metadata': True
        },
        headers={'Authorization': 'Bearer your_token'}
    )
    ai_ready_text = response.json()['ai_text']
```

### Repository-Wide AI Conversion
```python
# Convert entire project documentation for AI
response = requests.post(
    'https://yourfunctionapp.azurewebsites.net/api/ai/repository',
    json={
        'repository_path': '/path/to/project',
        'include_code': True,
        'include_docs': True,
        'target_model': 'claude-3',
        'output_format': 'contextual'
    },
    headers={'Authorization': 'Bearer your_token'}
)
# Get single AI-friendly file representing entire project
project_context = response.json()['consolidated_text']
```

## Development

### Setup Development Environment

```bash
make dev-install
```

### Run Tests

```bash
make test
make test-cov  # with coverage
```

### Code Quality

```bash
make lint      # Run linting
make format    # Format code
```

### Build Package

```bash
make build
```

### Local Setup with Azure Functions Core Tools
1. **Install Azure Functions Core Tools**:
   ```bash
   npm install -g azure-functions-core-tools@4
   ```

2. **Run Functions locally**:
   ```bash
   cd azure-functions
   func start
   ```

3. **AI Model Integration**:
   ```bash
   # Install AI optimization tools
   pip install tiktoken transformers sentence-transformers
   # Configure model-specific tokenizers
   python scripts/setup_ai_models.py
   ```

## AI Integration Features

### LLM Optimization
```yaml
# config/ai_optimization.yaml
ai_optimization:
  token_limits:
    gpt-4: 8192
    claude-3: 100000
    gpt-3.5: 4096
  formatting:
    preserve_code_blocks: true
    add_context_headers: true
    include_file_paths: true
    maintain_hierarchy: true
  chunking:
    strategy: "semantic"  # or "fixed", "adaptive"
    overlap_tokens: 200
    respect_boundaries: true
```

### Repository Processing
```yaml
# config/repository.yaml
repository_processing:
  include_patterns:
    - "*.md"
    - "*.rst" 
    - "*.txt"
    - "README*"
    - "docs/**"
  exclude_patterns:
    - "node_modules/**"
    - ".git/**"
    - "*.log"
    - "build/**"
  ai_enhancements:
    add_file_context: true
    preserve_directory_structure: true
    include_git_info: false
```

## Recent Improvements

### Security Enhancements
- ✅ JWT secret key management via environment variables and Azure Key Vault
- ✅ Removed mock authentication bypass
- ✅ CORS origin restrictions
- ✅ File path sanitization to prevent path traversal attacks
- ✅ Input validation for all endpoints

### Performance Optimizations
- ✅ Database connection pooling
- ✅ Rate limiting middleware
- ✅ Database indexes for faster queries
- ✅ Centralized file validation

### UI/UX Improvements
- ✅ Accessibility components (ARIA labels, keyboard navigation)
- ✅ Design token integration
- ✅ Responsive design support
- ✅ Error handling improvements

## Contributing

1. Fork the repository
2. Create a feature branch focused on AI optimization
3. Add tests for AI-specific functionality
4. Ensure compatibility with major LLM providers
5. Submit a pull request

## Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Deployment Guide](docs/DEPLOYMENT.md) - Deployment instructions
- [Contributing](docs/CONTRIBUTING.md) - Contribution guidelines
- [Testing Guide](docs/TESTING.md) - Testing documentation
- [Design System](docs/DESIGN_SYSTEM.md) - Design tokens and components

## Environment Variables

See [.env.example](.env.example) for all configuration options.

**Required for Production:**
- `JWT_SECRET_KEY` - Minimum 32 characters
- `MONGO_URL` - MongoDB connection string
- `ALLOWED_ORIGINS` - Comma-separated frontend URLs
- `ENVIRONMENT` - Set to `production`
- `ALLOW_MOCK_AUTH` - Set to `false`

## License

MIT License - see LICENSE file for details