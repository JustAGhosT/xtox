import logging
import json
import azure.functions as func
import asyncio
import uuid
import os
import tempfile
import shutil
import subprocess
from pathlib import Path

from shared_code.database import get_database
from shared_code.storage import store_file
from shared_code.models import ConversionResult

# Utility functions for LaTeX processing
def parse_latex_errors(log_content: str):
    """Parse LaTeX log file to extract errors and warnings"""
    errors = []
    warnings = []
    
    lines = log_content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('!') and 'Error' in line:
            error_msg = line
            # Try to get the next few lines for more context
            for j in range(i + 1, min(i + 3, len(lines))):
                if lines[j].strip() and not lines[j].startswith('l.'):
                    error_msg += " " + lines[j].strip()
                if lines[j].startswith('l.'):
                    error_msg += " " + lines[j].strip()
                    break
            errors.append(error_msg)
        elif 'Warning' in line and not line.startswith('('):
            warnings.append(line.strip())
    
    return errors, warnings

def auto_fix_latex(content: str):
    """Apply basic auto-fixes to LaTeX content"""
    original_content = content
    fixed = False
    
    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
        fixed = True
    
    # Check for \documentclass
    if '\\documentclass' not in content:
        content = '\\documentclass{article}\n' + content
        fixed = True
    
    # Check for \begin{document}
    if '\\begin{document}' not in content:
        # Find where to insert \begin{document}
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('\\documentclass'):
                insert_pos = i + 1
                break
        lines.insert(insert_pos, '\\begin{document}')
        content = '\n'.join(lines)
        fixed = True
    
    # Check for \end{document}
    if '\\end{document}' not in content:
        content = content + '\n\\end{document}'
        fixed = True
    
    return content, fixed

async def process_latex_file(file_content: str, filename: str, auto_fix: bool = False):
    """Process LaTeX file and convert to PDF"""
    conversion_id = str(uuid.uuid4())
    
    # Create temporary directory for this conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        try:
            # Apply auto-fix if requested
            fixed_content = None
            auto_fix_applied = False
            if auto_fix:
                file_content, auto_fix_applied = auto_fix_latex(file_content)
                if auto_fix_applied:
                    fixed_content = file_content
            
            # Write LaTeX file
            tex_file = temp_dir_path / f"{filename}.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Run pdflatex
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', f'{filename}.tex'],
                cwd=temp_dir_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Check if PDF was created
            pdf_file = temp_dir_path / f"{filename}.pdf"
            success = pdf_file.exists()
            
            # Parse errors and warnings
            errors = []
            warnings = []
            if result.returncode != 0 or not success:
                log_file = temp_dir_path / f"{filename}.log"
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    errors, warnings = parse_latex_errors(log_content)
                
                if not errors:
                    errors = [f"LaTeX compilation failed with return code {result.returncode}"]
                    if result.stderr:
                        errors.append(result.stderr)
            
            # Upload PDF to Azure Blob Storage if successful
            pdf_path = None
            if success:
                with open(pdf_file, 'rb') as f:
                    pdf_content = f.read()
                pdf_blob_name = f"conversions/{conversion_id}.pdf"
                pdf_path = await store_file(pdf_content, pdf_blob_name, "application/pdf")
            
            # Create result object
            result_obj = ConversionResult(
                id=conversion_id,
                filename=filename,
                success=success,
                auto_fix_applied=auto_fix_applied,
                errors=errors,
                warnings=warnings,
                pdf_path=pdf_path,
                fixed_content=fixed_content if auto_fix_applied else None
            )
            
            # Store result in database
            db = await get_database()
            await db.conversions.insert_one(result_obj.dict())
            
            return result_obj
            
        except subprocess.TimeoutExpired:
            logging.error("LaTeX compilation timed out")
            raise Exception("LaTeX compilation timed out")
        except Exception as e:
            logging.error(f"Error processing LaTeX: {str(e)}")
            raise

async def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('LaTeX to PDF conversion function triggered')
    
    try:
        # Get the file from the request
        file_data = None
        auto_fix = req.params.get('auto_fix', '').lower() == 'true'
        
        # Check for multipart form data
        if req.files:
            uploaded_file = req.files.get('file')
            if uploaded_file:
                file_data = uploaded_file.read()
                filename = uploaded_file.filename
        else:
            # Try to get file content from request body
            file_data = req.get_body()
            content_disposition = req.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"\'')
            else:
                filename = f"document-{uuid.uuid4()}.tex"
        
        if not file_data:
            return func.HttpResponse(
                json.dumps({"error": "No file provided in the request"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate file type
        if not filename.endswith('.tex'):
            return func.HttpResponse(
                json.dumps({"error": "Only .tex files are supported"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Check file size (limit to 10MB)
        MAX_SIZE = 10 * 1024 * 1024
        if len(file_data) > MAX_SIZE:
            return func.HttpResponse(
                json.dumps({"error": "File too large. Maximum size is 10MB"}),
                status_code=413,
                mimetype="application/json"
            )
        
        # Decode content
        try:
            file_content = file_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                file_content = file_data.decode('latin-1')
            except UnicodeDecodeError:
                return func.HttpResponse(
                    json.dumps({"error": "Unable to decode file. Please ensure it's a valid text file"}),
                    status_code=400,
                    mimetype="application/json"
                )
        
        # Extract filename without extension
        filename_without_ext = filename.rsplit('.', 1)[0]
        
        # Process the file
        result = await process_latex_file(file_content, filename_without_ext, auto_fix)
        
        # Return response
        return func.HttpResponse(
            json.dumps(result.dict(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error converting LaTeX to PDF: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to convert LaTeX to PDF: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )