"""
Workflow for converting Markdown to DOCX format.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from xtox.core import convert_markdown_to_docx


def process_markdown_to_docx(markdown_path: str, output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Complete workflow to convert Markdown to DOCX.
    
    Args:
        markdown_path: Path to the markdown file
        output_dir: Output directory (optional)
        
    Returns:
        Dictionary with path to generated DOCX file
    """
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
    
    markdown_path = Path(markdown_path)
    source_dir = markdown_path.parent
    
    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = Path(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
    base_name = markdown_path.stem
    docx_path = output_dir / f"{base_name}.docx"
    
    print(f"Starting conversion of {markdown_path}")
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print("Converting Markdown to DOCX...")
    convert_markdown_to_docx(markdown_content, str(docx_path))
    
    if not os.path.exists(docx_path):
        raise RuntimeError(f"DOCX generation failed: {docx_path} not found")
    
    print("Conversion complete. File generated:")
    print(f"- DOCX: {docx_path}")
    
    return {
        "docx_path": str(docx_path)
    }