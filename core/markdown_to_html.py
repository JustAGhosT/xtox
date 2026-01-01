"""
Convert Markdown to HTML format.
"""

import re
from pathlib import Path
from typing import Optional


def convert_markdown_to_html(markdown_content: str, output_path: Optional[str] = None, include_css: bool = True) -> str:
    """
    Convert Markdown content to HTML.
    
    Args:
        markdown_content: The Markdown content to convert
        output_path: Path to save the HTML output
        include_css: Whether to include basic CSS styling
        
    Returns:
        The HTML content
    """
    html_content = ""
    
    if include_css:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted from Markdown</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { color: #333; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 4px solid #ddd; margin: 0; padding-left: 20px; color: #666; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        img { max-width: 100%; height: auto; }
    </style>
</head>
<body>

"""
    
    lines = markdown_content.split('\n')
    in_code_block = False
    in_list = False
    in_blockquote = False
    
    for line in lines:
        line = line.rstrip()
        
        # Headers
        if line.startswith('# '):
            html_content += f"<h1>{_escape_html(line[2:])}</h1>\n"
        elif line.startswith('## '):
            html_content += f"<h2>{_escape_html(line[3:])}</h2>\n"
        elif line.startswith('### '):
            html_content += f"<h3>{_escape_html(line[4:])}</h3>\n"
        
        # Images
        elif '![' in line and '](' in line:
            alt_text = re.search(r'!\[(.*?)\]', line)
            image_path = re.search(r'\((.*?)\)', line)
            if alt_text and image_path:
                html_content += f'<img src="{image_path.group(1)}" alt="{_escape_html(alt_text.group(1))}">\n'
        
        # Code blocks
        elif line.startswith('```'):
            if in_code_block:
                html_content += "</pre>\n"
                in_code_block = False
            else:
                html_content += "<pre><code>"
                in_code_block = True
        
        # Lists
        elif line.strip().startswith('- '):
            if not in_list:
                html_content += "<ul>\n"
                in_list = True
            html_content += f"<li>{_process_inline_formatting(line.strip()[2:])}</li>\n"
        elif in_list and not line.strip().startswith('- '):
            html_content += "</ul>\n"
            in_list = False
            if line.strip():
                html_content += f"<p>{_process_inline_formatting(line)}</p>\n"
        
        # Blockquotes
        elif line.startswith('> '):
            if not in_blockquote:
                html_content += "<blockquote>\n"
                in_blockquote = True
            html_content += f"<p>{_process_inline_formatting(line[2:])}</p>\n"
        elif in_blockquote and not line.startswith('> '):
            html_content += "</blockquote>\n"
            in_blockquote = False
            if line.strip():
                html_content += f"<p>{_process_inline_formatting(line)}</p>\n"
        
        # Regular text
        elif in_code_block:
            html_content += _escape_html(line) + "\n"
        elif line.strip():
            html_content += f"<p>{_process_inline_formatting(line)}</p>\n"
        else:
            html_content += "\n"
    
    # Close open tags
    if in_list:
        html_content += "</ul>\n"
    if in_blockquote:
        html_content += "</blockquote>\n"
    if in_code_block:
        html_content += "</code></pre>\n"
    
    if include_css:
        html_content += "\n</body>\n</html>"
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    return html_content


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _process_inline_formatting(text: str) -> str:
    """Process inline Markdown formatting."""
    text = _escape_html(text)
    
    # Bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Italic
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    return text