"""
Unit tests for the text optimizer module.
"""

import unittest
from unittest.mock import patch, MagicMock
import pytest

from shared_code.ai.text_optimizer import (
    optimize_for_ai,
    process_text,
    get_text_chunks,
    ensure_markdown_formatting
)
from shared_code.models import AIConversionOptions


class TestTextOptimizer(unittest.TestCase):
    """Tests for text optimizer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_text = "This is a test document.\nIt has multiple lines.\nAnd several paragraphs.\n\n"
        self.options = AIConversionOptions(
            target_model="gpt-4",
            preserve_structure=True,
            include_metadata=True,
            max_tokens=1000,
            output_format="standard",
            chunking_strategy="semantic"
        )
    
    @pytest.mark.asyncio
    @patch("shared_code.ai.text_optimizer.HAVE_AI_MODULES", True)
    @patch("shared_code.ai.text_optimizer.process_text")
    @patch("shared_code.ai.text_optimizer.get_text_chunks")
    async def test_optimize_for_ai(self, mock_get_chunks, mock_process):
        """Test optimize_for_ai calls the right functions"""
        mock_process.return_value = "Processed text"
        mock_get_chunks.return_value = ["Chunk 1", "Chunk 2"]
        
        text, chunks = await optimize_for_ai(self.test_text, self.options)
        
        mock_process.assert_called_once_with(self.test_text, self.options)
        mock_get_chunks.assert_called_once_with("Processed text", self.options)
        self.assertEqual(text, "Processed text")
        self.assertEqual(chunks, ["Chunk 1", "Chunk 2"])
    
    @pytest.mark.asyncio
    @patch("shared_code.ai.text_optimizer.HAVE_AI_MODULES", False)
    async def test_optimize_for_ai_no_modules(self):
        """Test optimize_for_ai when AI modules aren't available"""
        text, chunks = await optimize_for_ai(self.test_text, self.options)
        
        self.assertEqual(text, self.test_text)
        self.assertEqual(chunks, [self.test_text])
    
    @pytest.mark.asyncio
    async def test_process_text_with_metadata(self):
        """Test process_text adds metadata when requested"""
        options = AIConversionOptions(include_metadata=True, target_model="test-model")
        
        result = await process_text(self.test_text, options)
        
        self.assertIn("# Document for AI processing", result)
        self.assertIn("Target model: test-model", result)
        self.assertIn(self.test_text, result)
    
    @pytest.mark.asyncio
    async def test_process_text_without_metadata(self):
        """Test process_text doesn't add metadata when not requested"""
        options = AIConversionOptions(include_metadata=False)
        
        result = await process_text(self.test_text, options)
        
        self.assertNotIn("# Document for AI processing", result)
        self.assertEqual(result, self.test_text)
    
    @pytest.mark.asyncio
    async def test_process_text_normalize_whitespace(self):
        """Test process_text normalizes whitespace when preserve_structure=False"""
        options = AIConversionOptions(preserve_structure=False, include_metadata=False)
        
        result = await process_text(self.test_text, options)
        
        self.assertNotIn("\n", result)
        self.assertEqual(result, "This is a test document. It has multiple lines. And several paragraphs.")
    
    @pytest.mark.asyncio
    @patch("shared_code.ai.text_optimizer.get_tokenizer_for_model")
    @patch("shared_code.ai.text_optimizer.split_text_into_chunks")
    async def test_get_text_chunks(self, mock_split, mock_get_tokenizer):
        """Test get_text_chunks calls tokenizer correctly"""
        mock_tokenizer = MagicMock()
        mock_get_tokenizer.return_value = mock_tokenizer
        mock_split.return_value = ["Chunk 1", "Chunk 2"]
        
        chunks = await get_text_chunks(self.test_text, self.options)
        
        mock_get_tokenizer.assert_called_once_with(self.options.target_model)
        mock_split.assert_called_once_with(
            self.test_text,
            self.options.max_tokens,
            mock_tokenizer,
            strategy=self.options.chunking_strategy
        )
        self.assertEqual(chunks, ["Chunk 1", "Chunk 2"])
    
    @pytest.mark.asyncio
    async def test_get_text_chunks_no_max_tokens(self):
        """Test get_text_chunks returns whole text when no max_tokens"""
        options = AIConversionOptions(max_tokens=None)
        
        chunks = await get_text_chunks(self.test_text, options)
        
        self.assertEqual(chunks, [self.test_text])
    
    def test_ensure_markdown_formatting(self):
        """Test markdown formatting function"""
        text = "#Title\nParagraph1\nStill paragraph1\n\nParagraph2"
        
        result = ensure_markdown_formatting(text)
        
        # Should add space after #
        self.assertIn("# Title", result)
        # Should add extra line break between lines of same paragraph
        self.assertIn("Paragraph1\n\nStill paragraph1", result)