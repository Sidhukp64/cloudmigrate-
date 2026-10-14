import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Enum as SAEnum, Text, Integer, ForeignKey
from app.core.guid import GUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class WebhookEvent(str, enum.Enum):
    JOB_RUN_STARTED = "job.run.started"
    JOB_RUN_COMPLETED = "job.run.completed"
    JOB_RUN_FAILED = "job.run.failed"
    ALL = "*"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    secret = Column(String(255), nullable=True)          # HMAC signing secret
    events = Column(JSON, nullable=False, default=list)  # List of WebhookEvent values
    is_active = Column(Boolean, default=True)
    headers = Column(JSON, nullable=True, default=dict)  # Custom headers
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    endpoint_id = Column(GUID(), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(SAEnum(DeliveryStatus), default=DeliveryStatus.PENDING)
    http_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=0)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")
