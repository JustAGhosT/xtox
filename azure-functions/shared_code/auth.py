"""
Authentication and authorization module for xtotext.
This module provides functionality for user authentication and permission checking.
"""

import logging
import json
from typing import Dict, List, Optional, Union, Any
import azure.functions as func
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import InvalidTokenError

from .database import get_database
from .models import User, Permission, Document


class AuthError(Exception):
    """Base class for authentication errors"""
    pass


class UnauthorizedError(AuthError):
    """Raised when a user is not authenticated"""
    pass


class ForbiddenError(AuthError):
    """Raised when a user doesn't have required permissions"""
    pass


async def get_current_user_from_request(req: func.HttpRequest) -> User:
    """
    Extract and validate the current user from the request.
    
    Args:
        req: The HTTP request
        
    Returns:
        The authenticated user
        
    Raises:
        UnauthorizedError: If the user is not authenticated
    """
    # Get token from header
    auth_header = req.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        # TODO: Production hardening - Remove mock authentication bypass
        # Check if mock auth is explicitly enabled for development/testing only
        allow_mock_auth = os.environ.get('ALLOW_MOCK_AUTH', 'false').lower() == 'true'
        is_development = os.environ.get('ENVIRONMENT', 'development').lower() == 'development'
        
        if allow_mock_auth and is_development:
            # Only allow mock auth in development with explicit flag
            user_id = req.params.get('user_id')
            if user_id and user_id.startswith('mock_'):
                logging.warning(f"Mock authentication used for user: {user_id}. Disable in production!")
                return User(
                    id=user_id,
                    email=f"{user_id}@example.com",
                    name=f"Mock User ({user_id})",
                    roles=["user"]
                )
        
        raise UnauthorizedError("No valid authentication token provided")
    
    # Extract token
    token = auth_header.split(' ')[1]
    
    try:
        # Decode and validate token
        # Note: In production, you would use proper key validation
        secret_key = get_auth_secret_key()
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Get user from database
        db = await get_database()
        user_data = await db.users.find_one({"id": payload["sub"]})
        
        if not user_data:
            raise UnauthorizedError("User not found")
        
        # Update last login time
        await db.users.update_one(
            {"id": payload["sub"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return User(**user_data)
    
    except InvalidTokenError as e:
        logging.error(f"Invalid token: {str(e)}")
        raise UnauthorizedError("Invalid authentication token")
    
    except Exception as e:
        logging.error(f"Authentication error: {str(e)}")
        raise UnauthorizedError("Authentication failed")


def get_auth_secret_key() -> str:
    """
    Get the secret key for JWT signing/validation.
    
    Priority order:
    1. Azure Key Vault secret (production)
    2. Environment variable (development/staging)
    3. Fallback error (prevents accidental deployment with insecure config)
    
    TODO: Production hardening required:
    - Implement Azure Key Vault integration for production
    - Add secret rotation mechanism
    - Implement key versioning for zero-downtime rotation
    - Add monitoring/alerting for secret access failures
    """
    import os
    
    # Try Azure Key Vault first (production)
    # TODO: Uncomment and configure for production
    # try:
    #     from azure.keyvault.secrets import SecretClient
    #     from azure.identity import DefaultAzureCredential
    #     key_vault_url = os.environ.get('AZURE_KEY_VAULT_URL')
    #     if key_vault_url:
    #         credential = DefaultAzureCredential()
    #         client = SecretClient(vault_url=key_vault_url, credential=credential)
    #         secret = client.get_secret("JWT-SECRET-KEY")
    #         return secret.value
    # except Exception as e:
    #     logging.warning(f"Failed to get secret from Key Vault: {e}")
    
    # Try environment variable (development/staging)
    secret_key = os.environ.get('JWT_SECRET_KEY')
    if secret_key:
        if len(secret_key) < 32:
            logging.warning("JWT_SECRET_KEY is too short. Use at least 32 characters for security.")
        return secret_key
    
    # Fallback: Check if we're in development mode
    is_development = os.environ.get('ENVIRONMENT', 'development').lower() == 'development'
    if is_development:
        logging.warning(
            "Using development JWT secret. Set JWT_SECRET_KEY environment variable "
            "or configure Azure Key Vault for production."
        )
        # TODO: Remove this fallback before production deployment
        return "xtotext-development-secret-key-change-in-production"
    
    # Production: Fail securely if no secret configured
    raise ValueError(
        "JWT_SECRET_KEY not configured. Set JWT_SECRET_KEY environment variable "
        "or configure Azure Key Vault (AZURE_KEY_VAULT_URL)."
    )


async def check_document_permission(
    user_id: str, 
    document_id: str, 
    required_action: str
) -> bool:
    """
    Check if a user has permission to perform an action on a document.
    
    Args:
        user_id: The user ID
        document_id: The document ID
        required_action: The action to check ("read", "write", "delete", "share")
        
    Returns:
        True if the user has permission, False otherwise
    """
    try:
        # Get document from database
        db = await get_database()
        doc = await db.documents.find_one({"id": document_id})
        
        if not doc:
            logging.warning(f"Document {document_id} not found during permission check")
            return False
        
        # Convert to Document model for easier access
        document = Document(**doc)
        
        # Check if user is the owner
        if document.uploaded_by == user_id:
            return True
        
        # Check explicit permissions
        user_permissions = document.permissions.get(user_id, [])
        if required_action in user_permissions:
            return True
        
        # Check for admin role (has access to all documents)
        user_data = await db.users.find_one({"id": user_id})
        if user_data and "admin" in user_data.get("roles", []):
            return True
        
        return False
    
    except Exception as e:
        logging.error(f"Error checking document permission: {str(e)}")
        return False


async def check_permission_or_raise(
    user_id: str,
    document_id: str,
    required_action: str
) -> None:
    """
    Check document permission and raise error if not allowed.
    
    Args:
        user_id: The user ID
        document_id: The document ID
        required_action: The action to check
        
    Raises:
        ForbiddenError: If the user doesn't have permission
    """
    has_permission = await check_document_permission(user_id, document_id, required_action)
    
    if not has_permission:
        raise ForbiddenError(
            f"User {user_id} doesn't have {required_action} permission for document {document_id}"
        )