"""
Convert HTML to Markdown format.
"""

import re
from pathlib import Path
from typing import Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("beautifulsoup4 is required for HTML conversion. Install with: pip install beautifulsoup4")


def convert_html_to_markdown(html_content: str, output_path: Optional[str] = None) -> str:
    """
    Convert HTML content to Markdown.
    
    Args:
        html_content: The HTML content to convert
        output_path: Path to save the Markdown output
        
    Returns:
        The Markdown content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    markdown_content = _convert_element(soup)
    
    # Clean up extra whitespace
    markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
    markdown_content = markdown_content.strip()
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    return markdown_content


def _convert_element(element) -> str:
    """Convert a BeautifulSoup element to Markdown."""
    if element.name is None:
        # Text node
        return element.string or ""
    
    content = ""
    for child in element.children:
        content += _convert_element(child)
    
    # Handle different HTML tags
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        level = int(element.name[1])
        return f"{'#' * level} {content.strip()}\n\n"
    
    elif element.name == 'p':
        return f"{content.strip()}\n\n"
    
    elif element.name == 'strong' or element.name == 'b':
        return f"**{content}**"
    
    elif element.name == 'em' or element.name == 'i':
        return f"*{content}*"
    
    elif element.name == 'code':
        return f"`{content}`"
    
    elif element.name == 'pre':
        return f"```\n{content}\n```\n\n"
    
    elif element.name == 'a':
        href = element.get('href', '')
        return f"[{content}]({href})"
    
    elif element.name == 'img':
        src = element.get('src', '')
        alt = element.get('alt', '')
        return f"![{alt}]({src})"
    
    elif element.name in ['ul', 'ol']:
        return f"{content}\n"
    
    elif element.name == 'li':
        return f"- {content.strip()}\n"
    
    elif element.name == 'blockquote':
        lines = content.strip().split('\n')
        quoted_lines = [f"> {line}" for line in lines if line.strip()]
        return '\n'.join(quoted_lines) + '\n\n'
    
    elif element.name == 'br':
        return '\n'
    
    elif element.name in ['div', 'span', 'body', 'html']:
        return content
    
    else:
        return content