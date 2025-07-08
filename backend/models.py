from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid

# Request/Response Models
class ConversionRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    auto_fix: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversionResult(BaseModel):
    id: str
    filename: str
    success: bool
    auto_fix_applied: bool = False
    errors: List[str] = []
    warnings: List[str] = []
    pdf_path: Optional[str] = None
    fixed_content: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Document storage models
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content_type: str
    size: int
    file_path: str
    uploaded_by: Optional[str] = None
    permissions: Dict[str, List[str]] = {}  # user_id -> list of permissions
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size: int
    uploaded_by: Optional[str] = None
    timestamp: datetime
    available_permissions: List[str]

class PermissionUpdate(BaseModel):
    user_id: str
    permissions: List[str]