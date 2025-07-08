"""
xtotext - AI-Ready Document Conversion System

A powerful document conversion system that transforms documents into AI-friendly formats.
"""

__version__ = "1.0.0"
__author__ = "xtotext Team"

from .core import DocumentConverter
from .workflows import process_markdown_to_pdf

__all__ = ["DocumentConverter", "process_markdown_to_pdf"]