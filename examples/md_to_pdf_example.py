"""
Example script demonstrating the Markdown to PDF conversion.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from xtox.core import DocumentConverter
from xtox.workflows import process_markdown_to_pdf


def main():
    """
    Convert a Markdown file to PDF.
    """
    # Check if a file was provided
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf_example.py <markdown_file> [output_dir]")
        sys.exit(1)
    
    # Get the input file and optional output directory
    markdown_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if the file exists
    if not os.path.exists(markdown_file):
        print(f"Error: File not found: {markdown_file}")
        sys.exit(1)
    
    # Create output directory if specified and it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting {markdown_file} to PDF...")
    
    try:
        # Method 1: Using the DocumentConverter class
        converter = DocumentConverter(output_dir=output_dir)
        result = converter.markdown_to_pdf(markdown_file, refinement_level=2)
        
        print("\nMethod 1 (DocumentConverter) - Files generated:")
        print(f"  LaTeX: {result['latex_path']}")
        print(f"  PDF: {result['pdf_path']}")
        if result['images']:
            print(f"  Images: {len(result['images'])} files copied")
        
        # Method 2: Using the workflow function
        if output_dir:
            # Use a different output directory for the second method
            alt_output = os.path.join(output_dir, "workflow_output")
            os.makedirs(alt_output, exist_ok=True)
        else:
            alt_output = None
        
        result2 = process_markdown_to_pdf(markdown_file, output_dir=alt_output, refinement_level=2)
        
        print("\nMethod 2 (workflow) - Files generated:")
        print(f"  LaTeX: {result2['latex_path']}")
        print(f"  PDF: {result2['pdf_path']}")
        if result2['images']:
            print(f"  Images: {len(result2['images'])} files copied")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()