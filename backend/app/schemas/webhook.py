from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from app.models.webhook import WebhookEvent, DeliveryStatus


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str] = [WebhookEvent.ALL]
    headers: Optional[Dict[str, str]] = {}
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class WebhookDeliveryOut(BaseModel):
    id: UUID
    endpoint_id: UUID
    event_type: str
    status: DeliveryStatus
    http_status_code: Optional[int]
    attempt_count: int
    delivered_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookOut(BaseModel):
    id: UUID
    name: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
