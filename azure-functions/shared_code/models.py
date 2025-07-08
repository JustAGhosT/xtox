"""
Data models for the xtotext application.
This module contains Pydantic models used across the application.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AIConversionOptions(BaseModel):
    """Options for AI text conversion"""
    
    target_model: str = "gpt-4"
    preserve_structure: bool = True
    include_metadata: bool = True
    max_tokens: Optional[int] = None
    output_format: str = "standard"  # "standard", "markdown", "plain"
    chunking_strategy: str = "semantic"  # "semantic", "token", "simple"


class AIConversionResult(BaseModel):
    """Result of AI text conversion"""
    
    id: str
    document_id: str
    filename: str
    content_type: str
    ai_text: Optional[str] = None
    chunks: List[str] = []
    token_count: int = 0
    model_target: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override dict method to handle datetime serialization"""
        d = super().dict(**kwargs)
        # Convert datetime to ISO format string for JSON serialization
        if "timestamp" in d and isinstance(d["timestamp"], datetime):
            d["timestamp"] = d["timestamp"].isoformat()
        return d


class Document(BaseModel):
    """Document stored in the system"""
    
    id: str
    filename: str
    content_type: str
    size: int
    storage_path: str
    storage_type: str = "azure_blob"
    uploaded_by: str
    permissions: Dict[str, List[str]] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Override dict method to handle datetime serialization"""
        d = super().dict(**kwargs)
        # Convert datetime to ISO format string for JSON serialization
        if "timestamp" in d and isinstance(d["timestamp"], datetime):
            d["timestamp"] = d["timestamp"].isoformat()
        return d


class User(BaseModel):
    """User in the system"""
    
    id: str
    email: str
    name: str
    roles: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    settings: Dict[str, Any] = {}


class Permission(BaseModel):
    """Permission for a resource"""
    
    resource_id: str
    resource_type: str  # "document", "folder", "project"
    user_id: str
    actions: List[str]  # "read", "write", "delete", "share"
    granted_by: str
    granted_at: datetime = Field(default_factory=datetime.utcnow)