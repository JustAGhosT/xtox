import os
import tempfile
from xtox.workflows.md_to_pdf import process_markdown_to_pdf

def create_api_endpoint():
    """
    Factory to create an API endpoint for the markdown to PDF conversion.
    This can be imported and used in a web framework like FastAPI or Flask.
    """
    async def convert_markdown_to_pdf_api(file, refinement_level=1):
        # This is an async function, assuming usage with a framework like FastAPI
        # that provides the 'file' object.
        temp_dir = tempfile.mkdtemp()
        try:
            markdown_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            with open(markdown_path, "wb") as f:
                f.write(content)
            
            result = process_markdown_to_pdf(markdown_path, temp_dir, refinement_level)
            
            # The calling framework would be responsible for returning the file response.
            return result
        except Exception as e:
            print(f"Error in conversion: {e}")
            # Proper error handling and HTTP response should be done by the framework
            raise
        
    return convert_markdown_to_pdf_api