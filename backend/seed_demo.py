"""
Seed initial demo data:
- Admin user: admin@cloudmigrate.io / Admin123!
- Operator user: operator@cloudmigrate.io / Operator123!
- Sample sync jobs (SFTP -> S3, PG -> S3)
- Sample audit log entries
"""
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.job import SyncJob, JobRun, SourceType, DestinationType, TransformType, JobStatus, RunStatus
from app.models.audit import AuditLog, AuditAction
from app.services.audit_service import _compute_checksum
from datetime import datetime, timezone, timedelta

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Create Users
        admin = db.query(User).filter(User.email == "admin@cloudmigrate.io").first()
        if not admin:
            admin = User(
                email="admin@cloudmigrate.io",
                full_name="Enterprise Admin",
                hashed_password=get_password_hash("Admin123!"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Created Admin user: admin@cloudmigrate.io")

        operator = db.query(User).filter(User.email == "operator@cloudmigrate.io").first()
        if not operator:
            operator = User(
                email="operator@cloudmigrate.io",
                full_name="Lead Migration Engineer",
                hashed_password=get_password_hash("Operator123!"),
                role=UserRole.OPERATOR,
                is_active=True,
            )
            db.add(operator)
            db.commit()
            db.refresh(operator)
            print("Created Operator user: operator@cloudmigrate.io")

        # 2. Sample Sync Jobs
        job1 = db.query(SyncJob).filter(SyncJob.name == "Daily Banking Core SFTP to S3").first()
        if not job1:
            job1 = SyncJob(
                name="Daily Banking Core SFTP to S3",
                description="Migrates end-of-day transaction settlements from core banking SFTP to AWS S3 bucket with PII masking.",
                source_type=SourceType.SFTP,
                destination_type=DestinationType.S3,
                source_config={"host": "sftp.fintech-legacy.internal", "path": "/var/data/eod_settlements", "file_pattern": "*.csv"},
                destination_config={"bucket": "cloudmigrate-data", "prefix": "banking/settlements/"},
                transform=TransformType.PII_MASK,
                schedule_cron="0 2 * * *",
                max_retries=3,
                retry_delay_seconds=60,
                status=JobStatus.ACTIVE,
                created_by=admin.id,
            )
            db.add(job1)
            db.commit()
            db.refresh(job1)

            # Sample run
            now = datetime.now(timezone.utc)
            run1 = JobRun(
                job_id=job1.id,
                status=RunStatus.SUCCESS,
                attempt_number=1,
                files_processed=142,
                bytes_transferred=84529104,
                duration_seconds=14.8,
                triggered_by="scheduler",
                started_at=now - timedelta(hours=3),
                completed_at=now - timedelta(hours=3) + timedelta(seconds=15),
            )
            db.add(run1)

        job2 = db.query(SyncJob).filter(SyncJob.name == "Customer Records Postgres to Parquet S3").first()
        if not job2:
            job2 = SyncJob(
                name="Customer Records Postgres to Parquet S3",
                description="Converts legacy Postgres transactional table into columnar Parquet format on S3 for analytics lakehouse.",
                source_type=SourceType.POSTGRESQL,
                destination_type=DestinationType.S3,
                source_config={"database_url": "postgresql://...", "query": "SELECT * FROM customers_2025"},
                destination_config={"bucket": "cloudmigrate-data", "prefix": "lakehouse/customers/"},
                transform=TransformType.CSV_TO_PARQUET,
                schedule_cron="0 4 * * 0",
                max_retries=3,
                retry_delay_seconds=120,
                status=JobStatus.ACTIVE,
                created_by=operator.id,
            )
            db.add(job2)
            db.commit()
            db.refresh(job2)

            now = datetime.now(timezone.utc)
            run2 = JobRun(
                job_id=job2.id,
                status=RunStatus.SUCCESS,
                attempt_number=1,
                files_processed=1,
                bytes_transferred=259104000,
                duration_seconds=32.4,
                triggered_by="manual",
                started_at=now - timedelta(hours=1),
                completed_at=now - timedelta(hours=1) + timedelta(seconds=33),
            )
            db.add(run2)

        # 3. Sample Audit Logs
        if db.query(AuditLog).count() == 0:
            events = [
                (AuditAction.USER_LOGIN, admin.id, admin.email, "user", str(admin.id), {"method": "password"}),
                (AuditAction.JOB_CREATED, admin.id, admin.email, "job", str(job1.id), {"name": job1.name}),
                (AuditAction.JOB_RUN_STARTED, None, "system", "job_run", "run-001", {"job_id": str(job1.id)}),
                (AuditAction.FILE_UPLOADED, None, "system", "s3_object", "banking/settlements/eod_2026.csv", {"bytes": 84529104}),
                (AuditAction.JOB_RUN_COMPLETED, None, "system", "job_run", "run-001", {"status": "SUCCESS"}),
            ]
            for action, actor_id, email, r_type, r_id, details in events:
                record = {
                    "action": action.value,
                    "actor_id": str(actor_id) if actor_id else None,
                    "actor_email": email,
                    "resource_type": r_type,
                    "resource_id": r_id,
                    "details": details,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                log = AuditLog(
                    action=action,
                    actor_id=actor_id,
                    actor_email=email,
                    resource_type=r_type,
                    resource_id=r_id,
                    details=details,
                    ip_address="127.0.0.1",
                    checksum=_compute_checksum(record),
                )
                db.add(log)
            db.commit()
            print("Sample audit logs populated!")

        print("Database seeding finished!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
