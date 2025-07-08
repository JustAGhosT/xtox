"""
Azure Function for converting documents to AI-ready text format.
This function processes documents and optimizes them for AI model consumption.
"""

import logging
import azure.functions as func
from .handler import process_request

async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main entry point for the ConvertToAIText Azure Function.
    
    Args:
        req: The HTTP request object
        
    Returns:
        HTTP response with the conversion result or error message
    """
    logging.info('AI document conversion function triggered')
    return await process_request(req)