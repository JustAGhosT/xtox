"""
Shared code package for xtotext Azure Functions.
This package contains reusable modules used across multiple Azure Functions.
"""

import logging

# Configure common logging
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.functions').setLevel(logging.INFO)

# Initialize package
__version__ = "1.0.0"