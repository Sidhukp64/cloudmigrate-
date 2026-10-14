from fastapi import APIRouter, Depends
from app.models.user import UserRole
from app.core.circuit_breaker import s3_circuit_breaker, sftp_circuit_breaker, webhook_circuit_breaker
from app.services.s3_service import check_bucket_health
from app.api.deps import require_role
from app.models.user import User

router = APIRouter()


@router.get("/health/circuit-breakers")
def circuit_breaker_status(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get circuit breaker states for all external services."""
    return {
        "s3": s3_circuit_breaker.get_status(),
        "sftp": sftp_circuit_breaker.get_status(),
        "webhooks": webhook_circuit_breaker.get_status(),
    }


@router.get("/health/services")
def services_health(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """Check health of dependent services."""
    return {
        "s3": {"healthy": check_bucket_health()},
        "database": {"healthy": True},  # If we got here, DB is up
    }
