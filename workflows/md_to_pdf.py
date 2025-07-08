import os
from pathlib import Path

from xtox.core import convert_markdown_to_latex, latex_to_pdf, fix_latex_structure
from xtox.utils.image_handler import copy_images_to_output_dir, update_image_paths

def process_markdown_to_pdf(markdown_path, output_dir=None, refinement_level=1):
    """
    Complete workflow to convert Markdown to LaTeX, refine it, and generate PDF.
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
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    print("Processing images...")
    image_path_mapping = copy_images_to_output_dir(markdown_content, str(source_dir), str(output_dir))
    
    if image_path_mapping:
        markdown_content = update_image_paths(markdown_content, image_path_mapping)
    
    print("Converting Markdown to LaTeX...")
    latex_content = convert_markdown_to_latex(markdown_content, str(latex_path))
    
    if refinement_level > 0:
        print("Refining LaTeX...")
        if refinement_level == 1:
            fix_latex_structure(str(latex_path))
        elif refinement_level >= 2:
            fix_latex_structure(str(latex_path), backup=True)
            if refinement_level >= 3:
                pass
    
    print("Generating PDF...")
    latex_to_pdf(str(latex_path), auto_fix=(refinement_level > 0))
    
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF generation failed: {pdf_path} not found")
    
    print("Conversion complete. Files generated:")
    print(f"- LaTeX: {latex_path}")
    print(f"- PDF: {pdf_path}")
    
    return {
        "latex_path": str(latex_path),
        "pdf_path": str(pdf_path),
        "images": list(image_path_mapping.values()) if image_path_mapping else []
    }