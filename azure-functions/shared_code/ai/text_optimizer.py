"""
Text optimizer module for preparing text for AI consumption.
This module provides functionality to optimize text for various AI models.
"""

import logging
from typing import Tuple, List, Optional
import re

# Import AI modules availability flag
from . import HAVE_AI_MODULES
from .tokenization import get_tokenizer_for_model, split_text_into_chunks

# Import models
from ..models import AIConversionOptions


async def optimize_for_ai(text: str, options: AIConversionOptions) -> Tuple[str, List[str]]:
    """
    Optimize text for AI consumption based on specified options.
    
    Args:
        text: The extracted document text
        options: AI conversion options specifying target model, etc.
        
    Returns:
        Tuple of (optimized_text, list_of_chunks)
    """
    if not HAVE_AI_MODULES:
        logging.warning("AI optimization modules not available, returning raw text")
        return text, [text]
    
    try:
        # Process the text based on options
        processed_text = await process_text(text, options)
        
        # Get chunks based on token limits if specified
        chunks = await get_text_chunks(processed_text, options)
        
        return processed_text, chunks
    
    except Exception as e:
        logging.error(f"Error in AI text optimization: {str(e)}")
        return text, [text]


async def process_text(text: str, options: AIConversionOptions) -> str:
    """
    Process text according to conversion options.
    
    Args:
        text: The raw document text
        options: AI conversion options
        
    Returns:
        Processed text
    """
    processed_text = text
    
    # Add document context headers if requested
    if options.include_metadata:
        processed_text = f"# Document for AI processing\nTarget model: {options.target_model}\n\n{processed_text}"
    
    # Preserve structure if requested, otherwise normalize whitespace
    if not options.preserve_structure:
        # Normalize whitespace (collapse multiple spaces, newlines, etc.)
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
    
    # Apply any additional formatting based on output format
    if options.output_format == "markdown":
        # Ensure proper markdown formatting
        processed_text = ensure_markdown_formatting(processed_text)
    
    return processed_text


async def get_text_chunks(text: str, options: AIConversionOptions) -> List[str]:
    """
    Split text into chunks based on token limits.
    
    Args:
        text: The processed document text
        options: AI conversion options
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    if options.max_tokens:
        try:
            # Get appropriate tokenizer based on model
            tokenizer = get_tokenizer_for_model(options.target_model)
            
            # Use tokenizer to split text
            chunks = await split_text_into_chunks(text, options.max_tokens, 
                                                tokenizer, 
                                                strategy=options.chunking_strategy)
        except Exception as e:
            logging.warning(f"Error in chunking text: {str(e)}")
            # Fallback to simple chunking
            chunks = [text]
    
    # If no chunking was done or it failed, use the entire text as a single chunk
    if not chunks:
        chunks = [text]
    
    return chunks


def ensure_markdown_formatting(text: str) -> str:
    """
    Ensure text has proper markdown formatting.
    
    Args:
        text: The text to format
        
    Returns:
        Markdown-formatted text
    """
    # This is a simple placeholder implementation
    # A real implementation would do much more to format text as proper markdown
    
    # Ensure headings have space after # if they don't already
    text = re.sub(r'^(#{1,6})([^#\s])', r'\1 \2', text, flags=re.MULTILINE)
    
    # Ensure paragraphs are separated by blank lines
    text = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', text)
    
    return text