# 🏭 Nika AI — AI Quality Copilot for MSME Manufacturing

> **AMD AI Developer Hackathon: Act II · July 6–11, 2026 · $20,000+ Prize Pool**  
> Track 3: Unicorn · Bonus Challenge: Best Use of Gemma 4  
> Author: Chandan Singh Ramola · chandanramola3967@gmail.com

---

## 💡 Vision

To democratize industrial quality control — making AI-powered defect detection accessible to every MSME factory on the planet, using nothing more than a smartphone.

Nika AI turns any factory worker into a trained quality engineer by putting the power of a **YOLOv8 computer vision model** and a **Gemma 4 AI reasoning engine** directly in their pocket.

> Manufacturing defects cost the global economy an estimated **$2.9 trillion annually**. Enterprise vision systems cost $40,000–$200,000. Nika AI's barrier to entry is a smartphone the worker already owns.

---

## 🎯 The Problem

India alone has **63 million MSMEs** employing over 110 million people. Quality control in these factories remains almost entirely manual — inconsistent, slow, and blind to root causes.

| Problem | Impact |
|---|---|
| Inconsistency | Same worker varies ±22% across shifts |
| Speed ceiling | Manual inspection bottleneck — 200–400 parts/hour max |
| Cost of misses | Missed defects cost 10× more post-shipment |
| Zero data capture | No logs, no trends, no root cause visibility |
| Affordability wall | Enterprise systems: $40k–$200k — unreachable for 99% of MSMEs |

---

## ✨ Key Features

### 🔍 Real-Time Defect Detection
- YOLOv8s model trained on **29,354 real industrial images** across **7 merged datasets**
- **17 defect classes** with 83% mAP
- Camera capture or image upload from any smartphone

### 🧠 Hallucination Shield (MC Dropout)
- Monte Carlo Dropout uncertainty quantification runs **30 stochastic forward passes**
- Classifies reliability: **High / Moderate / Low / UNCERTAIN**
- When the AI is uncertain, it tells you — instead of confidently lying
- *No other hackathon project will have this combination*

### 💬 Gemma 4 AI Reasoning Engine
- Powered by **Gemma 4 via Fireworks AI** (hackathon sponsor model)
- Structured output: **Root Cause → Severity → Repairability → Prevention → Recommended Action**
- Not a chatbot add-on — the core reasoning brain of the entire product
- Directly targets the **$6,000 Best Use of Gemma 4 bonus prize**

### 📊 Inspection History & Analytics
- Full inspection log with filters (date, machine, defect type, worker, action)
- Analytics dashboard with defect trends and distribution charts
- **PDF report download** per inspection (ReportLab, no external dependency)

### 🔐 Enterprise Security
- JWT authentication with RBAC (Admin / Supervisor / Worker roles)
- Rate limiting, CSP headers, secure token handling

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nika AI Stack                        │
├──────────────┬──────────────────┬───────────────────────────┤
│   Frontend   │     Backend      │      AMD Cloud GPU        │
│  React 18    │   FastAPI 0.11   │   ROCm-compatible         │
│  TypeScript  │   Python 3.11    │   YOLOv8 Inference        │
│  Vite        │   YOLOv8s        │   $100 Credits            │
│  Tailwind    │   Gemma 4 API    │                           │
│  Framer      │   PostgreSQL     │                           │
│  Motion      │   ReportLab PDF  │                           │
└──────────────┴──────────────────┴───────────────────────────┘
```

### Tech Stack

| Layer | Technology | Reasoning |
|---|---|---|
| Frontend | React 18 + Vite + Tailwind CSS | Mobile-responsive, Camera API, fast iteration |
| Backend | FastAPI (Python 3.11) | Async, auto OpenAPI docs, native Pydantic |
| Detection Model | YOLOv8s (Ultralytics) | Pre-trained 83% mAP, 17 classes, MC Dropout |
| LLM / Reasoning | Gemma 4 via Fireworks AI | Sponsor model — targets $6,000 bonus prize |
| Database | PostgreSQL + SQLAlchemy | Production-grade, Alembic migrations |
| PDF Reports | ReportLab (Python) | No external service, works offline |
| Deployment | Docker + AMD Developer Cloud | Mandatory sponsor tech, ROCm GPU acceleration |
| Model Registry | HuggingFace Hub | `negi3961/factory-defect-guard` |

---

## 🚀 Quick Start (Docker Compose)

```bash
git clone https://github.com/negi3961/NikaAI
cd NikaAI
docker compose up --build
```

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

Default credentials: `admin1` / `admin123`

---

## ☁️ AMD Developer Cloud Deployment

Nika AI is deployed on **AMD Developer Cloud** using the $100 hackathon credits with ROCm GPU acceleration.

### Deploy on AMD Cloud

```bash
# 1. Launch an AMD MI210/MI300X instance (Ubuntu 22.04 + ROCm)
# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Clone and deploy
git clone https://github.com/negi3961/NikaAI
cd NikaAI
docker compose up --build -d
```

### ROCm GPU Configuration

The `docker-compose.yml` is configured for AMD GPU acceleration:

```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: amdgpu
              capabilities: [gpu]
```

YOLOv8 inference runs on the AMD ROCm pipeline — no NVIDIA CUDA required.

---

## 🧪 Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Reference

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Login, returns JWT | — |
| POST | `/api/v1/predict` | Run defect detection on image | JWT |
| POST | `/api/v1/explain` | Invoke Gemma 4 reasoning on detection | JWT |
| GET | `/api/v1/inspections` | Paginated inspection history | JWT |
| GET | `/api/v1/inspections/{id}` | Single inspection detail | JWT |
| GET | `/api/v1/analytics/report/pdf/{id}` | Download PDF report | JWT |
| GET | `/api/v1/analytics/dashboard` | Analytics dashboard data | JWT |

Full interactive docs at `/docs` (Swagger UI).

---

## 🏆 Why Nika AI Should Win

### Five Unique Selling Points

**1. 🛡️ The Hallucination Shield**  
Every other submission shows a confidence score. Nika AI tells you *when to distrust the AI*. MC Dropout uncertainty quantification is graduate-level ML engineering that judges with ML backgrounds will immediately recognize as technically significant.

**2. 🧠 Gemma 4 as a Domain Expert**  
Not a chatbot. A manufacturing quality engineer with structured output — causes, severity, repairability, prevention, action. Precisely what the $6,000 bonus prize is designed to recognize.

**3. 📦 Real Pre-Trained Model**  
29,354 industrial images. 7 datasets merged. 17 defect classes. 83% mAP. Production-ready ML work — not a demo model on 200 images.

**4. 🌍 Genuine Billion-Dollar Market**  
63 million MSMEs in India. $40,000 minimum for enterprise alternatives. Nika AI's barrier to entry: a smartphone the worker already owns.

**5. ✅ Complete Working Product**  
Detection + uncertainty evaluation + AI explanation + inspection logging + PDF reports + inspection history. A working product, not a proof of concept.

### Prize Category Alignment

| Prize | Nika AI's Position |
|---|---|
| 🥇 Track 3: Unicorn | Full-stack AI app, genuine novelty (Hallucination Shield), real model, billion-dollar market |
| 💡 Best Use of Gemma 4 ($6,000) | Gemma 4 is the core reasoning engine — not decorative. Central to product value |
| ☁️ AMD GPU Usage | Deployed on AMD Developer Cloud with ROCm pipeline using $100 credits |

---

## 👨‍💻 Author

**Chandan Singh Ramola**  
chandanramola3967@gmail.com  
GitHub: [@negi3961](https://github.com/negi3961)  
HuggingFace: [negi3961/factory-defect-guard](https://huggingface.co/negi3961/factory-defect-guard)

---

*Built for AMD AI Developer Hackathon: Act II · July 6–11, 2026*
