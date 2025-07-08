"""
Document processor module for extracting text from various document formats.
This module provides functionality to extract text content from different file types.
"""

import os
import logging
import tempfile
import re
from typing import Optional, Dict, Type, Any
from abc import ABC, abstractmethod


class DocumentExtractor(ABC):
    """Base abstract class for document extractors"""
    
    @abstractmethod
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from document bytes"""
        pass
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        """Check if this extractor supports the given filename"""
        pass


class PDFExtractor(DocumentExtractor):
    """PDF document extractor"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return filename.lower().endswith('.pdf')
    
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from PDF documents"""
        text = ""
        try:
            import pypdf
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Process PDF file
                pdf_reader = pypdf.PdfReader(temp_path)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except ImportError:
            text = "[Error: PDF processing library (pypdf) not available]"
            logging.warning("PDF extraction failed: pypdf library not available")
        except Exception as e:
            text = f"[Error extracting PDF text: {str(e)}]"
            logging.error(f"PDF extraction error: {str(e)}")
            
        return text


class DocxExtractor(DocumentExtractor):
    """DOCX document extractor"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return filename.lower().endswith('.docx')
    
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from DOCX documents"""
        text = ""
        try:
            import docx2txt
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Process DOCX file
                text = docx2txt.process(temp_path)
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except ImportError:
            text = "[Error: DOCX processing library (docx2txt) not available]"
            logging.warning("DOCX extraction failed: docx2txt library not available")
        except Exception as e:
            text = f"[Error extracting DOCX text: {str(e)}]"
            logging.error(f"DOCX extraction error: {str(e)}")
            
        return text


class MarkdownExtractor(DocumentExtractor):
    """Markdown document extractor"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return filename.lower().endswith(('.md', '.markdown'))
    
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from Markdown documents"""
        try:
            # Decode bytes to string
            text = file_content.decode('utf-8', errors='replace')
            return text
        except Exception as e:
            logging.error(f"Markdown extraction error: {str(e)}")
            return f"[Error extracting Markdown text: {str(e)}]"


class TextExtractor(DocumentExtractor):
    """Plain text document extractor"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return filename.lower().endswith('.txt')
    
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from plain text documents"""
        try:
            # Decode bytes to string
            text = file_content.decode('utf-8', errors='replace')
            return text
        except Exception as e:
            logging.error(f"Text extraction error: {str(e)}")
            return f"[Error extracting plain text: {str(e)}]"


class LaTeXExtractor(DocumentExtractor):
    """LaTeX document extractor"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return filename.lower().endswith('.tex')
    
    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from LaTeX documents"""
        try:
            # Decode bytes to string
            latex_content = file_content.decode('utf-8', errors='replace')
            
            # Simple LaTeX cleaning (this is basic - a real implementation would be more sophisticated)
            # Remove commands
            text = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})*', ' ', latex_content)
            # Remove environment markers
            text = re.sub(r'\\begin\{[^}]*\}|\\end\{[^}]*\}', ' ', text)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            logging.error(f"LaTeX extraction error: {str(e)}")
            return f"[Error extracting LaTeX text: {str(e)}]"


class DefaultExtractor(DocumentExtractor):
    """Fallback extractor for unsupported formats"""
    
    @classmethod
    def supports_format(cls, filename: str) -> bool:
        return True  # Fallback for all formats
    
    async def extract_text(self, file_content: bytes) -> str:
        """Try to extract text as plain text"""
        try:
            # Decode bytes to string
            text = file_content.decode('utf-8', errors='replace')
            return text + "\n\n[Note: This file format may not be fully supported]"
        except Exception as e:
            logging.error(f"Default extraction error: {str(e)}")
            return f"[Error extracting text: {str(e)}]"


# Registry of document extractors
_EXTRACTORS = [
    PDFExtractor,
    DocxExtractor,
    MarkdownExtractor,
    TextExtractor,
    LaTeXExtractor,
    # Default extractor should be last
    DefaultExtractor
]


def get_document_extractor(filename: str) -> DocumentExtractor:
    """Factory method to get an appropriate document extractor for the file type"""
    for extractor_class in _EXTRACTORS:
        if extractor_class.supports_format(filename):
            return extractor_class()
    
    # This should never happen because DefaultExtractor supports all formats
    return DefaultExtractor()


async def extract_text_from_document(file_content: bytes, content_type: str, filename: str) -> str:
    """Extract text from document using appropriate extractor"""
    logging.info(f"Extracting text from {filename} ({content_type})")
    
    try:
        extractor = get_document_extractor(filename)
        text = await extractor.extract_text(file_content)
        
        # Log extraction result
        text_length = len(text)
        logging.info(f"Successfully extracted {text_length} characters from {filename}")
        
        return text
    except Exception as e:
        logging.error(f"Error in text extraction: {str(e)}")
        return f"[Error extracting text: {str(e)}]"