"""
Main document converter class that orchestrates all conversion operations.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from .markdown_to_latex import convert_markdown_to_latex
from .markdown_to_docx import convert_markdown_to_docx
from .markdown_to_html import convert_markdown_to_html
from .html_to_markdown import convert_html_to_markdown
from .latex_to_pdf import latex_to_pdf, fix_latex_structure
from ..utils.image_handler import copy_images_to_output_dir, update_image_paths


class DocumentConverter:
    """
    Main converter class that handles document transformations.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the document converter.
        
        Args:
            output_dir: Default output directory for conversions
        """
        self.output_dir = Path(output_dir) if output_dir else None
    
    def markdown_to_pdf(
        self, 
        markdown_path: Union[str, Path], 
        output_dir: Optional[str] = None,
        refinement_level: int = 1
    ) -> Dict[str, str]:
        """
        Convert Markdown file to PDF.
        
        Args:
            markdown_path: Path to the markdown file
            output_dir: Output directory (overrides default)
            refinement_level: Level of LaTeX refinement (0-3)
            
        Returns:
            Dictionary with paths to generated files
        """
        markdown_path = Path(markdown_path)
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        elif self.output_dir:
            output_path = self.output_dir
        else:
            output_path = markdown_path.parent
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate file paths
        base_name = markdown_path.stem
        latex_path = output_path / f"{base_name}.tex"
        pdf_path = output_path / f"{base_name}.pdf"
        
        # Read markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Process images
        image_mapping = copy_images_to_output_dir(
            markdown_content, 
            str(markdown_path.parent), 
            str(output_path)
        )
        
        if image_mapping:
            markdown_content = update_image_paths(markdown_content, image_mapping)
        
        # Convert to LaTeX
        latex_content = convert_markdown_to_latex(markdown_content, str(latex_path))
        
        # Apply refinements
        if refinement_level > 0:
            if refinement_level == 1:
                fix_latex_structure(str(latex_path))
            elif refinement_level >= 2:
                fix_latex_structure(str(latex_path), backup=True)
        
        # Generate PDF
        success = latex_to_pdf(str(latex_path), auto_fix=(refinement_level > 0))
        
        if not success or not pdf_path.exists():
            raise RuntimeError(f"PDF generation failed: {pdf_path}")
        
        return {
            "latex_path": str(latex_path),
            "pdf_path": str(pdf_path),
            "images": list(image_mapping.values()) if image_mapping else []
        }
    
    def latex_to_pdf(
        self, 
        latex_path: Union[str, Path], 
        auto_fix: bool = True
    ) -> str:
        """
        Convert LaTeX file to PDF.
        
        Args:
            latex_path: Path to the LaTeX file
            auto_fix: Whether to automatically fix LaTeX structure issues
            
        Returns:
            Path to generated PDF file
        """
        latex_path = Path(latex_path)
        if not latex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {latex_path}")
        
        success = latex_to_pdf(str(latex_path), auto_fix=auto_fix)
        
        pdf_path = latex_path.with_suffix('.pdf')
        if not success or not pdf_path.exists():
            raise RuntimeError(f"PDF generation failed: {pdf_path}")
        
        return str(pdf_path)
    
    def markdown_to_docx(
        self, 
        markdown_path: Union[str, Path], 
        output_dir: Optional[str] = None
    ) -> str:
        """
        Convert Markdown file to DOCX.
        
        Args:
            markdown_path: Path to the markdown file
            output_dir: Output directory (overrides default)
            
        Returns:
            Path to generated DOCX file
        """
        markdown_path = Path(markdown_path)
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        elif self.output_dir:
            output_path = self.output_dir
        else:
            output_path = markdown_path.parent
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        base_name = markdown_path.stem
        docx_path = output_path / f"{base_name}.docx"
        
        # Read markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to DOCX
        convert_markdown_to_docx(markdown_content, str(docx_path))
        
        if not docx_path.exists():
            raise RuntimeError(f"DOCX generation failed: {docx_path}")
        
        return str(docx_path)
    
    def markdown_to_html(
        self, 
        markdown_path: Union[str, Path], 
        output_dir: Optional[str] = None,
        include_css: bool = True
    ) -> str:
        """
        Convert Markdown file to HTML.
        
        Args:
            markdown_path: Path to the markdown file
            output_dir: Output directory (overrides default)
            include_css: Whether to include CSS styling
            
        Returns:
            Path to generated HTML file
        """
        markdown_path = Path(markdown_path)
        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        elif self.output_dir:
            output_path = self.output_dir
        else:
            output_path = markdown_path.parent
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        base_name = markdown_path.stem
        html_path = output_path / f"{base_name}.html"
        
        # Read markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to HTML
        convert_markdown_to_html(markdown_content, str(html_path), include_css)
        
        if not html_path.exists():
            raise RuntimeError(f"HTML generation failed: {html_path}")
        
        return str(html_path)
    
    def html_to_markdown(
        self, 
        html_path: Union[str, Path], 
        output_dir: Optional[str] = None
    ) -> str:
        """
        Convert HTML file to Markdown.
        
        Args:
            html_path: Path to the HTML file
            output_dir: Output directory (overrides default)
            
        Returns:
            Path to generated Markdown file
        """
        html_path = Path(html_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        elif self.output_dir:
            output_path = self.output_dir
        else:
            output_path = html_path.parent
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate file path
        base_name = html_path.stem
        md_path = output_path / f"{base_name}.md"
        
        # Read HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Convert to Markdown
        convert_html_to_markdown(html_content, str(md_path))
        
        if not md_path.exists():
            raise RuntimeError(f"Markdown generation failed: {md_path}")
        
        return str(md_path)