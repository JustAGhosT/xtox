# xtotext Examples

This directory contains example scripts demonstrating how to use the xtotext package.

## Markdown to PDF Example

The `md_to_pdf_example.py` script demonstrates how to convert a Markdown file to PDF using both the `DocumentConverter` class and the `process_markdown_to_pdf` workflow function.

### Usage

```bash
python md_to_pdf_example.py <markdown_file> [output_dir]
```

### Example

```bash
python md_to_pdf_example.py ../test_data/test_doc.md ./output
```

## Requirements

- Python 3.8 or higher
- xtotext package installed
- LaTeX distribution (e.g., TeX Live, MiKTeX, or MacTeX) installed and in the system path