# 🏭 Nika AI — AI Quality Copilot for MSME Manufacturing

<div align="center">

![Nika AI Banner](https://img.shields.io/badge/AMD%20AI%20Hackathon-Act%20II%202026-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)
![YOLOv8](https://img.shields.io/badge/YOLOv8-83%25%20mAP-orange?style=for-the-badge)

**Live Demo → [nika-ai-vert.vercel.app](https://nika-ai-vert.vercel.app)**  
**Backend API → [nikaai-production.up.railway.app](https://nikaai-production.up.railway.app/api/v1/health)**

*Demo credentials: `admin1` / `admin123`*

</div>

---

## 💡 The Vision

Manufacturing defects cost the global economy **$2.9 trillion annually**. Enterprise vision systems cost **$40,000–$200,000**. India has **63 million MSMEs** that can't afford either.

Nika AI puts the power of a trained quality engineer into the pocket of every factory worker — using nothing but a smartphone they already own.

---

## 🎯 The Problem

| Problem | Impact |
|---|---|
| Manual inconsistency | Same worker varies ±22% accuracy across shifts |
| Speed ceiling | 200–400 parts/hour max, manually |
| Cost of misses | Defects caught post-shipment cost 10× more |
| Zero data capture | No logs, no trends, no root cause visibility |
| Affordability wall | Enterprise systems: $40k–$200k — unreachable for 99% of MSMEs |

---

## ✨ Key Features

### 🔍 Real-Time Defect Detection
- **YOLOv8s** trained on 29,354 real industrial images across 7 merged datasets
- **17 defect classes** — cracks, scratches, pits, dents, surface anomalies and more
- **83% mAP** — production-grade accuracy
- Works from any smartphone camera, no special hardware

### 🧠 Hallucination Shield (MC Dropout)
- **Monte Carlo Dropout** runs 30 stochastic forward passes per inference
- Reliability classification: **High / Moderate / Low / UNCERTAIN**
- When the AI isn't confident, it tells you — no hallucinated certainty
- Unique to Nika AI among hackathon submissions

### 💬 Gemma 4 AI Reasoning Engine
- Powered by **Gemma 4 via Fireworks AI**
- Generates structured output: **Root Cause → Severity → Repairability → Prevention → Recommended Action**
- Not a chatbot add-on — the core reasoning brain of the product

### 📊 Analytics Dashboard
- Full inspection history with filters (date, machine, defect type, worker)
- Defect trend charts and distribution analytics
- PDF report download per inspection (ReportLab, no external dependency)
- Machine-level maintenance intelligence

### 🔐 Enterprise Security
- JWT authentication with RBAC (Admin / Supervisor / Worker roles)
- Rate limiting, CSP headers, audit logs
- Secure token handling throughout

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nika AI Stack                        │
├──────────────┬──────────────────┬───────────────────────────┤
│   Frontend   │     Backend      │      Infrastructure       │
│  React 18    │   FastAPI 0.11   │   Railway (Backend)       │
│  TypeScript  │   Python 3.11    │   Vercel (Frontend)       │
│  Vite        │   YOLOv8s        │   Neon (PostgreSQL)       │
│  Tailwind    │   Gemma 4 API    │   Upstash (Redis)         │
│  Framer      │   PostgreSQL     │                           │
│  Motion      │   ReportLab PDF  │                           │
└──────────────┴──────────────────┴───────────────────────────┘
```

### Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind CSS | Mobile-first, Camera API, fast iteration |
| Backend | FastAPI (Python 3.11) | Async, auto OpenAPI docs, Pydantic |
| Detection | YOLOv8s (Ultralytics) | 83% mAP, 17 classes, MC Dropout support |
| LLM | Gemma 4 via Fireworks AI | Structured reasoning, hackathon sponsor model |
| Database | PostgreSQL (Neon) + SQLAlchemy | Production-grade, Alembic migrations |
| Cache / Queue | Redis (Upstash) + Celery | Rate limiting, async task processing |
| PDF Reports | ReportLab | No external service, works offline |
| Deployment | Railway + Vercel | Zero-config, production-ready |
| Model Registry | HuggingFace Hub | `negi3961/factory-defect-guard` |

---

## 🚀 Quick Start

### Option 1: Live Demo
Visit **[nika-ai-vert.vercel.app](https://nika-ai-vert.vercel.app)**
- Username: `admin1` | Password: `admin123`
- Username: `operator1` | Password: `operator123`

### Option 2: Run Locally with Docker

```bash
git clone https://github.com/chandanNegi39671/NikaAI
cd NikaAI
cp backend/.env.example backend/.env  # fill in your keys
docker compose up --build
```

Visit `http://localhost:5173`

### Option 3: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## 🌐 Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | [nika-ai-vert.vercel.app](https://nika-ai-vert.vercel.app) |
| Backend API | Railway | [nikaai-production.up.railway.app](https://nikaai-production.up.railway.app) |
| Database | Neon (PostgreSQL) | Serverless Postgres |
| Cache | Upstash (Redis) | Serverless Redis |

---

## 📁 Project Structure

```
NikaAI/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── core/             # Config, DB, security
│   │   ├── models/           # YOLOv8 weights + DB models
│   │   └── services/         # Prediction, analytics, PDF
│   ├── Dockerfile
│   ├── railway.toml
│   └── requirements.txt
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── pages/            # Route pages
│   │   ├── lib/              # API client
│   │   └── hooks/            # Custom hooks
│   ├── vercel.json
│   └── vite.config.ts
├── design/                   # UI/UX mockups
├── kubernetes/               # K8s manifests
└── docker-compose.yml
```

---

## 🔑 Environment Variables

**Backend (`backend/.env`):**
```env
ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=rediss://default:token@host:6379
CELERY_BROKER_URL=rediss://default:token@host:6379
CELERY_RESULT_BACKEND=rediss://default:token@host:6379
GOOGLE_AI_KEY=your-gemini-key
GOOGLE_AI_MODEL=gemini-2.0-flash
CORS_ORIGINS=["https://your-frontend.vercel.app"]
CONFIDENCE_THRESHOLD=0.25
```

**Frontend (`frontend/.env.production`):**
```env
VITE_API_URL=https://your-backend.up.railway.app
```

---

## 👨‍💻 Author

**Chandan Singh Ramola**  
B.Tech CSE | ML / AI Engineer  
📧 chandanramola3967@gmail.com  
🔗 [GitHub](https://github.com/chandanNegi39671) · [LinkedIn](https://linkedin.com/in/chandan-singh-ramola)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ for India's 63 million MSMEs · AMD AI Hackathon Act II · July 2026
</div>
