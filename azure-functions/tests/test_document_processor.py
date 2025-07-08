"""
Unit tests for the document processor module.
"""

import unittest
import asyncio
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from shared_code.ai.document_processor import (
    extract_text_from_document,
    get_document_extractor,
    PDFExtractor,
    DocxExtractor,
    MarkdownExtractor,
    TextExtractor,
    LaTeXExtractor,
    DefaultExtractor
)


class TestDocumentExtractors(unittest.TestCase):
    """Tests for document extractors"""
    
    def test_get_document_extractor(self):
        """Test get_document_extractor returns the correct extractor class"""
        self.assertIsInstance(get_document_extractor("test.pdf"), PDFExtractor)
        self.assertIsInstance(get_document_extractor("test.docx"), DocxExtractor)
        self.assertIsInstance(get_document_extractor("test.md"), MarkdownExtractor)
        self.assertIsInstance(get_document_extractor("test.markdown"), MarkdownExtractor)
        self.assertIsInstance(get_document_extractor("test.txt"), TextExtractor)
        self.assertIsInstance(get_document_extractor("test.tex"), LaTeXExtractor)
        self.assertIsInstance(get_document_extractor("test.unknown"), DefaultExtractor)
    
    def test_supports_format(self):
        """Test file format support detection"""
        self.assertTrue(PDFExtractor.supports_format("test.pdf"))
        self.assertTrue(PDFExtractor.supports_format("TEST.PDF"))
        self.assertFalse(PDFExtractor.supports_format("test.docx"))
        
        self.assertTrue(DocxExtractor.supports_format("test.docx"))
        self.assertFalse(DocxExtractor.supports_format("test.pdf"))
        
        self.assertTrue(MarkdownExtractor.supports_format("test.md"))
        self.assertTrue(MarkdownExtractor.supports_format("test.markdown"))
        self.assertFalse(MarkdownExtractor.supports_format("test.txt"))
        
        self.assertTrue(TextExtractor.supports_format("test.txt"))
        self.assertFalse(TextExtractor.supports_format("test.md"))
        
        self.assertTrue(LaTeXExtractor.supports_format("test.tex"))
        self.assertFalse(LaTeXExtractor.supports_format("test.txt"))
        
        # Default extractor supports all formats
        self.assertTrue(DefaultExtractor.supports_format("anything.xyz"))


class TestTextExtraction(unittest.TestCase):
    """Tests for text extraction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_text = "This is a test document.\nIt has multiple lines.\n"
        self.test_latex = "\\documentclass{article}\n\\begin{document}\nThis is a test document.\n\\end{document}"
        
        # Create test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.txt_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(self.txt_path, "w") as f:
            f.write(self.test_text)
            
        self.latex_path = os.path.join(self.temp_dir.name, "test.tex")
        with open(self.latex_path, "w") as f:
            f.write(self.test_latex)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()
    
    @pytest.mark.asyncio
    async def test_text_extractor(self):
        """Test text extraction from a plain text file"""
        with open(self.txt_path, "rb") as f:
            content = f.read()
        
        extractor = TextExtractor()
        result = await extractor.extract_text(content)
        
        self.assertEqual(result, self.test_text)
    
    @pytest.mark.asyncio
    async def test_latex_extractor(self):
        """Test text extraction from a LaTeX file"""
        with open(self.latex_path, "rb") as f:
            content = f.read()
        
        extractor = LaTeXExtractor()
        result = await extractor.extract_text(content)
        
        # LaTeX extractor should strip commands but keep the text
        self.assertIn("This is a test document", result)
        self.assertNotIn("\\documentclass", result)
        self.assertNotIn("\\begin{document}", result)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_document(self):
        """Test the main extract_text_from_document function"""
        with open(self.txt_path, "rb") as f:
            content = f.read()
        
        result = await extract_text_from_document(content, "text/plain", "test.txt")
        
        self.assertEqual(result, self.test_text)
    
    @pytest.mark.asyncio
    @patch("shared_code.ai.document_processor.PDFExtractor.extract_text")
    async def test_pdf_extraction_called_correctly(self, mock_extract):
        """Test that PDF extraction is called correctly"""
        mock_extract.return_value = "Mock PDF content"
        
        result = await extract_text_from_document(b"fake pdf content", "application/pdf", "test.pdf")
        
        mock_extract.assert_called_once()
        self.assertEqual(result, "Mock PDF content")
    
    @pytest.mark.asyncio
    async def test_extraction_error_handling(self):
        """Test error handling in extraction"""
        # Test with invalid content that will cause a decode error
        result = await extract_text_from_document(b'\x80\x81', "text/plain", "test.txt")
        
        self.assertIn("[Error extracting", result)