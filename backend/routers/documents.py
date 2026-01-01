import logging
from typing import List

from database import Database
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models import DocumentResponse, PermissionUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents")

# TODO: Production hardening - Implement proper JWT authentication
# Current implementation uses environment-based mock auth for development only
async def get_current_user():
    """
    Get current authenticated user.

    TODO: Production implementation required:
    - Extract JWT token from Authorization header
    - Validate token signature and expiration
    - Fetch user from database
    - Cache user data to reduce database queries
    - Implement token refresh mechanism
    """
    import os

    from fastapi import HTTPException

    # Check if mock auth is enabled (development only)
    allow_mock = os.environ.get('ALLOW_MOCK_AUTH', 'false').lower() == 'true'
    is_dev = os.environ.get('ENVIRONMENT', 'development').lower() == 'development'

    if allow_mock and is_dev:
        logger.warning(
            "Mock authentication enabled. "
            "Disable ALLOW_MOCK_AUTH in production!"
        )
        return {"id": "mock_user_id", "username": "mock_user"}

    # Production: Require real authentication
    # TODO: Implement JWT validation
    raise HTTPException(
        status_code=501,
        detail="Authentication not yet implemented. "
        "Enable ALLOW_MOCK_AUTH for development."
    )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(user=Depends(get_current_user)):
    """List documents available to the current user."""
    # TODO: Implement document listing
    # db = Database.get_db()
    # documents = await db.documents.find({"user_id": user["id"]})
    return []


@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Upload a new document."""
    # TODO: Implement document upload
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.put("/{document_id}/permissions", response_model=DocumentResponse)
async def update_permissions(
    document_id: str,
    permission_update: PermissionUpdate,
    user=Depends(get_current_user)
):
    """Update document permissions."""
    # TODO: Implement permission updates
    raise HTTPException(status_code=501, detail="Not yet implemented")