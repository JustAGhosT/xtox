# xtotext - AI-Ready Document Conversion System

A powerful web-based application that transforms any document into AI-friendly text formats, designed for seamless integration with Large Language Models and AI workflows, with document storage and management capabilities.

## Features

- **Universal Document Conversion**: Transform documents (PDF, DOCX, LaTeX, Markdown, etc.) into AI-optimized text formats
- **AI-Ready Output**: Structured text output specifically formatted for LLM consumption and analysis
- **Document Storage**: Securely store and manage documents in Azure Data Lake Storage Gen2
- **Permission-Based Access**: Fine-grained user permissions for document access and conversion
- **LaTeX to PDF Conversion**: Convert LaTeX documents to PDF format with error handling
- **Repository Integration**: Batch convert entire project documentation into single AI-friendly files
- **Smart Context Preservation**: Maintain document structure and relationships for better AI understanding
- **API-First Design**: RESTful API designed for AI tool integration and automation workflows

## Architecture

This project consists of:

1. **Backend**: Azure Functions for serverless document processing, storage, retrieval, and conversion
2. **Frontend**: React application with AI-focused conversion interfaces
3. **Storage**: Azure Data Lake Storage Gen2 for document and converted text storage
4. **Database**: MongoDB for metadata, conversion history, and AI context mapping
5. **AI Conversion Engine**: Specialized pipeline for creating LLM-optimized text outputs
6. **Repository Processor**: Batch conversion system for entire codebases and documentation sets

## Prerequisites

- Azure subscription
- Azure CLI or PowerShell Az module
- Node.js 14+
- MongoDB
- Python 3.9+ (for development)
- AI conversion dependencies (transformers, tiktoken, etc.)

## AI-Optimized Features

### Smart Text Structuring
- **Context Headers**: Automatic insertion of document context and metadata
- **Token Optimization**: Text chunking optimized for LLM token limits
- **Relationship Mapping**: Preserve cross-document references and dependencies
- **Semantic Sectioning**: Intelligent document section identification

### Repository-Wide Conversion
- **Project Packaging**: Convert entire documentation sets into single AI-consumable files
- **Dependency Mapping**: Track and include related documents automatically  
- **Code-Documentation Linking**: Connect code files with their documentation
- **Version Tracking**: Maintain conversion history for iterative AI workflows

## Supported Formats

### Input Formats
- PDF documents → AI-structured text
- Microsoft Word (DOCX) → Formatted AI input
- LaTeX files → Mathematical content preserved
- Markdown → Enhanced structure for AI
- HTML → Clean text with link preservation
- Code repositories → Documentation + code context
- Technical diagrams → OCR + description extraction

### Output Formats
- **PDF**: Generated from LaTeX and other document types
- **AI-Text**: Clean, structured text for general LLM use
- **DOCX**: Microsoft Word format
- **Markdown**: Structured MD files
- **Contextual Format**: Text with preserved document relationships
- **Token-Optimized**: Chunked output respecting model token limits
- **Semantic JSON**: Structured data format for specialized AI tools
- **Repository Summary**: Single-file representation of entire projects

## Deployment

### Quick Start with PowerShell

1. Clone the repository
2. Navigate to the deployment directory
3. Run the AI-optimized deployment script:

```powershell
./deploy.ps1 -resourceGroupName "myResourceGroup" -location "eastus" -storageAccountName "mystorageacct" -enableAIOptimization $true
```

### Environment Configuration

```bash
# Azure Configuration
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
AZURE_FUNCTION_APP_NAME=your_function_app_name

# MongoDB Configuration  
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/xtotext

# AI Optimization Settings
ENABLE_TOKEN_OPTIMIZATION=true
MAX_TOKENS_PER_CHUNK=4000
PRESERVE_CODE_CONTEXT=true
AI_MODEL_TARGET=gpt-4  # or claude-3, etc.

# Repository Processing
BATCH_SIZE=50
INCLUDE_HIDDEN_FILES=false
RESPECT_GITIGNORE=true
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

### LaTeX to PDF Conversion
```python
import requests

# Convert LaTeX file to PDF
with open('document.tex', 'rb') as f:
    response = requests.post(
        'https://yourfunctionapp.azurewebsites.net/api/convert',
        files={'file': f},
        params={'auto_fix': 'true'},
        headers={'Authorization': 'Bearer your_token'}
    )
    
    # Get conversion result with download link
    conversion_id = response.json()['id']
    pdf_url = f'https://yourfunctionapp.azurewebsites.net/api/download/{conversion_id}'
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

## Development

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

## Monitoring AI Performance
- **Token Usage Tracking**: Monitor token consumption per conversion
- **Model Performance**: Track conversion quality metrics
- **AI Workflow Analytics**: Measure integration success rates
- **Context Preservation**: Validate relationship maintenance
- **Azure Application Insights**: Monitor function performance and errors

## AI Use Cases
- **Documentation Analysis**: Convert technical documentation for AI-powered Q&A systems
- **Code Understanding**: Transform codebases into AI-readable formats for analysis
- **Research and Analysis**: Convert academic papers for AI-powered research assistance

## Contributing
1. Fork the repository
2. Create a feature branch focused on AI optimization
3. Add tests for AI-specific functionality
4. Ensure compatibility with major LLM providers
5. Submit a pull request

## License
MIT License - see LICENSE file for details

## Support
- AI Integration Guide: [docs.xtotext.com/ai-integration](https://docs.xtotext.com/ai-integration)
- LLM Compatibility: [docs.xtotext.com/llm-support](https://docs.xtotext.com/llm-support)
- Issues: [GitHub Issues](https://github.com/your-org/xtotext/issues)