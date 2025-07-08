import argparse
import sys
from pathlib import Path

from xtox.core import DocumentConverter


def main():
    parser = argparse.ArgumentParser(
        description="xtotext - AI-Ready Document Conversion System"
    )
    parser.add_argument(
        "input_file", 
        help="Input file to convert (Markdown or LaTeX)"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output directory (default: same as input file)"
    )
    parser.add_argument(
        "-r", "--refinement", 
        type=int, 
        default=1, 
        choices=[0, 1, 2, 3],
        help="LaTeX refinement level (0-3, default: 1)"
    )
    parser.add_argument(
        "--format", 
        choices=["pdf", "latex"], 
        default="pdf",
        help="Output format (default: pdf)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        converter = DocumentConverter(output_dir=args.output)
        
        if input_path.suffix.lower() == '.md':
            result = converter.markdown_to_pdf(
                input_path, 
                args.output, 
                args.refinement
            )
            print(f"Success! Files generated:")
            print(f"  LaTeX: {result['latex_path']}")
            print(f"  PDF: {result['pdf_path']}")
            if result['images']:
                print(f"  Images: {len(result['images'])} files copied")
        
        elif input_path.suffix.lower() == '.tex':
            pdf_path = converter.latex_to_pdf(input_path, auto_fix=True)
            print(f"Success! PDF generated: {pdf_path}")
        
        else:
            print(f"Error: Unsupported file format: {input_path.suffix}")
            print("Supported formats: .md, .tex")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()