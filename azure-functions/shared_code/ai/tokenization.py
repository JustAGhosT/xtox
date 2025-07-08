"""
Tokenization module for handling tokens and text chunking.
This module provides functionality for tokenizing text and creating chunks based on token limits.
"""

import logging
from typing import List, Callable, Optional, Dict, Any
from enum import Enum

# Import AI modules availability flag
from . import HAVE_AI_MODULES

# Tokenizer types
class TokenizerType(Enum):
    OPENAI = "openai"
    TRANSFORMERS = "transformers"
    APPROXIMATE = "approximate"


class BaseTokenizer:
    """Base tokenizer interface"""
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text"""
        raise NotImplementedError
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        raise NotImplementedError
    
    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text"""
        raise NotImplementedError


class OpenAITokenizer(BaseTokenizer):
    """Tokenizer for OpenAI models using tiktoken"""
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize with a specific model name"""
        if not HAVE_AI_MODULES:
            raise ImportError("tiktoken module is not available")
        
        import tiktoken
        self.model_name = model_name
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base for newer or custom models
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text"""
        return len(self.encode(text))
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        return self.encoding.encode(text)
    
    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text"""
        return self.encoding.decode(tokens)


class TransformersTokenizer(BaseTokenizer):
    """Tokenizer using HuggingFace Transformers"""
    
    def __init__(self, model_name: str = "gpt2"):
        """Initialize with a specific model name"""
        if not HAVE_AI_MODULES:
            raise ImportError("transformers module is not available")
        
        from transformers import AutoTokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:
            logging.warning(f"Failed to load {model_name} tokenizer: {e}")
            # Fallback to GPT-2 tokenizer which is widely compatible
            self.tokenizer = AutoTokenizer.from_pretrained("gpt2")
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text"""
        return len(self.encode(text))
    
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs"""
        return self.tokenizer.encode(text)
    
    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text"""
        return self.tokenizer.decode(tokens)


class ApproximateTokenizer(BaseTokenizer):
    """Simple tokenizer that approximates token counts based on words"""
    
    def count_tokens(self, text: str) -> int:
        """
        Approximate token count based on words.
        A rough approximation: 1 token ≈ 0.75 words, or 4 tokens ≈ 3 words
        """
        words = text.split()
        return int(len(words) * 1.33)  # 4/3 ratio
    
    def encode(self, text: str) -> List[int]:
        """
        This doesn't actually encode tokens but returns word indices as a proxy.
        Should not be used for actual encoding/decoding operations.
        """
        words = text.split()
        # This is just a placeholder that returns word indices
        return list(range(len(words)))
    
    def decode(self, tokens: List[int]) -> str:
        """Not implemented for approximate tokenizer"""
        raise NotImplementedError("ApproximateTokenizer cannot decode tokens")


def get_tokenizer_for_model(model_name: str) -> BaseTokenizer:
    """
    Get the appropriate tokenizer for a given model name.
    
    Args:
        model_name: Name of the target AI model
        
    Returns:
        A tokenizer instance
    """
    model_lower = model_name.lower()
    
    if not HAVE_AI_MODULES:
        logging.warning("AI modules not available, using approximate tokenizer")
        return ApproximateTokenizer()
    
    try:
        # Try to use tiktoken for OpenAI models
        if "gpt" in model_lower or "text-davinci" in model_lower or "openai" in model_lower:
            import tiktoken
            return OpenAITokenizer(model_name)
    except ImportError:
        logging.warning("tiktoken not available")
    
    try:
        # Try to use transformers for other models
        if HAVE_AI_MODULES:
            return TransformersTokenizer(model_name)
    except ImportError:
        logging.warning("transformers not available")
    
    # Fallback to approximate tokenizer
    logging.warning(f"No specific tokenizer available for {model_name}, using approximate tokenizer")
    return ApproximateTokenizer()


async def split_text_into_chunks(
    text: str, 
    max_tokens: int,
    tokenizer: BaseTokenizer,
    strategy: str = "semantic"
) -> List[str]:
    """
    Split text into chunks based on token limit.
    
    Args:
        text: The text to split
        max_tokens: Maximum tokens per chunk
        tokenizer: Tokenizer to use for counting tokens
        strategy: Chunking strategy ("semantic", "token", or "simple")
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # Use different chunking strategies based on the specified strategy
    if strategy == "token" and hasattr(tokenizer, "encode") and hasattr(tokenizer, "decode"):
        # Token-based chunking (most precise)
        try:
            tokens = tokenizer.encode(text)
            
            # Create chunks based on token count
            current_chunk = []
            current_length = 0
            
            for token in tokens:
                if current_length + 1 > max_tokens:
                    # Convert tokens back to text and add to chunks
                    chunk_text = tokenizer.decode(current_chunk)
                    chunks.append(chunk_text)
                    current_chunk = [token]
                    current_length = 1
                else:
                    current_chunk.append(token)
                    current_length += 1
            
            # Add the last chunk
            if current_chunk:
                chunk_text = tokenizer.decode(current_chunk)
                chunks.append(chunk_text)
            
            return chunks
        except Exception as e:
            logging.warning(f"Token-based chunking failed: {str(e)}")
            # Fall through to simple chunking
    
    elif strategy == "semantic":
        # Semantic chunking tries to keep paragraphs together
        try:
            # Split by paragraphs (double newlines)
            paragraphs = text.split("\n\n")
            
            current_chunk = []
            current_token_count = 0
            
            for paragraph in paragraphs:
                paragraph_token_count = tokenizer.count_tokens(paragraph)
                
                if paragraph_token_count > max_tokens:
                    # If a single paragraph is too long, we need to split it
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = []
                        current_token_count = 0
                    
                    # Split the paragraph using simple word-based chunking
                    words = paragraph.split()
                    temp_chunk = []
                    temp_token_count = 0
                    
                    for word in words:
                        word_with_space = word + " "
                        word_token_count = tokenizer.count_tokens(word_with_space)
                        
                        if temp_token_count + word_token_count > max_tokens:
                            chunks.append(" ".join(temp_chunk))
                            temp_chunk = [word]
                            temp_token_count = word_token_count
                        else:
                            temp_chunk.append(word)
                            temp_token_count += word_token_count
                    
                    if temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                
                elif current_token_count + paragraph_token_count > max_tokens:
                    # If adding this paragraph would exceed the limit, start a new chunk
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = [paragraph]
                    current_token_count = paragraph_token_count
                else:
                    # Add paragraph to the current chunk
                    current_chunk.append(paragraph)
                    current_token_count += paragraph_token_count
            
            # Add the last chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            
            return chunks
        except Exception as e:
            logging.warning(f"Semantic chunking failed: {str(e)}")
            # Fall through to simple chunking
    
    # Simple word-based chunking (fallback)
    try:
        words = text.split()
        words_per_chunk = max(1, int(max_tokens / 1.33))  # Approximate words per chunk
        
        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i:i+words_per_chunk])
            chunks.append(chunk)
    except Exception as e:
        logging.error(f"Simple chunking failed: {str(e)}")
        # Last resort fallback
        chunks = [text]
    
    return chunks