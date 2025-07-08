import logging
import tempfile
import shutil
import os
import json
from pathlib import Path

import azure.functions as func
from ..shared_code.auth import get_current_user_from_request
from ..shared_code.storage import store_file, generate_sas_url
from ..docs.md_to_pdf_workflow import process_markdown_to_pdf

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function for converting Markdown to PDF.
    """
    logging.info('Processing Markdown to PDF conversion request')
    
    try:
        # Get current user (optional - for permission checks)
        # user_id = get_current_user_from_request(req)
        
        # Check if the request has files
        files = req.files.get('file')
        if not files:
            return func.HttpResponse(
                "No file provided. Please upload a Markdown file.",
                status_code=400
            )
        
        file = files[0]
        
        # Get refinement level from query parameters
        refinement_level = int(req.params.get('refinement_level', 1))
        
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save the uploaded file to the temporary directory
            markdown_path = os.path.join(temp_dir, file.filename)
            file_content = file.stream.read()
            
            with open(markdown_path, 'wb') as f:
                f.write(file_content)
            
            # Process the Markdown file
            result = process_markdown_to_pdf(markdown_path, temp_dir, refinement_level)
            
            # Store the PDF in blob storage
            pdf_path = result['pdf_path']
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Generate a unique blob name
            pdf_filename = os.path.basename(pdf_path)
            blob_name = f"pdf/{Path(pdf_path).stem}_{os.urandom(4).hex()}.pdf"
            
            # Store the file and get download URL
            store_file(pdf_content, blob_name, 'application/pdf')
            download_url = generate_sas_url(blob_name)
            
            # Return success response with download link
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "pdf_url": download_url,
                    "filename": pdf_filename
                }),
                mimetype="application/json"
            )
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        logging.error(f"Error converting Markdown to PDF: {str(e)}")
        return func.HttpResponse(
            f"Error converting Markdown to PDF: {str(e)}",
            status_code=500
        )