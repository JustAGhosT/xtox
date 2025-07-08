# xtotext Azure Functions

This folder contains the Azure Functions implementation of the xtotext AI-Ready Document Conversion System backend.

## Architectural Evaluation

We evaluated four potential architectural approaches for implementing the AI document processing system:

| Option | Description | Score |
|--------|-------------|-------|
| **1. Pure Python Azure Functions** | Keep current Python implementation with improved structure | **8.1/10** |
| **2. Full C# Conversion** | Convert entire codebase to C# | 7.35/10 |
| **3. C# with Python Interop** | C# Azure Functions calling Python for AI processing | 6.9/10 |
| **4. Azure ML Integration** | Python/C# Functions with AI models deployed to Azure ML | 7.9/10 |

### Evaluation Criteria (Scale 1-10)

| Measure | Weight | Option 1<br>Pure Python | Option 2<br>Full C# | Option 3<br>C# + Python | Option 4<br>Azure ML |
|---------|--------|------------------------|-------------------|------------------------|-------------------|
| Development Speed | 15% | 9 | 5 | 6 | 7 |
| AI Library Ecosystem | 20% | 10 | 5 | 9 | 9 |
| Performance | 15% | 7 | 9 | 7 | 8 |
| Maintainability | 15% | 7 | 8 | 5 | 6 |
| Azure Integration | 10% | 7 | 9 | 8 | 10 |
| Scalability | 15% | 8 | 9 | 7 | 10 |
| Cost Efficiency | 10% | 8 | 9 | 6 | 5 |
| **Weighted Total** | 100% | **8.1** | **7.35** | **6.9** | **7.9** |

### Decision: Pure Python Azure Functions

We've decided to proceed with **Option 1: Pure Python Azure Functions** because:

1. **Python has superior AI library support** - Essential for document processing and text optimization
2. **Fastest path to production** - Leverages existing code
3. **Simplest architecture** - Single language, simpler deployment
4. **Good performance for document workloads** - Python is sufficient for our needs
5. **Lower operational complexity** - Easier to maintain and extend

## Improved Python Structure

The current implementation works but can be improved with better organization, error handling, and modularity. Here's the planned new structure:

```
azure-functions/
├── host.json                # Azure Functions host configuration
├── local.settings.json      # Local development settings
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── shared_code/             # Shared code modules
│   ├── __init__.py
│   ├── database.py          # MongoDB connection and operations
│   ├── storage.py           # Azure Storage operations
│   ├── models.py            # Pydantic data models
│   ├── auth.py              # Authentication and authorization
│   └── ai/                  # AI processing modules
│       ├── __init__.py
│       ├── document_processor.py   # Extract text from documents
│       ├── text_optimizer.py       # Optimize text for AI
│       └── tokenization.py         # Token handling and chunking
├── ConvertToAIText/         # AI document conversion function
│   ├── __init__.py          # Main entry point (simplified)
│   ├── function.json        # Function definition
│   └── handler.py           # Request handling logic
├── UploadDocument/          # Document upload function
├── DownloadDocument/        # Document download function
├── ListDocuments/           # Document listing function
└── ConvertLatexToPdf/       # LaTeX to PDF conversion function
```

### Key Improvements

1. **Better Modularization**
   - Move AI functionality to dedicated modules
   - Separate request handling from business logic
   - Create reusable components

2. **Enhanced Error Handling**
   - More granular exception handling
   - Better logging for AI processing steps
   - Proper error responses with helpful messages

3. **Performance Optimization**
   - More efficient async/await patterns
   - Improved file handling with context managers
   - Optimized database queries

4. **Maintainability Improvements**
   - Clear separation of concerns
   - Better code documentation
   - Unit tests for core functionality

## Implementation Plan

### 1. Refactor Shared Code

Create specialized modules in the shared_code directory:

- `ai/document_processor.py` - Extract text from various document formats
- `ai/text_optimizer.py` - Optimize text for AI consumption
- `ai/tokenization.py` - Handle tokenization and chunking
- `auth.py` - Authentication and permission checking

### 2. Simplify Function Entry Points

The main function entry points will be simplified to:

```python
# ConvertToAIText/__init__.py
import logging
import azure.functions as func
from .handler import process_request

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('AI document conversion function triggered')
    return await process_request(req)
```

With the implementation details moved to handler.py:

```python
# ConvertToAIText/handler.py
async def process_request(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. Parse request
        file_data, filename, content_type, doc_id, options = await parse_request(req)
        
        # 2. Validate access if document ID provided
        if doc_id:
            file_data, filename, content_type = await get_document_with_permission_check(doc_id)
            
        # 3. Process document
        document_text = await extract_document_text(file_data, filename)
        ai_text, chunks = await optimize_text_for_ai(document_text, options)
        
        # 4. Store and return result
        result = await create_and_store_result(doc_id, filename, content_type, ai_text, chunks, options)
        return create_success_response(result)
        
    except DocumentNotFoundException:
        return create_error_response("Document not found", 404)
    except PermissionDeniedException:
        return create_error_response("Permission denied", 403)
    except Exception as e:
        logging.error(f"Error in AI conversion: {str(e)}")
        return create_error_response(f"Failed to convert document for AI: {str(e)}", 500)
```

### 3. Improve AI Processing Modules

Specialized AI processing modules with better error handling:

```python
# shared_code/ai/document_processor.py
async def extract_text_from_document(file_content, content_type, filename):
    """Extract text from various document formats with improved error handling"""
    extractor = get_document_extractor(filename)
    return await extractor.extract_text(file_content)

# shared_code/ai/text_optimizer.py
async def optimize_for_ai(text, options):
    """Optimize text for AI with better chunking strategies"""
    tokenizer = get_tokenizer_for_model(options.target_model)
    return await tokenizer.process_text(text, options)
```

## Migration Strategy

1. Create the new structure with empty files
2. Move shared code to appropriate modules
3. Refactor one function at a time, starting with ConvertToAIText
4. Add unit tests for each module
5. Validate the refactored functions against the original behavior

## Conclusion

The improved Python structure will maintain all the benefits of the AI-focused Python ecosystem while addressing the current limitations in code organization and maintainability. This approach will result in a more robust, maintainable, and performant system without requiring a complete rewrite or introducing unnecessary complexity.