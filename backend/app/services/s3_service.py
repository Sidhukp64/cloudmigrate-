"""
AWS S3 service with circuit breaker integration and retry logic.
"""
import io
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.circuit_breaker import s3_circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


def _get_s3_client():
    kwargs = {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
    }
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


@retry(
    retry=retry_if_exception_type((ClientError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def upload_bytes(
    data: bytes,
    s3_key: str,
    bucket: Optional[str] = None,
    content_type: str = "application/octet-stream",
    metadata: Optional[dict] = None,
) -> dict:
    """Upload bytes to S3 with retry + circuit breaker."""
    bucket = bucket or settings.AWS_S3_BUCKET

    def _do_upload():
        client = _get_s3_client()
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}
        client.put_object(Bucket=bucket, Key=s3_key, Body=data, **extra_args)
        return {"bucket": bucket, "key": s3_key, "size_bytes": len(data)}

    try:
        return s3_circuit_breaker.call(_do_upload)
    except CircuitBreakerOpenError as e:
        logger.error(f"S3 circuit breaker is OPEN: {e}")
        raise


def upload_file_obj(file_obj: io.IOBase, s3_key: str, bucket: Optional[str] = None) -> dict:
    """Stream a file-like object to S3."""
    bucket = bucket or settings.AWS_S3_BUCKET
    client = _get_s3_client()
    client.upload_fileobj(file_obj, bucket, s3_key)
    return {"bucket": bucket, "key": s3_key}


def list_objects(prefix: str = "", bucket: Optional[str] = None) -> list:
    """List objects in S3 bucket under a prefix."""
    bucket = bucket or settings.AWS_S3_BUCKET
    client = _get_s3_client()
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return response.get("Contents", [])


def generate_presigned_url(s3_key: str, expiration: int = 3600, bucket: Optional[str] = None) -> str:
    """Generate a pre-signed URL for temporary secure access."""
    bucket = bucket or settings.AWS_S3_BUCKET
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expiration,
    )


def check_bucket_health() -> bool:
    """Quick health check — verify bucket is accessible."""
    try:
        client = _get_s3_client()
        client.head_bucket(Bucket=settings.AWS_S3_BUCKET)
        return True
    except Exception:
        return False
