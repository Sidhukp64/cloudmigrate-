"""
SFTP service: connect to legacy SFTP servers and stream files for migration.
"""
import io
import logging
import stat
from typing import List, Optional
from pathlib import PurePosixPath
import paramiko
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.core.circuit_breaker import sftp_circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class SFTPClient:
    """Context manager for SFTP connections."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_path: Optional[str] = None,
    ):
        self.host = host or settings.SFTP_HOST
        self.port = port or settings.SFTP_PORT
        self.username = username or settings.SFTP_USER
        self.password = password or settings.SFTP_PASSWORD
        self.private_key_path = private_key_path or settings.SFTP_PRIVATE_KEY_PATH
        self._transport = None
        self._sftp = None

    def connect(self):
        self._transport = paramiko.Transport((self.host, self.port))
        if self.private_key_path:
            key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
            self._transport.connect(username=self.username, pkey=key)
        else:
            self._transport.connect(username=self.username, password=self.password)
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        logger.info(f"Connected to SFTP {self.host}:{self.port}")
        return self

    def disconnect(self):
        if self._sftp:
            self._sftp.close()
        if self._transport:
            self._transport.close()
        logger.info("SFTP connection closed")

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.disconnect()

    def list_files(self, remote_path: str, recursive: bool = False) -> List[dict]:
        """List files at a remote SFTP path."""
        results = []
        attrs = self._sftp.listdir_attr(remote_path)
        for attr in attrs:
            full_path = str(PurePosixPath(remote_path) / attr.filename)
            if stat.S_ISDIR(attr.st_mode) and recursive:
                results.extend(self.list_files(full_path, recursive=True))
            elif stat.S_ISREG(attr.st_mode):
                results.append({
                    "path": full_path,
                    "filename": attr.filename,
                    "size_bytes": attr.st_size,
                    "modified_at": attr.st_mtime,
                })
        return results

    def read_file(self, remote_path: str) -> bytes:
        """Read a remote file into memory."""
        with self._sftp.open(remote_path, "rb") as f:
            return f.read()

    def read_file_obj(self, remote_path: str) -> io.BytesIO:
        """Stream a remote file as BytesIO."""
        data = self.read_file(remote_path)
        return io.BytesIO(data)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=5, max=60), reraise=True)
def list_sftp_files(remote_path: str, recursive: bool = False) -> List[dict]:
    """List SFTP files with retry + circuit breaker."""
    def _do():
        with SFTPClient() as sftp:
            return sftp.list_files(remote_path, recursive)
    try:
        return sftp_circuit_breaker.call(_do)
    except CircuitBreakerOpenError as e:
        logger.error(f"SFTP circuit breaker is OPEN: {e}")
        raise
