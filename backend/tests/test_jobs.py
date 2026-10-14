import pytest
from fastapi import status


JOB_PAYLOAD = {
    "name": "Test SFTP Sync",
    "description": "Test sync job",
    "source_type": "sftp",
    "destination_type": "s3",
    "source_config": {"path": "/uploads"},
    "destination_config": {"prefix": "test/"},
    "transform": "none",
    "max_retries": 2,
    "retry_delay_seconds": 30,
}


class TestSyncJobs:
    def test_create_job_as_operator(self, client, operator_token):
        response = client.post(
            "/api/v1/jobs",
            json=JOB_PAYLOAD,
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == JOB_PAYLOAD["name"]
        assert data["source_type"] == "sftp"
        assert "id" in data

    def test_create_job_as_viewer_forbidden(self, client, db):
        from app.core.security import create_access_token, get_password_hash
        from app.models.user import User, UserRole
        viewer = User(
            email="viewer@cloudmigrate.io",
            full_name="Viewer",
            hashed_password=get_password_hash("ViewerPass!"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        db.add(viewer)
        db.commit()
        viewer_token = create_access_token({"sub": str(viewer.id), "role": viewer.role.value})
        response = client.post(
            "/api/v1/jobs",
            json=JOB_PAYLOAD,
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_jobs(self, client, operator_token):
        response = client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {operator_token}"})
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_job_not_found(self, client, operator_token):
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/jobs/{fake_id}", headers={"Authorization": f"Bearer {operator_token}"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
