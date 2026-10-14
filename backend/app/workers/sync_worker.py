"""
Celery worker: executes sync jobs with retry logic, circuit breakers, and webhook dispatch.
"""
import logging
from datetime import datetime, timezone
from celery import Task
from sqlalchemy.orm import Session
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.job import SyncJob, JobRun, RunStatus, SourceType, TransformType
from app.models.audit import AuditAction
from app.services.audit_service import log_event
from app.services.s3_service import upload_bytes
from app.services.sftp_service import SFTPClient
from app.services.transform_service import apply_transform
from app.services.webhook_service import dispatch_event

logger = logging.getLogger(__name__)


class SyncTask(Task):
    """Base task with database session management."""
    abstract = True
    _db: Session = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if self._db:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=SyncTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def run_sync_job_task(self, job_id: str, run_id: str):
    """
    Main sync task: reads from source, optionally transforms, uploads to S3.
    Handles retries with exponential backoff.
    """
    db = SessionLocal()
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        run = db.query(JobRun).filter(JobRun.id == run_id).first()

        if not job or not run:
            logger.error(f"Job {job_id} or Run {run_id} not found")
            return

        # Mark as running
        run.status = RunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        log_event(
            db=db, action=AuditAction.JOB_RUN_STARTED,
            resource_type="job_run", resource_id=run_id,
            details={"job_id": job_id, "job_name": job.name, "attempt": self.request.retries + 1},
        )

        dispatch_event(db, "job.run.started", {
            "job_id": job_id, "run_id": run_id, "job_name": job.name
        })

        files_processed = 0
        bytes_transferred = 0

        if job.source_type == SourceType.SFTP:
            files_processed, bytes_transferred = _sync_sftp(job, run, db)
        elif job.source_type == SourceType.POSTGRESQL:
            files_processed, bytes_transferred = _sync_postgres(job, run, db)
        else:
            raise NotImplementedError(f"Source type {job.source_type} not yet implemented")

        # Mark success
        run.status = RunStatus.SUCCESS
        run.files_processed = files_processed
        run.bytes_transferred = bytes_transferred
        run.completed_at = datetime.now(timezone.utc)
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
        db.commit()

        log_event(
            db=db, action=AuditAction.JOB_RUN_COMPLETED,
            resource_type="job_run", resource_id=run_id,
            details={
                "files_processed": files_processed,
                "bytes_transferred": bytes_transferred,
                "duration_seconds": run.duration_seconds,
            },
        )
        dispatch_event(db, "job.run.completed", {
            "job_id": job_id, "run_id": run_id, "files_processed": files_processed,
            "bytes_transferred": bytes_transferred,
        })

    except Exception as exc:
        logger.exception(f"Sync job {job_id} / run {run_id} failed: {exc}")
        run = db.query(JobRun).filter(JobRun.id == run_id).first()
        if run:
            run.status = RunStatus.RETRYING if self.request.retries < self.max_retries else RunStatus.FAILED
            run.error_message = str(exc)[:1000]
            db.commit()

        log_event(
            db=db, action=AuditAction.JOB_RUN_FAILED,
            resource_type="job_run", resource_id=run_id,
            details={"error": str(exc), "attempt": self.request.retries + 1},
        )
        dispatch_event(db, "job.run.failed", {
            "job_id": job_id, "run_id": run_id, "error": str(exc)
        })
        raise
    finally:
        db.close()


def _sync_sftp(job: SyncJob, run: JobRun, db: Session) -> tuple[int, int]:
    """Sync files from SFTP to S3."""
    src_cfg = job.source_config
    dst_cfg = job.destination_config
    remote_path = src_cfg.get("path", "/")
    s3_prefix = dst_cfg.get("prefix", "")
    recursive = src_cfg.get("recursive", False)
    file_pattern = src_cfg.get("file_pattern", None)

    files_processed = 0
    bytes_transferred = 0

    sftp_cfg = {
        "host": src_cfg.get("host"),
        "port": src_cfg.get("port", 22),
        "username": src_cfg.get("username"),
        "password": src_cfg.get("password"),
    }

    with SFTPClient(**{k: v for k, v in sftp_cfg.items() if v}) as sftp:
        files = sftp.list_files(remote_path, recursive=recursive)
        if file_pattern:
            import fnmatch
            files = [f for f in files if fnmatch.fnmatch(f["filename"], file_pattern)]

        for file_info in files:
            data = sftp.read_file(file_info["path"])
            s3_key = f"{s3_prefix}{file_info['filename']}"
            extension_change = ""

            if job.transform != TransformType.NONE:
                data, extension_change = apply_transform(
                    data, job.transform.value, job.transform_config
                )
                if extension_change:
                    s3_key += extension_change

            upload_bytes(data, s3_key, metadata={"source": "sftp", "job_id": str(job.id)})
            files_processed += 1
            bytes_transferred += len(data)
            logger.info(f"Uploaded {file_info['path']} → s3://{s3_key}")

    return files_processed, bytes_transferred


def _sync_postgres(job: SyncJob, run: JobRun, db: Session) -> tuple[int, int]:
    """Export PostgreSQL query results to S3 as CSV or Parquet."""
    import io
    import pandas as pd
    from sqlalchemy import create_engine as pg_engine

    src_cfg = job.source_config
    dst_cfg = job.destination_config
    pg_url = src_cfg.get("database_url")
    query = src_cfg.get("query", "SELECT 1")
    s3_key = dst_cfg.get("s3_key", f"exports/{job.id}.csv")

    pg = pg_engine(pg_url)
    df = pd.read_sql(query, pg)
    pg.dispose()

    buf = io.BytesIO()
    if job.transform == TransformType.CSV_TO_PARQUET:
        df.to_parquet(buf, index=False, engine="pyarrow")
        s3_key = s3_key.replace(".csv", ".parquet")
        content_type = "application/octet-stream"
    else:
        csv_data = df.to_csv(index=False)
        buf.write(csv_data.encode())
        content_type = "text/csv"

    data = buf.getvalue()
    upload_bytes(data, s3_key, content_type=content_type, metadata={"source": "postgresql", "job_id": str(job.id)})
    logger.info(f"Exported {len(df)} rows from PostgreSQL → s3://{s3_key}")
    return 1, len(data)
