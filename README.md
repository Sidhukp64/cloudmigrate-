# ☁️ CloudMigrate — Enterprise Multi-Cloud File & Data Synchronization Gateway

> An enterprise-grade, microservice-based data migration and synchronization gateway built in **Python (FastAPI)** and **React (TypeScript)**, designed to safely route, transform, and sync large batches of structured files and transactional data between legacy systems (SFTP, on-prem PostgreSQL) and modern cloud storage (AWS S3).

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CloudMigrate Platform                          │
│                                                                        │
│   ┌──────────────┐      ┌──────────────┐      ┌────────────────────┐   │
│   │   React UI   │      │   FastAPI    │      │ Background Workers │   │
│   │  Dashboard   │─────▶│   Gateway    │─────▶│  (Celery + Redis)  │   │
│   │ (Port 3000)  │      │ (Port 8000)  │      │                    │   │
│   └──────────────┘      └──────────────┘      └────────────────────┘   │
│                                │                         │             │
│                         ┌──────┴──────┐           ┌──────┴──────┐      │
│                         │ SQLite/PG   │           │  AWS S3 /   │      │
│                         │ (Audit DB)  │           │  SFTP       │      │
│                         └─────────────┘           └─────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Core Features

| Feature | Description |
|---|---|
| **Sync Jobs Engine** | Automated routing and synchronization between legacy sources (SFTP, PostgreSQL) and AWS S3. |
| **Resilience & Circuit Breakers** | Thread-safe 3-state circuit breaker pattern (`CLOSED` → `OPEN` → `HALF_OPEN`) with Tenacity retry policies for network dropouts. |
| **Security & Compliance** | Immutable audit logs secured with cryptographic **SHA-256 tamper-detection checksums** and CSV compliance export. |
| **RBAC Authentication** | Multi-tier Role-Based Access Control (`Admin`, `Operator`, `Viewer`) with JWT bearer tokens. |
| **Data Transformation Pipeline** | On-the-fly CSV to Parquet conversion via Apache Arrow, JSON normalization, and automated PII masking. |
| **Webhook Delivery** | HMAC-SHA256 signed event notifications (`X-CloudMigrate-Signature`) for job lifecycle tracking. |
| **Modern React Dashboard** | Real-time monitoring interface with Tailwind CSS, Lucide icons, and TanStack React Query. |

---

## 📦 Project Structure

```
cloudmigrate/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (jobs, auth, audit, webhooks, admin)
│   │   ├── core/          # Config, security, database, circuit breakers
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   ├── services/      # S3 client, SFTP streaming, transform engine, webhooks
│   │   ├── workers/       # Celery task definitions
│   │   └── main.py        # Application entrypoint & middleware
│   ├── alembic/           # Database migration configuration
│   ├── tests/             # pytest suite (auth, jobs, circuit breaker, audit)
│   ├── seed_demo.py       # Seed script for initial users & demo jobs
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios HTTP client & API endpoints
│   │   ├── components/    # Reusable Layout, Badges, Stat Cards
│   │   ├── pages/         # Dashboard, Jobs, Audit Trail, Webhooks, Login
│   │   ├── store/         # Zustand auth store with localStorage persistence
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml     # Multi-container orchestration
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (with npm)
- *(Optional)* **Docker & Docker Compose**

---

### Option 1: Run with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sidhukp64/cloudmigrate-.git
   cd cloudmigrate-
   ```

2. **Configure environment:**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Start the stack:**
   ```bash
   docker-compose up --build
   ```

* **Frontend**: `http://localhost:3000`
* **Backend API Docs**: `http://localhost:8000/docs`
* **Flower Celery Monitor**: `http://localhost:5555`

---

### Option 2: Run Locally (Without Docker)

#### Step 1: Start the Backend

```bash
cd backend

# Create .env from template
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/Mac

# Install Python requirements
pip install -r requirements.txt

# Seed demo users & sample data
python seed_demo.py

# Run the FastAPI server
python -m uvicorn app.main:app --reload --port 8000
```

Backend will be running at **`http://localhost:8000`** (Swagger docs at **`http://localhost:8000/docs`**).

#### Step 2: Start the Frontend

Open a **separate terminal window**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev -- --port 3000
```

Frontend will be running at **`http://localhost:3000`**.

---

## 🔑 Demo Credentials

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin@cloudmigrate.io` | `Admin123!` | Full control, audit export, delete jobs, register users |
| **Operator** | `operator@cloudmigrate.io` | `Operator123!` | Create & trigger sync jobs, configure webhooks |

---

## 🔌 API Endpoints Summary

### Authentication (`/api/v1/auth`)
* `POST /login` — Authenticate and receive JWT access token
* `POST /register` — Register a new user (`Admin` only)
* `GET /me` — Current user profile and assigned role

### Sync Jobs (`/api/v1/jobs`)
* `GET /` — List sync jobs with execution status
* `POST /` — Create a new sync job (`Operator` or `Admin`)
* `GET /{id}` — Job details and historical run logs
* `PUT /{id}` — Update job configuration or schedule
* `DELETE /{id}` — Delete sync job (`Admin` only)
* `POST /{id}/run` — Trigger manual execution
* `GET /{id}/runs` — Get run execution history

### Audit Logs (`/api/v1/audit`)
* `GET /` — Filterable audit logs with tamper checksums
* `GET /{id}` — Single log entry with cryptographic verification
* `GET /export` — Export audit trail to CSV (`Admin` only)

### Webhooks (`/api/v1/webhooks`)
* `GET /` — List configured webhook destinations
* `POST /` — Register a webhook endpoint with HMAC secret
* `DELETE /{id}` — Delete webhook endpoint
* `GET /{id}/deliveries` — Inspect past delivery attempts and HTTP response codes

---

## 🏢 Enterprise Relevance (TCS / Wipro Profile Context)

This project reflects the core patterns found in enterprise IT modernization contracts:

- **Managed File Transfer (MFT)**: Migrating legacy on-premise SFTP/FTP data feeds to cloud-native object stores (S3).
- **Data Lakehouse Ingestion**: Ingesting legacy relational databases directly into columnar Parquet formats for big data query engines (Snowflake / AWS Athena).
- **Auditability & Compliance**: Immutable audit trails meeting strict SOX, HIPAA, and GDPR standards.
- **Circuit Breakers & High Availability**: Fault tolerance against third-party network hiccups using Circuit Breaker state machines.

---

## 📄 License
MIT License.
