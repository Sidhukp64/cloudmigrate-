from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel
from app.models.audit import AuditAction


class AuditLogOut(BaseModel):
    id: UUID
    action: AuditAction
    actor_id: Optional[UUID]
    actor_email: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    checksum: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditQueryParams(BaseModel):
    action: Optional[AuditAction] = None
    actor_email: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
