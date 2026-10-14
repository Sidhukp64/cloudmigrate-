import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Enum as SAEnum, Text, ForeignKey
from app.core.guid import GUID
from app.core.database import Base


class AuditAction(str, enum.Enum):
    JOB_CREATED = "JOB_CREATED"
    JOB_UPDATED = "JOB_UPDATED"
    JOB_DELETED = "JOB_DELETED"
    JOB_RUN_STARTED = "JOB_RUN_STARTED"
    JOB_RUN_COMPLETED = "JOB_RUN_COMPLETED"
    JOB_RUN_FAILED = "JOB_RUN_FAILED"
    FILE_UPLOADED = "FILE_UPLOADED"
    FILE_TRANSFORMED = "FILE_TRANSFORMED"
    USER_LOGIN = "USER_LOGIN"
    USER_CREATED = "USER_CREATED"
    WEBHOOK_FIRED = "WEBHOOK_FIRED"
    WEBHOOK_FAILED = "WEBHOOK_FAILED"
    CONFIG_CHANGED = "CONFIG_CHANGED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    action = Column(SAEnum(AuditAction), nullable=False, index=True)
    actor_id = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)  # Denormalized for retention
    resource_type = Column(String(100), nullable=True)   # job, user, webhook
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True, default=dict)  # What changed
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)          # SHA-256 tamper detection
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} actor={self.actor_email}>"
