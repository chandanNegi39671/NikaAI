# Nika AI Enterprise Platform

Nika AI is an enterprise-grade AI visual inspection platform designed to automate manufacturing defect detection. Originally built as a Hackathon Demo, this version (v3) has been completely re-architected for production readiness, scalability, and robust security.

## Architecture Highlights
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python 3.11, Ultralytics YOLOv8
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Concurrency**: ThreadPoolExecutor for non-blocking YOLO inference
- **Security**: JWT Authentication, RBAC, SlowAPI Rate Limiting, CSP Headers

## Getting Started (Docker Compose)
The easiest way to run the entire stack is via Docker Compose:

```bash
docker-compose up --build
```
This will start:
- Frontend on `http://localhost`
- Backend API on `http://localhost:8000`
- PostgreSQL database on port `5432`

## Local Development
If you prefer running components individually:

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` (update as needed)
4. `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Deployment
For production deployment, ensure that you set a secure `SECRET_KEY` in your environment, switch `ENVIRONMENT` to `production`, and map persistent volumes for the database and file uploads.
