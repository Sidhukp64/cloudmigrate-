# ☁️ CloudMigrate — Enterprise Multi-Cloud File & Data Synchronization Gateway

> An enterprise-grade, microservice-based data migration and synchronization gateway built in **Python (FastAPI)**, designed to safely route, transform, and sync large batches of structured files and transactional data between legacy systems and modern cloud storage (AWS S3).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CloudMigrate Platform                        │
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────────────────┐  │
│  │  React UI   │   │  FastAPI    │   │   Background Workers     │  │
│  │  Dashboard  │──▶│  Gateway    │──▶│   (Celery + Redis)       │  │
│  │  (Port 3000)│   │  (Port 8000)│   │                          │  │
│  └─────────────┘   └─────────────┘   └──────────────────────────┘  │
│                          │                        │                 │
│                    ┌─────┴──────┐         ┌──────┴──────┐          │
│                    │ PostgreSQL  │         │  AWS S3 /   │          │
│                    │  (Audit DB) │         │  SFTP       │          │
│                    └────────────┘         └─────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Core Features

| Feature | Description |
|---|---|
| **Sync Jobs** | Create, schedule, and manage file sync jobs between SFTP → S3 and PG → S3 |
| **Retry Engine** | Exponential backoff with configurable max retries & circuit breakers |
| **Audit Logging** | Full immutable audit trail for every file operation with tamper detection |
| **Webhooks** | Push notifications to external endpoints on job completion/failure |
| **RBAC** | Role-based access control (Admin, Operator, Viewer) |
| **Transforms** | CSV→Parquet, JSON normalization, PII masking before upload |
| **Dashboard** | Real-time React dashboard for monitoring jobs, logs, and webhooks |

## 📦 Project Structure

```
cloudmigrate/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (jobs, auth, webhooks, audit)
│   │   ├── core/          # Config, security, database, circuit breaker
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic (sync engine, S3, SFTP, transform)
│   │   ├── workers/       # Celery background tasks
│   │   └── main.py        # FastAPI app entrypoint
│   ├── alembic/           # DB migrations
│   ├── tests/             # pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Dashboard, Jobs, Audit, Webhooks
│   │   ├── hooks/         # Custom React hooks
│   │   ├── api/           # Axios API client
│   │   └── App.tsx
│   └── package.json
└── docker-compose.yml     # Full stack orchestration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- AWS credentials (or LocalStack for local dev)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd cloudmigrate
cp backend/.env.example backend/.env
# Fill in your AWS credentials and DB URL
```

### 2. Start with Docker Compose

```bash
docker-compose up -d
```

This spins up:
- **FastAPI** backend on `http://localhost:8000`
- **React** dashboard on `http://localhost:3000`
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **Celery** workers

### 3. API Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 🔑 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | Get JWT token |
| POST | `/api/v1/auth/register` | Register user (admin only) |
| GET | `/api/v1/auth/me` | Current user info |

### Sync Jobs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/jobs` | List all sync jobs |
| POST | `/api/v1/jobs` | Create new sync job |
| GET | `/api/v1/jobs/{id}` | Get job details |
| PUT | `/api/v1/jobs/{id}` | Update job config |
| DELETE | `/api/v1/jobs/{id}` | Delete job |
| POST | `/api/v1/jobs/{id}/run` | Trigger manual run |
| GET | `/api/v1/jobs/{id}/runs` | Job run history |

### Audit Logs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/audit` | Query audit logs |
| GET | `/api/v1/audit/{id}` | Single audit event |
| GET | `/api/v1/audit/export` | Export logs as CSV |

### Webhooks
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/webhooks` | List webhook endpoints |
| POST | `/api/v1/webhooks` | Register webhook |
| DELETE | `/api/v1/webhooks/{id}` | Remove webhook |
| GET | `/api/v1/webhooks/{id}/deliveries` | Delivery history |

---

## 🏢 TCS/Wipro Enterprise Context

This project mirrors real enterprise engagement patterns:

- **Managed File Transfer (MFT)**: SFTP → Cloud pipelines are standard in banking, insurance, and healthcare clients
- **Data Lake Ingestion**: PostgreSQL → S3 (Parquet) is the classic "lift-and-shift analytics" pattern
- **Audit & Compliance**: SOX, HIPAA, GDPR require immutable audit trails — this is built-in
- **Webhook Notifications**: Integrates with ServiceNow, Jira, Slack for enterprise ITSM workflows
- **Circuit Breakers**: Resilience4j pattern translated to Python — common in Java enterprise shops

---

## 📄 License
MIT
