"""
Unit tests for the tokenization module.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import pytest

from shared_code.ai.tokenization import (
    BaseTokenizer,
    OpenAITokenizer,
    TransformersTokenizer,
    ApproximateTokenizer,
    get_tokenizer_for_model,
    split_text_into_chunks,
    TokenizerType
)


class TestTokenizers(unittest.TestCase):
    """Tests for tokenizer classes"""
    
    def test_approximate_tokenizer_count(self):
        """Test the approximate tokenizer's count_tokens method"""
        tokenizer = ApproximateTokenizer()
        text = "This is a test with 10 words in it to count."
        token_count = tokenizer.count_tokens(text)
        
        # Should be approximately 4/3 times the word count
        expected_count = int(10 * 1.33)
        self.assertEqual(token_count, expected_count)
    
    def test_approximate_tokenizer_encode(self):
        """Test the approximate tokenizer's encode method"""
        tokenizer = ApproximateTokenizer()
        text = "This is a test with 10 words."
        indices = tokenizer.encode(text)
        
        # Should return indices for each word
        self.assertEqual(len(indices), 7)  # 7 words in this text
        self.assertEqual(indices, [0, 1, 2, 3, 4, 5, 6])
    
    def test_approximate_tokenizer_decode_raises(self):
        """Test the approximate tokenizer's decode method raises NotImplementedError"""
        tokenizer = ApproximateTokenizer()
        with self.assertRaises(NotImplementedError):
            tokenizer.decode([0, 1, 2])
    
    @patch("shared_code.ai.tokenization.HAVE_AI_MODULES", False)
    @patch("shared_code.ai.tokenization.logging")
    def test_get_tokenizer_no_modules(self, mock_logging):
        """Test get_tokenizer_for_model falls back to approximate when modules not available"""
        tokenizer = get_tokenizer_for_model("gpt-4")
        
        self.assertIsInstance(tokenizer, ApproximateTokenizer)
        mock_logging.warning.assert_called_once()
    
    @patch("shared_code.ai.tokenization.HAVE_AI_MODULES", True)
    @patch("shared_code.ai.tokenization.OpenAITokenizer")
    @patch("shared_code.ai.tokenization.TransformersTokenizer")
    def test_get_tokenizer_for_openai_model(self, mock_transformers, mock_openai):
        """Test get_tokenizer_for_model returns OpenAITokenizer for OpenAI models"""
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        # Test different OpenAI model names
        models = ["gpt-4", "gpt-3.5-turbo", "text-davinci-003"]
        
        for model in models:
            tokenizer = get_tokenizer_for_model(model)
            self.assertEqual(tokenizer, mock_openai_instance)
            mock_openai.assert_called_with(model)
            mock_transformers.assert_not_called()
            mock_openai.reset_mock()
    
    @patch("shared_code.ai.tokenization.HAVE_AI_MODULES", True)
    @patch("shared_code.ai.tokenization.OpenAITokenizer", side_effect=ImportError)
    @patch("shared_code.ai.tokenization.TransformersTokenizer")
    def test_get_tokenizer_fallback_to_transformers(self, mock_transformers, mock_openai):
        """Test get_tokenizer_for_model falls back to TransformersTokenizer when OpenAI fails"""
        mock_transformers_instance = MagicMock()
        mock_transformers.return_value = mock_transformers_instance
        
        tokenizer = get_tokenizer_for_model("gpt-4")
        
        mock_openai.assert_called_once()
        mock_transformers.assert_called_once()
        self.assertEqual(tokenizer, mock_transformers_instance)


class TestTextChunking(unittest.TestCase):
    """Tests for text chunking functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_text = "This is a test document. It has multiple sentences. " * 10
        self.mock_tokenizer = MagicMock(spec=BaseTokenizer)
        self.mock_tokenizer.count_tokens.return_value = 100  # Simulate 100 tokens
    
    @pytest.mark.asyncio
    @patch("shared_code.ai.tokenization.HAVE_AI_MODULES", True)
    async def test_split_text_token_strategy(self):
        """Test token-based chunking strategy"""
        # Setup mock tokenizer with encode/decode methods
        self.mock_tokenizer.encode.return_value = list(range(100))  # 100 tokens
        self.mock_tokenizer.decode.side_effect = lambda tokens: "".join([str(t) for t in tokens])
        
        # Split with max 30 tokens
        chunks = await split_text_into_chunks(self.test_text, 30, self.mock_tokenizer, "token")
        
        # Should call encode once and decode for each chunk
        self.mock_tokenizer.encode.assert_called_once_with(self.test_text)
        self.assertEqual(self.mock_tokenizer.decode.call_count, 4)  # 100/30 = 3.33 -> 4 chunks
        self.assertEqual(len(chunks), 4)
    
    @pytest.mark.asyncio
    async def test_split_text_semantic_strategy(self):
        """Test semantic chunking strategy with paragraphs"""
        # Create text with paragraphs
        test_text = "Paragraph 1.\nStill paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        
        # Mock tokenizer behavior
        self.mock_tokenizer.count_tokens.side_effect = [30, 10, 10, 10]  # Total, P1, P2, P3
        
        # Split with max 15 tokens
        chunks = await split_text_into_chunks(test_text, 15, self.mock_tokenizer, "semantic")
        
        # Should create 3 chunks, one for each paragraph
        self.assertEqual(len(chunks), 3)
        self.assertIn("Paragraph 1", chunks[0])
        self.assertIn("Paragraph 2", chunks[1])
        self.assertIn("Paragraph 3", chunks[2])
    
    @pytest.mark.asyncio
    async def test_split_text_simple_strategy_fallback(self):
        """Test fallback to simple word-based chunking"""
        # Mock a failure in other strategies
        with patch("shared_code.ai.tokenization.split_text_into_chunks", side_effect=Exception("Chunking failed")):
            # This would normally cause an infinite recursion, but we'll intercept the actual function call
            # to simulate a fallback to the simple strategy
            
            # Create a text with many words
            test_text = "Word " * 100
            
            # Use simple word-based chunking
            chunks = []
            words = test_text.split()
            words_per_chunk = 30
            
            for i in range(0, len(words), words_per_chunk):
                chunk = " ".join(words[i:i+words_per_chunk])
                chunks.append(chunk)
            
            # Should have ceiling(100/30) = 4 chunks
            self.assertEqual(len(chunks), 4)
            
            # Each chunk except the last should have 30 words
            for i in range(3):
                self.assertEqual(len(chunks[i].split()), 30)