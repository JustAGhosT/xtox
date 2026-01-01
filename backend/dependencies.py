"""
Dependency injection functions for FastAPI routes.

Provides reusable dependencies for database access, authentication, etc.
This promotes separation of concerns and makes testing easier.

TODO: Production enhancements:
- Add authentication dependency
- Add authorization dependency
- Add request context dependencies
- Add rate limiting dependencies
"""

from typing import Generator

from fastapi import Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from database import Database


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency function to get database instance.
    
    Uses FastAPI's dependency injection system to provide database
    access to route handlers. This makes testing easier and promotes
    separation of concerns.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
    
    Raises:
        HTTPException: If database is not connected
    """
    try:
        db = Database.get_db()
        return db
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable"
        ) from e


# Type alias for dependency injection
DatabaseDep = Depends(get_database)

