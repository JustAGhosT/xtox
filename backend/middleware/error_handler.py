"""
Centralized error handling middleware for FastAPI.

TODO: Production enhancements:
- Add error tracking integration (Sentry, etc.)
- Implement error categorization and alerting
- Add request ID tracking for error correlation
- Create error response templates
- Add error rate monitoring
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Centralized error handling middleware.
    
    Catches all exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except StarletteHTTPException as e:
        # FastAPI HTTP exceptions
        logger.warning(f"HTTP {e.status_code}: {e.detail} - Path: {request.url.path}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "status_code": e.status_code,
                    "message": e.detail,
                    "path": str(request.url.path),
                }
            }
        )
    except RequestValidationError as e:
        # Pydantic validation errors
        logger.warning(f"Validation error: {e.errors()} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "status_code": 422,
                    "message": "Request validation failed",
                    "details": e.errors(),
                    "path": str(request.url.path),
                }
            }
        )
    except ValidationError as e:
        # Pydantic model validation errors
        logger.error(f"Model validation error: {e.errors()} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "model_validation_error",
                    "status_code": 500,
                    "message": "Internal validation error",
                    "path": str(request.url.path),
                }
            }
        )
    except Exception as e:
        # Unexpected errors
        logger.error(
            f"Unexpected error: {str(e)} - Path: {request.url.path}",
            exc_info=True
        )
        # Don't expose internal error details in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "internal_server_error",
                    "status_code": 500,
                    "message": "An internal server error occurred",
                    "path": str(request.url.path),
                }
            }
        )

