"""
AI processing modules for xtotext document conversion system.
This package contains modules for document text extraction, AI optimization, and tokenization.
"""

# Check for available AI modules
try:
    import tiktoken
    import spacy
    from transformers import pipeline
    HAVE_AI_MODULES = True
except ImportError:
    HAVE_AI_MODULES = False