"""
Webhook delivery service with HMAC signing and retry logic.
"""
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.circuit_breaker import webhook_circuit_breaker, CircuitBreakerOpenError
from app.models.webhook import WebhookEndpoint, WebhookDelivery, DeliveryStatus
from app.models.audit import AuditAction

logger = logging.getLogger(__name__)


def _sign_payload(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def dispatch_event(
    db: Session,
    event_type: str,
    payload: dict,
    job_id: Optional[str] = None,
):
    """Find matching webhook endpoints and dispatch events."""
    endpoints = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.is_active == True
    ).all()

    for endpoint in endpoints:
        events = endpoint.events or []
        if "*" in events or event_type in events:
            _deliver_to_endpoint(db, endpoint, event_type, payload)


def _deliver_to_endpoint(
    db: Session,
    endpoint: WebhookEndpoint,
    event_type: str,
    payload: dict,
    attempt: int = 1,
):
    """Attempt webhook delivery with HMAC signature."""
    delivery = WebhookDelivery(
        endpoint_id=endpoint.id,
        event_type=event_type,
        payload=payload,
        status=DeliveryStatus.PENDING,
        attempt_count=attempt,
    )
    db.add(delivery)
    db.flush()

    payload_str = json.dumps(payload, default=str)
    headers = {
        "Content-Type": "application/json",
        "X-CloudMigrate-Event": event_type,
        "X-CloudMigrate-Delivery": str(delivery.id),
        **(endpoint.headers or {}),
    }

    if endpoint.secret:
        sig = _sign_payload(payload_str, endpoint.secret)
        headers["X-CloudMigrate-Signature"] = f"sha256={sig}"

    def _do_request():
        with httpx.Client(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
            return client.post(endpoint.url, content=payload_str, headers=headers)

    try:
        response = webhook_circuit_breaker.call(_do_request)
        delivery.status = DeliveryStatus.SUCCESS
        delivery.http_status_code = response.status_code
        delivery.response_body = response.text[:2000]
        delivery.delivered_at = datetime.now(timezone.utc)
        logger.info(f"Webhook delivered to {endpoint.url} — HTTP {response.status_code}")
    except (httpx.RequestError, CircuitBreakerOpenError) as exc:
        delivery.status = DeliveryStatus.FAILED
        delivery.response_body = str(exc)[:2000]
        logger.error(f"Webhook delivery failed to {endpoint.url}: {exc}")
    finally:
        db.commit()
        db.refresh(delivery)

    return delivery
