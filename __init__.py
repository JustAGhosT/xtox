"""
xtotext - AI-Ready Document Conversion System

A powerful document conversion system that transforms documents into AI-friendly formats.
"""

__version__ = "1.0.0"
__author__ = "xtotext Team"

from .core import DocumentConverter, ImageConverter, MultiDocumentProcessor
from .workflows import process_markdown_to_pdf, process_markdown_to_docx

__all__ = [
    "DocumentConverter", 
    "ImageConverter", 
    "MultiDocumentProcessor",
    "process_markdown_to_pdf", 
    "process_markdown_to_docx"
]