from fastapi import APIRouter
from app.api.v1.endpoints import auth, jobs, audit, webhooks, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Sync Jobs"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
