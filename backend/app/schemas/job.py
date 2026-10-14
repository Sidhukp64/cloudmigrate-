from uuid import UUID
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, field_validator
from app.models.job import SourceType, DestinationType, TransformType, JobStatus, RunStatus


class SyncJobCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: SourceType
    destination_type: DestinationType = DestinationType.S3
    source_config: Dict[str, Any] = {}
    destination_config: Dict[str, Any] = {}
    transform: TransformType = TransformType.NONE
    transform_config: Optional[Dict[str, Any]] = {}
    schedule_cron: Optional[str] = None
    max_retries: int = 3
    retry_delay_seconds: int = 60

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Job name cannot be empty")
        return v.strip()


class SyncJobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_config: Optional[Dict[str, Any]] = None
    destination_config: Optional[Dict[str, Any]] = None
    transform: Optional[TransformType] = None
    transform_config: Optional[Dict[str, Any]] = None
    schedule_cron: Optional[str] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    status: Optional[JobStatus] = None


class JobRunOut(BaseModel):
    id: UUID
    job_id: UUID
    status: RunStatus
    attempt_number: int
    files_processed: int
    bytes_transferred: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    triggered_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncJobOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    source_type: SourceType
    destination_type: DestinationType
    source_config: Dict[str, Any]
    destination_config: Dict[str, Any]
    transform: TransformType
    schedule_cron: Optional[str]
    max_retries: int
    retry_delay_seconds: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    last_run: Optional[JobRunOut] = None

    model_config = {"from_attributes": True}
