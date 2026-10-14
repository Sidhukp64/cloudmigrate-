from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.job import SyncJob, JobRun, RunStatus, JobStatus
from app.models.audit import AuditAction
from app.schemas.job import SyncJobCreate, SyncJobUpdate, SyncJobOut, JobRunOut
from app.services.audit_service import log_event
from app.api.deps import get_current_user, require_role
from app.workers.sync_worker import run_sync_job_task

router = APIRouter()


@router.get("", response_model=List[SyncJobOut])
def list_jobs(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all sync jobs with optional status filter."""
    q = db.query(SyncJob)
    if status_filter:
        q = q.filter(SyncJob.status == status_filter)
    jobs = q.order_by(SyncJob.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for job in jobs:
        job_out = SyncJobOut.model_validate(job)
        # Attach last run
        last_run = (
            db.query(JobRun)
            .filter(JobRun.job_id == job.id)
            .order_by(JobRun.created_at.desc())
            .first()
        )
        if last_run:
            job_out.last_run = JobRunOut.model_validate(last_run)
        result.append(job_out)
    return result


@router.post("", response_model=SyncJobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: SyncJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR)),
):
    """Create a new sync job. Operator/Admin only."""
    job = SyncJob(**payload.model_dump(), created_by=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    log_event(
        db=db, action=AuditAction.JOB_CREATED,
        actor_id=current_user.id, actor_email=current_user.email,
        resource_type="job", resource_id=str(job.id),
        details={"name": job.name, "source_type": job.source_type.value},
    )
    return SyncJobOut.model_validate(job)


@router.get("/{job_id}", response_model=SyncJobOut)
def get_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a sync job by ID."""
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return SyncJobOut.model_validate(job)


@router.put("/{job_id}", response_model=SyncJobOut)
def update_job(
    job_id: UUID,
    payload: SyncJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR)),
):
    """Update a sync job configuration."""
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    log_event(
        db=db, action=AuditAction.JOB_UPDATED,
        actor_id=current_user.id, actor_email=current_user.email,
        resource_type="job", resource_id=str(job.id),
        details={"updated_fields": list(update_data.keys())},
    )
    return SyncJobOut.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Delete a sync job. Admin only."""
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    log_event(
        db=db, action=AuditAction.JOB_DELETED,
        actor_id=current_user.id, actor_email=current_user.email,
        resource_type="job", resource_id=str(job_id),
        details={"name": job.name},
    )
    db.delete(job)
    db.commit()


@router.post("/{job_id}/run", response_model=JobRunOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR)),
):
    """Manually trigger a sync job run."""
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not active")

    run = JobRun(job_id=job.id, triggered_by="manual", status=RunStatus.PENDING)
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch to Celery if available, or fall back to FastAPI BackgroundTasks for local demo
    try:
        task = run_sync_job_task.delay(str(job.id), str(run.id))
        run.celery_task_id = task.id
    except Exception:
        # Local fallback execution without Celery/Redis broker running
        def _run_local(j_id: str, r_id: str):
            try:
                from app.workers.sync_worker import run_sync_job_task
                run_sync_job_task(j_id, r_id)
            except Exception:
                pass
        background_tasks.add_task(_run_local, str(job.id), str(run.id))
        run.celery_task_id = "local-background-task"
    db.commit()

    return JobRunOut.model_validate(run)


@router.get("/{job_id}/runs", response_model=List[JobRunOut])
def get_job_runs(
    job_id: UUID,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get run history for a job."""
    job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    runs = (
        db.query(JobRun)
        .filter(JobRun.job_id == job_id)
        .order_by(JobRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [JobRunOut.model_validate(r) for r in runs]
