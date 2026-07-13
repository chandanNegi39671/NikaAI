<div align="center">

# NIKA AI
### Industrial Defect Detection & Quality Intelligence Platform

[![AMD AI Hackathon](https://img.shields.io/badge/AMD%20AI%20Hackathon-Act%20II%20%C2%B7%20July%202026-ED1C24?style=flat-square&logo=amd)](https://developer.amd.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.3-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-83%25%20mAP-00FFFF?style=flat-square)](https://ultralytics.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**[Live Demo](https://nika-ai-vert.vercel.app)** · **[API Docs](https://nikaai-production.up.railway.app/docs)** · **[Model on HuggingFace](https://huggingface.co/negi3961/factory-defect-guard)**

*Demo → `admin1` / `admin123`*

</div>

---

## Overview

Nika AI is a production-grade computer vision system for real-time industrial surface defect detection. It combines a fine-tuned YOLOv8s object detection model, Monte Carlo Dropout uncertainty quantification, and an LLM-powered reasoning engine to deliver actionable quality intelligence — accessible from any smartphone.

**Why it exists:** India has 63 million MSMEs employing 110 million workers. Quality control in most of them is entirely manual. Enterprise vision systems cost $40,000–$200,000 — unreachable for 99% of small manufacturers. Nika AI's barrier to entry is a phone the worker already owns.

---

## ML System Design

### 1. Object Detection Pipeline

```
Input Image (JPEG/PNG)
        │
        ▼
┌──────────────────┐
│  Preprocessing   │  ← OpenCV resize, normalize to [0,1], BGR→RGB
│  (OpenCV + PIL)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   YOLOv8s Model  │  ← Ultralytics 8.2.50, PyTorch 2.3 backend
│  29,354 images   │  ← 7 merged industrial datasets
│   17 defect cls  │  ← crack, scratch, pit, dent, surface anomaly...
│    83% mAP       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│  MC Dropout Inference    │  ← 30 stochastic forward passes (T=30)
│  (Uncertainty Quant.)    │  ← model.train() mode during inference
│                          │  ← Epistemic uncertainty via prediction variance
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Confidence Calibration  │  ← threshold=0.25, NMS IoU=0.45
│  + Reliability Scoring   │  ← HIGH / MODERATE / LOW / UNCERTAIN
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│   LLM Reasoning Layer    │  ← Gemma 4 via Google AI API
│   (Structured Output)    │  ← Root Cause, Severity, Repairability,
│                          │    Prevention, Recommended Action
└──────────────────────────┘
```

### 2. Monte Carlo Dropout — Uncertainty Quantification

Standard neural networks produce a single point estimate with no measure of confidence reliability. MC Dropout addresses this by keeping dropout layers **active during inference** and running T=30 forward passes:

```python
# Epistemic uncertainty via MC Dropout
def mc_dropout_predict(model, image, T=30):
    model.train()  # keep dropout active
    predictions = [model(image) for _ in range(T)]
    mean = np.mean(predictions, axis=0)
    variance = np.var(predictions, axis=0)
    return mean, variance  # uncertainty = variance

# Reliability classification
if variance < 0.02:    → HIGH confidence
if variance < 0.08:    → MODERATE confidence  
if variance < 0.15:    → LOW confidence
else:                  → UNCERTAIN — flag for human review
```

This prevents the model from making confident wrong predictions — a critical safety requirement in manufacturing.

### 3. Model Training Details

| Parameter | Value |
|---|---|
| Base Architecture | YOLOv8s (Small variant) |
| Training Dataset | 29,354 images, 7 merged industrial datasets |
| Defect Classes | 17 (crack, scratch, pit, dent, inclusion, roll pit, silk spot, waist folding, crease, etc.) |
| mAP@0.5 | 83% |
| Inference Latency | ~38ms on CPU (ARM), ~12ms on GPU |
| Input Resolution | 640×640 |
| Model Registry | [HuggingFace: negi3961/factory-defect-guard](https://huggingface.co/negi3961/factory-defect-guard) |
| Framework | Ultralytics 8.2.50 + PyTorch 2.3.1 |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                           │
│   React 18 · TypeScript · Vite · Tailwind CSS · Framer Motion   │
│              Camera API · PWA-ready · Mobile-first              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS / REST
┌─────────────────────────▼───────────────────────────────────────┐
│                         API GATEWAY                             │
│   FastAPI 0.111 · Uvicorn · Gunicorn (multi-worker)             │
│   SlowAPI rate limiting · JWT RBAC · CORS · CSP headers         │
│   OpenTelemetry tracing · Prometheus metrics                    │
└──────┬──────────────┬──────────────┬──────────────┬────────────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
│  ML Service │ │   Gemma 4  │ │ Celery  │ │  Analytics  │
│  YOLOv8s   │ │  Reasoning │ │ Workers │ │  Engine     │
│  MC Dropout │ │  Engine    │ │ (async) │ │  PDF/Excel  │
└──────┬──────┘ └─────┬──────┘ └────┬────┘ └──────┬──────┘
       │              │              │              │
┌──────▼──────────────▼──────────────▼──────────────▼──────┐
│                      DATA LAYER                            │
│   PostgreSQL (Neon) · Redis (Upstash) · SQLAlchemy ORM     │
│   Alembic migrations · Connection pooling                  │
└───────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
| Component | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | 0.111.0 |
| ASGI Server | Uvicorn + Gunicorn | 0.30.1 / 22.0.0 |
| ML Framework | PyTorch | 2.3.1 |
| Object Detection | Ultralytics YOLOv8s | 8.2.50 |
| Image Processing | OpenCV Headless + Pillow | 4.10.0 / 10.4.0 |
| Data Validation | Pydantic v2 | 2.7.4 |
| ORM | SQLAlchemy | 2.0.31 |
| Migrations | Alembic | 1.13.1 |
| Database | PostgreSQL (Neon serverless) | 16 |
| Cache / Broker | Redis (Upstash, TLS) | 5.0.4 |
| Task Queue | Celery | 5.3.6 |
| Auth | PyJWT + Passlib/bcrypt | 2.8.0 / 1.7.4 |
| Rate Limiting | SlowAPI | 0.1.9 |
| PDF Generation | ReportLab | 4.2.5 |
| Observability | OpenTelemetry + Prometheus | 1.24.0 / 0.20.0 |
| LLM | Google Gemini / Gemma 4 | gemini-2.0-flash |
| Testing | Pytest + pytest-asyncio | 8.2.2 / 0.23.7 |

### Frontend
| Component | Technology | Version |
|---|---|---|
| UI Framework | React | 18 |
| Language | TypeScript | 5.x |
| Build Tool | Vite | 5.4 |
| Styling | Tailwind CSS | 3.x |
| Animation | Framer Motion | 11.x |
| HTTP Client | Axios | 1.x |
| State Management | Zustand | 4.x |
| Charts | Recharts | 2.x |

### Infrastructure
| Service | Platform |
|---|---|
| Frontend | Vercel (Edge Network) |
| Backend | Railway (Docker, auto-scaling) |
| Database | Neon (Serverless PostgreSQL) |
| Cache | Upstash (Serverless Redis, TLS) |
| Model Registry | HuggingFace Hub |
| Container | Docker + Docker Compose |
| Orchestration | Kubernetes manifests (included) |

---

## API Reference

Full interactive docs: **[nikaai-production.up.railway.app/docs](https://nikaai-production.up.railway.app/docs)**

```
POST   /api/v1/auth/login              # JWT authentication
POST   /api/v1/predict                 # YOLOv8 inference + MC Dropout
GET    /api/v1/inspections             # Paginated inspection history
GET    /api/v1/analytics/dashboard     # Aggregated defect analytics
GET    /api/v1/analytics/report/pdf/{id}  # ReportLab PDF generation
GET    /api/v1/maintenance/fleet       # Fleet health overview
GET    /api/v1/maintenance/predict/{id}   # RUL prediction per machine
GET    /api/v1/maintenance/trend/*     # Daily/weekly/monthly trend data
POST   /api/v1/assistant/ask          # LLM Q&A (Gemma 4)
GET    /api/v1/models                  # Model version registry
GET    /api/v1/inference/history       # Full inference audit log
GET    /api/v1/audit                   # Enterprise audit trail
GET    /api/v1/health                  # Health check + uptime
GET    /metrics                        # Prometheus metrics endpoint
```

---

## Project Structure

```
NikaAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/          # auth, predict, inspections, analytics,
│   │   │                           # maintenance, assistant, models, audit
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings, env validation
│   │   │   ├── database.py         # SQLAlchemy engine + session factory
│   │   │   ├── security.py         # JWT encode/decode, bcrypt hashing
│   │   │   ├── middleware.py       # Request logging, correlation IDs
│   │   │   └── db_init.py          # Schema creation + seed data
│   │   ├── models/
│   │   │   ├── db_models.py        # SQLAlchemy ORM models
│   │   │   └── best.pt             # YOLOv8s weights (83% mAP)
│   │   └── services/
│   │       ├── prediction.py       # YOLOv8 inference + MC Dropout
│   │       ├── gemma.py            # LLM reasoning engine
│   │       ├── analytics.py        # Dashboard aggregations
│   │       ├── predictive_maintenance.py  # RUL + failure risk scoring
│   │       ├── trend_analysis.py   # Time-series defect trends
│   │       ├── visualization_engine.py   # Defect overlay rendering
│   │       ├── report.py           # ReportLab PDF generation
│   │       ├── audit.py            # Audit trail service
│   │       ├── ml_monitoring.py    # Model drift + performance tracking
│   │       └── inference_history.py  # Inference log management
│   ├── tests/                      # Pytest test suite
│   ├── alembic/                    # DB migration scripts
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/             # LoginModal, PredictionCanvas,
│   │   │                           # MetricsBar, ConfidenceChart, etc.
│   │   ├── pages/                  # Home, LiveInspection, Dashboard,
│   │   │                           # Maintenance, Copilot, ModelRegistry,
│   │   │                           # InferenceHistory, AuditLogs
│   │   ├── hooks/                  # useInference, useBackendHealth,
│   │   │                           # useCamera, useNotifications
│   │   ├── lib/
│   │   │   └── apiClient.ts        # Axios client, retry logic, error normalization
│   │   └── store/
│   │       └── inspectionStore.ts  # Zustand global state
│   ├── vercel.json
│   └── vite.config.ts
├── kubernetes/
│   └── nika_k8s_manifests.yaml    # Deployment, Service, Ingress, HPA
├── design/                         # UI/UX design mockups (Figma exports)
└── docker-compose.yml
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose (optional)
- PostgreSQL 14+ or Neon account
- Redis or Upstash account

### Docker (Recommended)

```bash
git clone https://github.com/chandanNegi39671/NikaAI
cd NikaAI
cp backend/.env.example backend/.env   # add your credentials
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # configure environment variables
alembic upgrade head                              # run migrations
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Environment Configuration

```env
# Backend — backend/.env
ENV=production
SECRET_KEY=<64-char random hex>
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
REDIS_URL=rediss://default:token@host:6379
CELERY_BROKER_URL=rediss://default:token@host:6379
CELERY_RESULT_BACKEND=rediss://default:token@host:6379
GOOGLE_AI_KEY=<your-gemini-api-key>
GOOGLE_AI_MODEL=gemini-2.0-flash
CORS_ORIGINS=["https://your-frontend.vercel.app"]
CONFIDENCE_THRESHOLD=0.25
LOG_LEVEL=INFO
```

```env
# Frontend — frontend/.env.production
VITE_API_URL=https://your-backend.up.railway.app
```

---

## Deployment

### Backend → Railway

```bash
# railway.toml already configured in backend/
# Set root directory to backend/ in Railway dashboard
# All environment variables configured via Railway Variables tab
```

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
# Set VITE_API_URL in Vercel Environment Variables
```

### Kubernetes

```bash
kubectl apply -f kubernetes/nika_k8s_manifests.yaml
```

---

## Security

- **Authentication:** JWT (HS256) with access + refresh token rotation
- **Authorization:** RBAC — Admin / Supervisor / Worker role hierarchy
- **Rate Limiting:** SlowAPI — 5 req/min on `/predict`, 10 req/min on `/auth/login`
- **Headers:** CSP, X-Frame-Options, X-Content-Type-Options, HSTS
- **Data:** bcrypt password hashing (rounds=12), parameterized SQL queries
- **Transport:** TLS enforced on all external services (Redis, PostgreSQL)
- **Audit:** Full request audit trail with IP, user agent, correlation ID

---

## Observability

- **Tracing:** OpenTelemetry → spans on every DB query and HTTP request
- **Metrics:** Prometheus endpoint at `/metrics` — inference latency, model load time, request rate, error rate
- **Logging:** Structured JSON logs with correlation IDs
- **Health:** `/api/v1/health` — returns uptime, model load status, version

---

## Testing

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

Test coverage includes: auth endpoints, prediction pipeline, analytics queries, maintenance engine, rate limiting, JWT validation.

---

## Author

**Chandan Singh Ramola**  
B.Tech Computer Science & Engineering  
ML / AI Engineer · Full-Stack Developer

📧 [chandanramola3967@gmail.com](mailto:chandanramola3967@gmail.com)  
🔗 [GitHub](https://github.com/chandanNegi39671) · [LinkedIn](https://www.linkedin.com/in/chandan-singh-3967ramola/)  
🤗 [HuggingFace](https://huggingface.co/negi3961)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built for India's 63 million MSMEs · AMD AI Hackathon Act II · July 2026

</div>
