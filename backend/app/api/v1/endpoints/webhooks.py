from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookOut, WebhookDeliveryOut
from app.api.deps import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=List[WebhookOut])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered webhook endpoints."""
    return db.query(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc()).all()


@router.post("", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR)),
):
    """Register a new webhook endpoint."""
    endpoint = WebhookEndpoint(**payload.model_dump(), created_by=current_user.id)
    db.add(endpoint)
    db.commit()
    db.refresh(endpoint)
    return endpoint


@router.put("/{webhook_id}", response_model=WebhookOut)
def update_webhook(
    webhook_id: UUID,
    payload: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.OPERATOR)),
):
    """Update a webhook endpoint."""
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(endpoint, field, val)
    db.commit()
    db.refresh(endpoint)
    return endpoint


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Delete a webhook endpoint. Admin only."""
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(endpoint)
    db.commit()


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryOut])
def get_deliveries(
    webhook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get delivery history for a webhook."""
    endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook not found")
    deliveries = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.endpoint_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(100)
        .all()
    )
    return [WebhookDeliveryOut.model_validate(d) for d in deliveries]
