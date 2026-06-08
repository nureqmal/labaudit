# 🔬 LabAudit

**Laboratory Audit Readiness Platform**
> *Know your audit readiness in 30 seconds.*

LabAudit is a production-ready SaaS web application for Quality Managers, Compliance Officers and Laboratory Managers in food testing, environmental, pharmaceutical and industrial R&D laboratories.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Audit Readiness Score** | Weighted 0–100% score across 4 compliance pillars |
| **Document Management** | SOPs, policies, calibration certs — upload PDF/DOCX/XLSX |
| **Calibration Tracking** | Equipment schedule with overdue/due-soon alerts |
| **Training Records** | Staff competency tracking with expiry reminders |
| **CAPA Register** | Raise, assign and close corrective/preventive actions |
| **Audit View** | Green / Yellow / Red compliance map per department |
| **Role-Based Access** | Admin · Manager · Viewer |
| **Audit Trail** | Immutable log of every action |
| **Demo Data** | Realistic Malaysian lab data seeded automatically |

---

## 🚀 Quick Start (Docker — recommended)

### Prerequisites
- Docker Desktop installed and running
- Git

### 1. Clone and configure
```bash
git clone <your-repo-url>
cd labaudit
cp .env.example .env
# Edit .env if needed — defaults work out of the box
```

### 2. Start the stack
```bash
docker compose up --build
```

### 3. Open the app
```
http://localhost:8501
```

### 4. Login with demo credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | admin@nexusfood.com.my | Admin@1234 |
| **Manager** | quality.manager@nexusfood.com.my | Manager@1234 |
| **Manager** | compliance@nexusfood.com.my | Manager@1234 |
| **Viewer** | lab.microbio@nexusfood.com.my | Viewer@1234 |
| **Viewer** | lab.chem@nexusfood.com.my | Viewer@1234 |

---

## 🛠️ Local Development (without Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ running locally

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — change DATABASE_URL to point to your local postgres:
# DATABASE_URL=postgresql://youruser:yourpass@localhost:5432/labaudit_db
```

### Create the database
```bash
# In psql or pgAdmin:
CREATE DATABASE labaudit_db;
CREATE USER labaudit WITH PASSWORD 'labaudit_pass';
GRANT ALL PRIVILEGES ON DATABASE labaudit_db TO labaudit;
```

### Run the app
```bash
streamlit run Home.py
```

The app will auto-create tables and seed demo data on first run.

---

## 📁 Project Structure

```
labaudit/
├── Home.py                     # Entry point — auth gate + startup
├── pages/
│   ├── 1_Dashboard.py          # Audit score + KPI overview
│   ├── 2_Documents.py          # Document management + upload
│   ├── 3_Calibration.py        # Equipment calibration schedule
│   ├── 4_Training.py           # Staff training records
│   ├── 5_CAPA.py               # CAPA register
│   ├── 6_Audit_View.py         # Green/Yellow/Red compliance map
│   └── 7_Admin.py              # User management + audit trail
├── components/
│   ├── auth_guard.py           # Login page + session management
│   ├── sidebar.py              # Navigation sidebar
│   ├── score_card.py           # Gauge chart + pillar cards
│   ├── status_badge.py         # Coloured status badges
│   └── ui_helpers.py           # Shared UI utilities
├── app/
│   ├── config.py               # Settings via pydantic-settings
│   ├── database.py             # SQLAlchemy engine + sessions
│   ├── models/                 # SQLAlchemy ORM models (7 tables)
│   ├── repositories/           # DB access layer
│   ├── services/               # Business logic layer
│   └── utils/                  # Security, file handling, seed, logging
├── alembic/                    # DB migrations
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🧮 Audit Score Formula

```
Score = (Documents × 35%) + (Calibrations × 30%) + (Training × 20%) + (CAPA × 15%)
```

| Score | Status |
|---|---|
| 90–100% | ✅ Audit Ready |
| 70–89% | ⚠️ Minor Gaps |
| 50–69% | 🟠 Moderate Risk |
| 0–49% | 🚨 Critical Risk |

Penalties applied for:
- Expiring-soon documents (−up to 10pts per pillar)
- Overdue CAPAs (−5pts each, max −25)
- Critical open CAPAs (−8pts each, max −24)

---

## 🔐 Roles & Permissions

| Action | Viewer | Manager | Admin |
|---|---|---|---|
| View dashboard & reports | ✅ | ✅ | ✅ |
| Upload documents | ❌ | ✅ | ✅ |
| Add calibration records | ❌ | ✅ | ✅ |
| Add training records | ❌ | ✅ | ✅ |
| Raise & manage CAPAs | ❌ | ✅ | ✅ |
| Create users | ❌ | ❌ | ✅ |
| View audit trail | ❌ | ❌ | ✅ |

---

## 🔔 Expiry Reminder Logic

| Threshold | Alert Level |
|---|---|
| Past expiry | 🔴 Red — Overdue |
| ≤ 7 days | 🔴 Red — Critical |
| ≤ 14 days | 🟠 Orange — Urgent |
| ≤ 30 days | 🟡 Yellow — Warning |

Applies to: Documents, Calibration records, Training records, CAPA due dates.

---

## 🐳 Production Deployment

### Environment variables to change for production
```bash
APP_ENV=production
DEBUG=false
SECRET_KEY=<long-random-string-min-32-chars>
SEED_DEMO_DATA=false
```

### Generate a secure SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Stop demo data seeding
Set `SEED_DEMO_DATA=false` in `.env` before first run in production.

### Database backups
```bash
# Backup
docker exec labaudit_db pg_dump -U labaudit labaudit_db > backup.sql

# Restore
docker exec -i labaudit_db psql -U labaudit labaudit_db < backup.sql
```

### Useful Docker commands
```bash
docker compose up -d          # Start in background
docker compose down           # Stop
docker compose logs -f app    # Stream app logs
docker compose restart app    # Restart app only
docker compose ps             # Check status
```

---

## 🗄️ Database Migrations (Alembic)

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## 📝 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.35 |
| Backend / Services | Python 3.11 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Charts | Plotly |
| Config | pydantic-settings |
| Container | Docker + Docker Compose |

---

## 🧪 Demo Organisation

The seeded demo data represents **Nexus Food Analytics Sdn Bhd** — a Malaysian ISO 17025 accredited food testing laboratory with:

- 15 documents (mix of active, expiring, expired, draft)
- 12 calibration records (current, due soon, overdue)
- 15 training records (current, due soon, overdue, completed)
- 7 CAPA items (closed, in progress, open, overdue)
- 6 staff across Admin, Manager and Viewer roles

---

*Built with ❤️ for laboratory compliance teams.*
