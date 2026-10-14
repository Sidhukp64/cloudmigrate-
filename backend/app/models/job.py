import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, Enum as SAEnum, ForeignKey, Float, Text
from app.core.guid import GUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class SourceType(str, enum.Enum):
    SFTP = "sftp"
    POSTGRESQL = "postgresql"
    LOCAL_FS = "local_fs"


class DestinationType(str, enum.Enum):
    S3 = "s3"


class TransformType(str, enum.Enum):
    NONE = "none"
    CSV_TO_PARQUET = "csv_to_parquet"
    JSON_NORMALIZE = "json_normalize"
    PII_MASK = "pii_mask"


class JobStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(SAEnum(SourceType), nullable=False)
    destination_type = Column(SAEnum(DestinationType), nullable=False, default=DestinationType.S3)
    source_config = Column(JSON, nullable=False, default=dict)   # SFTP path, PG query, etc.
    destination_config = Column(JSON, nullable=False, default=dict)  # S3 prefix, bucket
    transform = Column(SAEnum(TransformType), nullable=False, default=TransformType.NONE)
    transform_config = Column(JSON, nullable=True, default=dict)
    schedule_cron = Column(String(100), nullable=True)            # "0 2 * * *" = 2 AM daily
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    status = Column(SAEnum(JobStatus), default=JobStatus.ACTIVE, nullable=False)
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    runs = relationship("JobRun", back_populates="job", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("sync_jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(SAEnum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)
    attempt_number = Column(Integer, default=1)
    files_processed = Column(Integer, default=0)
    bytes_transferred = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    triggered_by = Column(String(50), default="scheduler")  # scheduler | manual | api
    celery_task_id = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job = relationship("SyncJob", back_populates="runs")
