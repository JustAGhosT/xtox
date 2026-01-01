import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from xtox.core import convert_markdown_to_latex, latex_to_pdf, fix_latex_structure, check_latex_structure
from xtox.utils.image_handler import copy_images_to_output_dir, update_image_paths

def process_markdown_to_pdf(
    markdown_path: Union[str, Path], 
    output_dir: Optional[str] = None, 
    refinement_level: int = 1
) -> Dict[str, Union[str, List[str]]]:
    """
    Complete workflow to convert Markdown to LaTeX, refine it, and generate PDF.
    
    Args:
        markdown_path: Path to the markdown file
        output_dir: Output directory (defaults to same as input file)
        refinement_level: Level of LaTeX refinement (0-3)
            0: No refinement
            1: Basic structure fixes
            2: Structure fixes with backup
            3: Advanced refinement (future enhancement)
    
    Returns:
        Dictionary with paths to generated files
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
    latex_path = output_dir / f"{base_name}.tex"
    pdf_path = output_dir / f"{base_name}.pdf"
    
    print(f"Starting conversion of {markdown_path}")
    
    # Read markdown content
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(markdown_path, 'r', encoding='latin-1') as f:
            markdown_content = f.read()
    
    # Process images
    print("Processing images...")
    image_path_mapping = copy_images_to_output_dir(markdown_content, str(source_dir), str(output_dir))
    
    if image_path_mapping:
        markdown_content = update_image_paths(markdown_content, image_path_mapping)
        print(f"Processed {len(image_path_mapping)} images")
    
    # Convert to LaTeX
    print("Converting Markdown to LaTeX...")
    latex_content = convert_markdown_to_latex(markdown_content, str(latex_path))
    print(f"LaTeX file created: {latex_path}")
    
    # Apply refinements based on level
    if refinement_level > 0:
        print(f"Refining LaTeX (level {refinement_level})...")
        if refinement_level == 1:
            fix_latex_structure(str(latex_path), backup=False)
        elif refinement_level >= 2:
            fix_latex_structure(str(latex_path), backup=True)
            if refinement_level >= 3:
                # Future enhancement: More advanced LaTeX refinements
                print("Advanced refinement (level 3) - reserved for future enhancements")
    
    # Generate PDF
    print("Generating PDF...")
    success = latex_to_pdf(str(latex_path), auto_fix=(refinement_level > 0))
    
    if not success or not os.path.exists(pdf_path):
        print("PDF generation failed. Checking for issues...")
        has_documentclass, has_begin_document, has_end_document = check_latex_structure(str(latex_path))
        if not all([has_documentclass, has_begin_document, has_end_document]):
            print("LaTeX structure issues detected. Try with higher refinement level.")
        raise RuntimeError(f"PDF generation failed: {pdf_path} not found")
    
    print("\nConversion complete. Files generated:")
    print(f"- LaTeX: {latex_path}")
    print(f"- PDF: {pdf_path}")
    if image_path_mapping:
        print(f"- Images: {len(image_path_mapping)} files processed")
    
    return {
        "latex_path": str(latex_path),
        "pdf_path": str(pdf_path),
        "images": list(image_path_mapping.values()) if image_path_mapping else []
    }