import re
import os
from pathlib import Path

def convert_markdown_to_latex(markdown_content, output_path=None, include_preamble=True):
    """
    Convert Markdown content to LaTeX.
    
    Parameters:
    -----------
    markdown_content : str
        The Markdown content to convert
    output_path : str, optional
        Path to save the LaTeX output
    include_preamble : bool, default=True
        Whether to include a standard LaTeX preamble
        
    Returns:
    --------
    str
        The LaTeX content
    """
    # Initialize LaTeX content with a standard preamble if requested
    latex_content = ""
    if include_preamble:
        latex_content = """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{graphicx}
\\usepackage{hyperref}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{listings}
\\usepackage{xcolor}
\\usepackage{booktabs}

\\title{Converted from Markdown}
\\author{}
\\date{\\today}

\\begin{document}
\\maketitle

"""
    
    # Process Markdown content
    lines = markdown_content.split('\n')
    in_code_block = False
    in_list = False
    
    for line in lines:
        # Headers
        if line.startswith('# '):
            latex_content += f"\\section{{{line[2:]}}}\n\n"
        elif line.startswith('## '):
            latex_content += f"\\subsection{{{line[3:]}}}\n\n"
        elif line.startswith('### '):
            latex_content += f"\\subsubsection{{{line[4:]}}}\n\n"
        
        # Images
        # ![alt text](image_path)
        elif '![' in line and '](' in line:
            alt_text = re.search(r'!\[(.*?)\]', line).group(1)
            image_path = re.search(r'\((.*?)\)', line).group(1)
            
            # Make sure path is using forward slashes for LaTeX
            image_path = image_path.replace('\\', '/')
            
            latex_content += f"""
\\begin{{figure}}[h]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{image_path}}}
\\caption{{{alt_text}}}
\\end{{figure}}
"""
        
        # Code blocks
        elif line.startswith('```'):
            if in_code_block:
                latex_content += "\\end{lstlisting}\n\n"
                in_code_block = False
            else:
                language = line[3:].strip()
                if language:
                    latex_content += f"\\begin{{lstlisting}}[language={language}]\n"
                else:
                    latex_content += "\\begin{lstlisting}\n"
                in_code_block = True
        
        # Regular text (inside or outside code blocks)
        elif in_code_block:
            latex_content += line + "\n"
        else:
            # Lists
            if line.strip().startswith('- '):
                if not in_list:
                    latex_content += "\\begin{itemize}\n"
                    in_list = True
                latex_content += f"\\item {line.strip()[2:]}\n"
            elif in_list and not line.strip().startswith('- '):
                if in_list:
                    latex_content += "\\end{itemize}\n\n"
                    in_list = False
                if line.strip():
                    latex_content += line + "\n\n"
            elif line.strip():
                latex_content += line + "\n\n"
    
    # Close any open environments
    if in_list:
        latex_content += "\\end{itemize}\n\n"
    if in_code_block:
        latex_content += "\\end{lstlisting}\n\n"
    
    # Close document if preamble was included
    if include_preamble:
        latex_content += "\\end{document}"
    
    # Save to file if output path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
    
    return latex_content