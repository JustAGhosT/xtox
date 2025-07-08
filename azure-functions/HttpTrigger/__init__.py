import azure.functions as func
import logging
from ..function_app import func_app

# This delegates the request handling to the ASGI app (FastAPI)
main = func_app