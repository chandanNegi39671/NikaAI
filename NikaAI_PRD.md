## **NIKA AI** 

## **AI Quality Copilot for MSME Manufacturing** 

Product Requirements Document  ·  v1.0 

**AMD AI Developer Hackathon: Act II  ·  July 6–11, 2026  ·  $20,000+ Prize Pool** 

Author: Chandan Singh Ramola  ·  chandanramola3967@gmail.com Track 3: Unicorn  ·  Bonus Challenge: Best Use of Gemma 4 

## **1. Vision** 

💡 

To democratize industrial quality control — making AI-powered defect detection accessible to every MSME factory on the planet, using nothing more than a smartphone. 

Nika AI is not a replacement for human workers. It is a cognitive upgrade. It turns any factory worker into a trained quality engineer by putting the power of a YOLOv8 computer vision model and a Gemma 4 AI reasoning engine directly in their pocket. 

Manufacturing defects cost the global economy an estimated $2.9 trillion annually. The vast majority of that loss occurs in small and medium enterprises — not because the problems are unavoidable, but because MSMEs cannot afford the $40,000–$200,000 industrial vision systems used by large manufacturers. 

Nika AI closes that gap completely. The only hardware requirement is a smartphone that the worker already owns. 

## **2. Problem Statement** 

## **2.1 The MSME Quality Crisis** 

India alone has 63 million MSMEs employing over 110 million people. Globally, MSMEs represent 90% of all businesses. Yet quality control in these factories remains almost entirely manual — a worker visually inspects a part, makes a subjective judgment, and passes or rejects it. 

|**Problem**|**Impact**|**Scale**|
|---|---|---|
|Inconsistency|Defect pass/reject based on worker fatgue,<br>experience, mood|Same worker varies ±22%<br>across shifs|
|Speed ceiling|Manual inspecton botleneck — 200–400<br>parts/hour maximum|Every botleneck = lost revenue|
|Cost of misses|Missed defects → returns, warranty claims,<br>safety incidents|Avg defect costs 10× more<br>post-shipment|
|Zero data capture|No logs, no trends, no root cause visibility|Managers fying blind on<br>quality|
|Afordability wall|Enterprise vision systems: $40k–$200k —<br>unreachable for MSMEs|99% of MSMEs have zero AI QC<br>tools|



## **2.2 Why Existing Solutions Fail** 

- Enterprise systems (Cognex, Keyence, Basler): hardware-locked, $40k+ investment, specialist integrators required 

- Generic QC software: not trained on industrial defects, requires costly custom dataset creation 

- Manual checklists: no consistency, no trend capture, no intelligence, no feedback loop 

- No solution addresses the 'why': workers know something is wrong but not cause, severity, or action 

## **3. Target Users** 

|**User Type**|**Role**|**Primary Pain**|**Nika AI Value**|
|---|---|---|---|
|Factory Worker|Operates producton<br>line, performs visual<br>QC|Subjectve judgment, no<br>guidance when uncertain|Real-tme AI guidance on<br>every part|
|Quality Manager|Sets standards,<br>reviews rejectons,<br>reports upward|No live data, reactve not<br>proactve|Live dashboard: trends,<br>alerts, defect rates|
|Factory Owner|P&L responsibility,<br>client relatonships|Defect costs eatng margins,<br>no budget for enterprise<br>tools|Enterprise-grade QC at<br>near-zero hardware cost|
|Process Engineer|Root cause analysis,<br>process improvement|Cannot see paterns across<br>thousands of inspectons|AI-generated defect<br>clustering and trend signals|



## **4. User Personas** 

## **Persona 1 — Ravi, 28, Line Inspector** 

Ravi works a 9-hour shift at a steel components factory in Pune. He inspects ~300 parts per 💡 shift. He has no formal QC training — learned by watching senior workers. He owns an Android phone with a 12MP camera. 

Goals: Do his job correctly. Not be blamed for defects that slip through. Finish on time. 

Frustrations: Uncertain about borderline parts. No one explains why a defect matters or what to do. Fatigue after hour 6 causes him to miss subtle defects. 

How Nika AI helps: Real-time detection removes subjectivity. Gemma 4 explains what the defect is and what to do next. Ravi feels competent and confident rather than guessing. 

## **Persona 2 — Priya, 42, Quality Manager** 

💡 

Priya manages QC for a PCB assembly unit with 45 workers across 3 shifts. She manually compiles defect reports from handwritten logs. Reporting takes 4 hours every Friday. 

Goals: Reduce customer returns. Identify which machines or workers are generating defects. Present clean data to the MD. 

Frustrations: Data is stale by the time it reaches her. Cannot correlate defect spikes with shift changes or machine maintenance schedules. 

How Nika AI helps: Live inspection dashboard. Automatic defect logging. Trend alerts when defect rate on a machine exceeds configured threshold. Friday reports generated in one click. 

## **Persona 3 — Vikram, 55, Factory Owner** 

💡 

Vikram runs a 60-person metal components factory supplying Tier-1 auto parts. He lost a contract last year due to a defective batch. He is cost-conscious but growth-oriented. 

Goals: Win back OEM clients. Prove quality standards. Avoid future defect incidents that cost contracts. 

Frustrations: Cannot afford enterprise vision systems. Does not trust his current QC process but has no affordable alternative. 

How Nika AI helps: Zero hardware cost — works on existing factory smartphones. Provides quality-inspection certificates backed by AI inspection logs. Competitive differentiation with OEM clients. 

## **5. User Journey** 

## **5.1 Worker Inspection Journey** 

|**Step**|**Acton**|**System Response**|**Worker Emoton**|
|---|---|---|---|
|1|Worker opens Nika AI on<br>smartphone|Camera actvates, YOLOv8 model loads from edge<br>cache|Ready|
|2|Points camera at<br>manufactured part|Live inference begins — bounding boxes appear<br>in real-tme at 15+ FPS|Focused|
|3|Defect detected:<br>'Surface Crack'|Hallucinaton Shield checks confdence: 91% →<br>reliability ter = HIGH|Alert|
|4|Result displayed<br>instantly|Red bounding box + 'Surface Crack — 91% —<br>HIGH — REJECT'|Informed|
|5|Worker taps 'Why?'<br>buton|Gemma 4 returns: defect cause, severity,<br>repairability, recommended acton|Empowered|
|6|Worker marks part as<br>Rejected|Inspecton logged to DB, PDF report entry<br>created, dashboard updated|Confdent|
|7|Borderline part detected<br>at 48% confdence|Hallucinaton Shield fres: 'UNCERTAIN — Human<br>Review Required'|Cautous|
|8|Worker escalates to<br>supervisor|Escalaton logged with image, tmestamp,<br>confdence score|Accountable|



## **5.2 Manager Journey** 

- Logs into web dashboard on desktop or tablet 

- Views today's inspection summary: total inspections, acceptance rate, top defect types 

- Drills into Machine 3 — defect rate spiked 40% this shift 

- Downloads PDF shift report for the last 8 hours 

- Configures alert: notify via dashboard badge if defect rate > 15% on any machine 

## **6. Features** 

## **6.1 Core MVP Features (P0 — Must Ship)** 

|**Feature**|**Descripton**|**Priority**|
|---|---|---|
|Real-Time Defect<br>Detecton|YOLOv8s running via API — 17 defect classes across steel<br>surfaces, PCBs, and industrial components. Webcam<br>snapshot mode for demo.|P0 — Core|
|Hallucinaton Shield|MC Dropout uncertainty estmaton (10 forward passes).<br>Classifes reliability as HIGH / MEDIUM / UNCERTAIN.<br>Blocks UNCERTAIN results from auto-passing.|P0 — Core|
|Gemma 4 AI Explanaton|On-demand quality engineering guidance — root cause,<br>severity, repairability, preventon, recommended acton.<br>Triggered by worker request or low confdence.|P0 — Bonus<br>Prize|
|Inspecton Logging|Every inspecton persisted: image path, defect class,<br>confdence, reliability ter, acton taken, worker ID,<br>tmestamp, machine ID.|P0 — Core|
|PDF Report Generaton|Per-inspecton PDF: inspecton ID, image thumbnail,<br>bounding boxes, defect class, confdence, reliability ter,<br>Gemma recommendaton, acton.|P0 — Demo|
|React Web UI|Mobile-responsive — live camera view, detecton overlay,<br>result panel, Gemma explanaton panel, inspecton history<br>tab.|P0 — Core|
|FastAPI Backend|Async REST API — /predict, /explain, /inspectons,<br>/report, /analytcs, /auth endpoints with JWT<br>authentcaton.|P0 — Core|



## **6.2 Enhanced Features (P1 — Post-MVP)** 

|**Feature**|**Descripton**|**Priority**|
|---|---|---|
|Analytcs Dashboard|Defect trends over tme, acceptance rate by<br>machine/shif/worker, anomaly detecton alerts|P1|
|Voice Interacton|Worker speaks 'Is this acceptable?' — Gemma 4<br>replies via text-to-speech|P1|
|Inspecton History Filter|Filter by date range, machine, defect class, reliability<br>ter, acton taken|P1|
|Real-Time Video Stream|WebRTC contnuous stream vs current snapshot<br>mode — true contnuous inspecton|P1|
|Mult-language UI|Hindi, Tamil, Telugu — worker instructons in local<br>language|P2|
|Edge/Ofine ONNX|ONNX-exported model with service worker — works<br>in factories with no internet|P2|
|ERP Integraton|Push defect data to SAP, Tally, or custom ERP via|P2|



|**Feature**|**Descripton**|**Priority**|
|---|---|---|
||webhook||
|Quality Certfcate PDF|AI-signed quality certfcate for shipment — backed<br>by inspecton record hash|P2|



## **7. Functional Requirements** 

## **FR-1: Defect Detection** 

- System SHALL accept image input via webcam capture (base64) or multipart file upload 

- System SHALL run YOLOv8 inference and return bounding boxes, class names, and confidence scores 

- System SHALL support all 17 trained defect classes as defined in the negi3961/factory-defect-guard model 

- System SHALL complete single-image inference in < 500ms on GPU hardware 

- System SHALL return confidence scores as float values in range [0.0, 1.0] 

## 

## 

- System SHALL execute N=10 Monte Carlo Dropout forward passes per inference request 

- System SHALL compute mean confidence (μ) and variance (σ²) across all passes for each bounding box 

- System SHALL classify reliability tier: HIGH (μ > 0.75, σ² < 0.02), MEDIUM (μ > 0.50), UNCERTAIN (otherwise) 

- System SHALL include reliability_tier and mc_variance in every detection response 

- System SHALL never auto-pass UNCERTAIN detections — must require explicit human review action 

## **FR-3: Gemma 4 Explanation** 

- System SHALL invoke Gemma 4 when: (a) worker taps 'Why?', or (b) reliability_tier is UNCERTAIN 

- Gemma 4 prompt SHALL include: defect_class, confidence score, reliability tier, and manufacturing domain context 

- Response SHALL be structured JSON with: possible_causes[], repairability, severity, prevention, recommended_action, confidence_note 

- Plain-language response — no ML jargon — readable at 8th-grade level 

- System SHALL persist Gemma explanation to database linked to the detection record 

## **FR-4: Inspection Logging** 

- Every completed inspection SHALL be persisted within 2 seconds of worker action 

- Log SHALL include: inspection_id, worker_id, machine_id, timestamp, image_path, overall_action, shield_triggered flag 

- Each detection within an inspection SHALL be separately logged with all confidence and bounding box data 

- System SHALL support paginated retrieval with filters: date range, machine_id, defect_class, worker_id, action 

## **FR-5: Report Generation** 

- System SHALL generate a single-inspection PDF report on demand (GET or POST trigger) 

- Report SHALL include: inspection ID, timestamp, worker, machine, image with bounding box overlay, defect class, confidence, reliability tier, Gemma explanation, final action 

- System SHALL generate shift summary PDFs aggregating all inspections within a specified time window 

## **8. Non-Functional Requirements** 

|**Category**|**Requirement**|**Target**|
|---|---|---|
|Performance|Single image inference latency (API mode)|< 500ms|
|Performance|Gemma 4 explanaton response tme|< 4 seconds|
|Performance|UI webcam capture + display cycle|< 1 second end-to-end|
|Reliability|API uptme during hackathon demo window|99.5%+|
|Scalability|Concurrent inspecton sessions supported|10+ (MVP), 100+ (Phase 2)|
|Security|Worker session management|JWT token, 8-hour expiry|
|Security|Image storage|Filesystem paths in DB — no<br>image BLOBs, served as statc fles|
|Usability|Time for new worker to complete frst<br>inspecton|< 5 minutes|
|Usability|Mobile viewport support|360px+ width, touch-optmized<br>controls|
|Portability|Primary deployment target|AMD Developer Cloud (ROCm<br>GPU) via Docker|
|Observability|Request logging|Structured JSON logs with<br>request_id tracing|
|Compliance|Image data retenton|Images stored locally, no third-<br>party upload without consent|



## **9. AI Architecture** 

## **9.1 Detection Layer — YOLOv8s + MC Dropout** 

**==> picture [31 x 52] intentionally omitted <==**

**----- Start of picture text -----**<br>
💡<br>**----- End of picture text -----**<br>


Pre-trained YOLOv8s model on 29,354 industrial images across 7 datasets and 17 defect classes. MC Dropout injected into C2f blocks post-training for uncertainty estimation. Production model: negi3961/factory-defect-guard on HuggingFace Hub. 

Training progression demonstrating iterative improvement: 

- V5 — 43 epochs, early stopping: mAP@0.5 = 74.8% 

- V6 — 60 epochs, full run: mAP@0.5 = 79.6% 

- V6_MC — MC Dropout fine-tune (production model): mAP@0.5 = 83.0% 

MC Dropout Uncertainty Pipeline — step by step: 

- Step 1: Set model to train() mode (enables dropout) while disabling gradient computation (torch.no_grad()) 

- Step 2: Execute N=10 stochastic forward passes on the identical input image 

- Step 3: Collect confidence scores across all passes for each detected bounding box 

- Step 4: Compute mean confidence μ and variance σ² per box 

- Step 5: Apply reliability tier thresholds (HIGH / MEDIUM / UNCERTAIN) 

- Step 6: Return tier and variance alongside standard detection results 

## **9.2 Reasoning Layer — Gemma 4 via Fireworks AI** 

Gemma 4 is Google DeepMind's latest open model and the AMD Hackathon's $6,000 💡 bonus prize target. Accessed via Fireworks AI API using the $50 Fireworks credits included in the hackathon developer perks. 

Prompt engineering strategy: Nika AI uses a structured system prompt casting Gemma 4 as a 'Senior Manufacturing Quality Engineer with 20 years of experience.' The user prompt passes: 

- Detected defect class name (e.g., 'surface_crack') 

- Mean confidence score and reliability tier from the Hallucination Shield 

- Manufacturing domain context (steel surface / PCB / industrial component) 

- Output format specification: JSON with fields causes[], repairability, severity, prevention, recommended_action 

## **9.3 Per-Class Model Performance** 

|**Defect Class**|**mAP@0.5**|**Domain**|**Shield Behavior**|
|---|---|---|---|
|tle_defect|99.5%|Industrial (MVTec)|Rarely triggers — near-perfect|



|**Defect Class**|**mAP@0.5**|**Domain**|**Shield Behavior**|
|---|---|---|---|
||||confdence|
|pcb_missing_hole|99.3%|PCB|Geometric shape — consistently<br>HIGH ter|
|pcb_short|95.5%|PCB|Strong color/line signal|
|patches|91.6%|Steel (NEU)|Clear texture anomaly|
|pcb_open_circuit|90.7%|PCB|Reliable line-break detecton|
|pcb_spurious_copper|91.1%|PCB|Distnct color signature|
|inclusion|81.3%|Steel|Variable depth afects confdence|
|scratches|80.7%|Steel|Directon-sensitve — shield watches<br>variance|
|rolled_in_scale|57.4%|Steel|Low contrast — MEDIUM ter<br>common|
|screw_defect|56.8%|Industrial|High intra-class variaton — shield<br>ofen fres|
|transistor_defect|54.0%|Industrial|Small component, low pixel density<br>at 640px|
|crazing|48.9%|Steel|Hardest class — subtle texture.<br>Shield ALWAYS fres → Gemma<br>explains|



## **9.4 Why This AI Architecture Stands Apart** 

Most hackathon submissions stop at detection. Confidence score = 0.62 means nothing to a factory worker. Nika AI adds two layers that transform raw ML output into actionable industrial intelligence: 

- Hallucination Shield: Quantifies epistemic uncertainty. Communicates not just what the model thinks, but how much to trust it. This is graduate-level ML engineering, not just model deployment. 

- Gemma 4 Reasoning Layer: Translates machine output into human-readable quality engineering guidance. A worker does not need to know what 'crazing' means — Gemma tells them it is microscopic surface cracking from rapid thermal cycling, it is non-repairable, and the part must be scrapped. 

No other submission at this hackathon will combine MC Dropout uncertainty quantification with LLM-powered domain-expert explanation in a real-time industrial inspection system. This combination is the project's defining technical contribution. 

## **10. System Architecture** 

## **10.1 Architecture Diagram** 

```
┌───────────────────────────────────────────────────────────┐ │                    CLIENT LAYER
│ │   React + Vite + Tailwind CSS (Mobile-Responsive)        │ │  ┌──────────────┐
┌──────────────┐ ┌───────────────────┐ │ │  │  Camera View │ │ Result Panel │ │  History /
Reports│ │ │  └──────┬───────┘ └──────┬───────┘ └───────────────────┘ │
└─────────┼────────────────┼───────────────────────────────┘           │  HTTP / WebSocket REST
API                        ┌─────────▼────────────────▼───────────────────────────────┐ │
FASTAPI BACKEND                         │ │  Route Layer: /predict /explain /inspections /report
│ │  ──────────────────────────────────────────────────────── │ │  Detection Service   Uncertainty
Shield   Gemma 4 Client  │ │  (YOLOv8s)          (MC Dropout, N=10)   (Fireworks API)  │ │
──────────────────────────────────────────────────────── │ │  Data Access Layer → SQLite (MVP) /
PostgreSQL (Prod)     │ └────────────┬──────────────────────────┬───────────────────┘
│                          │    ┌─────────▼──────────┐   ┌──────────▼────────────┐    │
HuggingFace Hub   │   │  Fireworks AI API     │    │  YOLOv8 Weights    │   │  Gemma 4 Inference
│    │  negi3961 repo     │   │  $50 hackathon credits│    └────────────────────┘
└───────────────────────┘
```

## **10.2 Deployment on AMD Cloud** 

- Backend + Frontend: Single Docker container deployed to AMD Developer Cloud 

- GPU: ROCm-compatible inference pipeline for YOLOv8 — uses the $100 AMD Developer Cloud credits 

- Model: Pulled from HuggingFace Hub on container startup, cached in /models/ 

- Database: SQLite volume-mounted for persistence across container restarts 

- Static files: Nginx serves the React build and inspection images 

## **10.3 Tech Stack Decision Table** 

|**Layer**|**Technology**|**Reasoning**|
|---|---|---|
|Frontend|React + Vite + Tailwind CSS|Fast iteraton during hackathon. Mobile-responsive out<br>of box. Camera API straightorward.|
|Backend|FastAPI (Python 3.11)|Async, auto-generates OpenAPI docs, natve Pydantc<br>validaton, Python ML ecosystem.|
|Detecton Model|YOLOv8s (Ultralytcs)|Own pre-trained model — 83% mAP, 17 classes, MC<br>Dropout uncertainty built in.|
|LLM / Reasoning|Gemma 4 via Fireworks AI|Sponsor model — directly targets $6,000 bonus prize.<br>Fast inference. Fireworks credits included.|
|Database|SQLite → PostgreSQL|Zero-confg for hackathon MVP. Schema designed to be<br>PostgreSQL-portable.|
|PDF Reports|ReportLab (Python)|Programmatc PDF — no external service dependency.<br>Works ofine.|
|Deployment|Docker + AMD Developer<br>Cloud|Mandatory sponsor tech. ROCm GPU acceleraton. $100<br>credits available.|
|Model Registry|HuggingFace Hub|Industry standard, free, versioned. negi3961/factory-<br>defect-guard already published.|



## **11. API Reference** 

## **11.1 Endpoint Summary** 

|**Meth**<br>**od**|**Endpoint**|**Descripton**|**Auth**|
|---|---|---|---|
|POST|/api/v1/predict|Run defect detecton on image. Returns bounding<br>boxes, class names, confdence, and reliability ter.|JWT|
|POST|/api/v1/explain|Invoke Gemma 4 on a detecton. Returns structured<br>quality engineering guidance.|JWT|
|GET|/api/v1/inspectons|Paginated inspecton history with flters (date,<br>machine, defect, worker, acton).|JWT|
|GET|/api/v1/inspectons/{id}|Single inspecton detail — full detectons, Gemma<br>explanatons, image path.|JWT|
|POST|/api/v1/inspectons/{id}/acton|Record worker's fnal acton on an inspecton<br>(ACCEPT / REJECT / ESCALATE).|JWT|
|POST|/api/v1/report/inspecton/{id}|Generate and return PDF report for a single<br>inspecton.|JWT|
|POST|/api/v1/report/shif|Generate shif summary PDF for a specifed tme<br>range.|JWT|
|GET|/api/v1/analytcs/summary|Dashboard data: totals, acceptance rate, top defects,<br>daily trend.|JWT|
|POST|/api/v1/auth/login|Authentcate worker/manager. Returns JWT access<br>token.|None|
|GET|/api/v1/health|Health check — model loaded, GPU status, DB<br>connecton.|None|



## **11.2 Key Response Schemas** 

## **POST /api/v1/predict — Response Body** 

```
{   "inspection_id": "insp_20260707_143022_a3f1",   "timestamp": "2026-07-07T14:30:22Z",
"detections": [     {       "detection_id": "det_a3f1_01",       "class": "surface_crack",
"confidence": 0.91,       "mc_mean": 0.91,       "mc_variance": 0.008,
"reliability_tier": "HIGH",       "bbox": { "x1": 120, "y1": 80, "x2": 340, "y2": 210 },
"recommended_action": "REJECT"     }   ],   "overall_action": "REJECT",   "shield_triggered":
false,   "inference_ms": 312 }
```

## **POST /api/v1/explain — Response Body** 

```
{   "detection_id": "det_a3f1_01",   "defect_type": "Surface Crack",   "severity": "HIGH",
"possible_causes": [     "Rapid thermal cycling during hot rolling process",
"Insufficient annealing after rolling — residual stress",     "Material impurity
concentration at crack origin"   ],   "repairability": "NOT_REPAIRABLE",   "prevention":
"Increase annealing duration by 15%. Verify roller temperature uniformity. Inspect material
certification for sulphur content.",   "recommended_action": "REJECT part. Log batch number.
Inspect 10 adjacent parts for same defect.",   "confidence_note": "Detection confidence 91% —
HIGH reliability. Result is trustworthy." }
```

## **12. Database Design** 

## **12.1 Entity Relationship Overview** 

Five core tables: Workers (authentication and attribution), Machines (location context), Inspections (session records), Detections (per-bounding-box results), and Explanations (Gemma 4 outputs). Relationships are 1:N at every level — one inspection contains many detections; one detection may have one explanation. 

## **12.2 Schema (SQLite / PostgreSQL compatible)** 

```
-- Workers: authentication and role management CREATE TABLE workers (     id           TEXT PRIMARY KEY,
-- UUID     name         TEXT NOT NULL,     role         TEXT CHECK(role IN ('worker', 'manager',
'admin')),     factory_id   TEXT,     created_at   DATETIME DEFAULT CURRENT_TIMESTAMP );  -- Machines:
physical asset tracking CREATE TABLE machines (     id           TEXT PRIMARY KEY,     name         TEXT
NOT NULL,     factory_id   TEXT,     location     TEXT );  -- Inspections: one record per inspection
session CREATE TABLE inspections (     id               TEXT PRIMARY KEY,       --
insp_YYYYMMDD_HHMMSS_uid     worker_id        TEXT REFERENCES workers(id),     machine_id       TEXT
REFERENCES machines(id),     timestamp        DATETIME NOT NULL,     image_path       TEXT,
-- local filesystem path     overall_action   TEXT CHECK(overall_action IN ('ACCEPT', 'REJECT',
'ESCALATE', 'PENDING')),     shield_triggered BOOLEAN DEFAULT FALSE,     created_at       DATETIME
DEFAULT CURRENT_TIMESTAMP );  -- Detections: one record per bounding box per inspection CREATE TABLE
detections (     id               TEXT PRIMARY KEY,     inspection_id    TEXT REFERENCES inspections(id)
ON DELETE CASCADE,     defect_class     TEXT NOT NULL,     confidence       REAL NOT NULL,     mc_mean
REAL,     mc_variance      REAL,     reliability_tier TEXT CHECK(reliability_tier IN ('HIGH', 'MEDIUM',
'UNCERTAIN')),     recommended_action TEXT,     bbox_x1 REAL, bbox_y1 REAL, bbox_x2 REAL, bbox_y2
REAL );  -- Explanations: Gemma 4 output, keyed to a detection CREATE TABLE explanations (     id
TEXT PRIMARY KEY,     detection_id     TEXT REFERENCES detections(id) ON DELETE CASCADE,     severity
TEXT,     causes_json      TEXT,                   -- JSON array of cause strings     repairability
TEXT,     prevention       TEXT,     recommended_action TEXT,     confidence_note  TEXT,
generated_at     DATETIME DEFAULT CURRENT_TIMESTAMP );
```

## **12.3 Design Decisions** 

- Inspections and Detections are separated — one inspection session contains N bounding boxes. Correct 1:N normalization avoids repeated inspection metadata. 

- Images stored as filesystem paths, not database BLOBs — keeps SQLite file small, images served as Nginx static files. 

- SQLite for hackathon MVP — single file, zero infrastructure. Schema written to be fully PostgreSQLcompatible for production migration. 

- Explanations stored per detection — allows retrieval without re-invoking Gemma 4. Inference is idempotent and results are cached. 

- causes_json stored as TEXT JSON array — avoids a separate causes table while remaining queryable with JSON_EXTRACT in SQLite 3.38+. 

## **13. UI Screen Designs** 

All screens are designed for mobile-first usage (factory floor context) while remaining fully functional on desktop (manager/dashboard context). Design language: high contrast, large touch targets, status indicated by color and icon — not text alone. 

## **Screen 1 — Live Inspection View (Primary Worker Screen)** 

Full-screen camera feed (16:9 ratio). Real-time YOLO bounding boxes overlaid directly on the video frame. Color coding: RED = defect detected / HIGH confidence, AMBER = 📷 MEDIUM reliability, GREY = UNCERTAIN. Bottom drawer (slide-up panel) shows: detected class name, confidence percentage, reliability badge, and three action buttons: ACCEPT (green), REJECT (red), WHY? (blue). Designed for one-handed thumb operation. 

## **Screen 2 — Gemma 4 Explanation Panel** 

💡 

Slides up from bottom as a modal sheet over the camera view. Header: defect name + severity badge (HIGH / MEDIUM / LOW). Body sections: Possible Causes (bulleted list), Repairability (chip: Repairable / Not Repairable), Prevention Tip (highlighted box), Recommended Action (large bold CTA). Footer: 'This explanation is generated by Gemma 4 and logged to your inspection record.' Close button returns to camera view. 

## **Screen 3 — Inspection History** 

Scrollable timeline list of past inspections. Each row: defect type icon, class name, timestamp, confidence badge (color-coded by tier), action chip (ACCEPTED / REJECTED / 📋 ESCALATED). Top filter bar: date picker, defect class dropdown, machine selector, action filter. Tap any row to expand to full inspection detail (Screen 5). Pagination: 20 rows per page with infinite scroll. 

## **Screen 4 — Manager Analytics Dashboard** 

📊 

Top row: 4 KPI cards — Total Inspections Today / Acceptance Rate (%) / Top Defect Class / Shield Triggers (escalations). Middle: Line chart of defect rate over last 7 days (recharts). Bottom: Horizontal bar chart of defect count by class. Side panel (desktop): Table of escalated inspections requiring manager review. Header action: 'Download Shift Report PDF' button. 

## **Screen 5 — Inspection Detail & PDF Report** 

💡 

Full inspection record view. Top: inspection ID, timestamp, worker name, machine name. Centre: image with bounding box overlay rendered in canvas. Below image: detection 

table — class, confidence, reliability tier, action. Gemma explanation if available (expandable card). Footer: 'Download PDF' button triggers /api/v1/report/inspection/{id} — returns ReportLab-generated PDF. 

## **14. MVP Scope — 4-Day Execution Plan** 

The hackathon opened July 6. Today is July 7. Submission deadline is July 11. That is 4 usable working days. The scope below is calibrated to what one solo developer can build, test, and demo in that window. 

|**Day**|**Primary Goal**|**Deliverables**|**Defniton of Done**|
|---|---|---|---|
|Day 1 (July<br>7)|Backend spine —<br>end to end|FastAPI app. /predict endpoint. YOLO<br>model loading from HuggingFace. MC<br>Dropout uncertainty. /explain endpoint<br>calling Gemma 4 via Fireworks API.|/predict returns correct<br>bounding boxes +<br>reliability ter. /explain<br>returns Gemma JSON for a<br>test defect.|
|Day 2 (July<br>8)|Working frontend|React UI with webcam capture. Image<br>sent to /predict. Bounding box overlay on<br>result image. Reliability badge displayed.<br>Gemma panel on 'Why?' tap.|Worker can inspect a part<br>from browser and see AI<br>result + Gemma<br>explanaton end-to-end.|
|Day 3 (July<br>9)|Logging + Reports|SQLite inspecton logging. /inspectons<br>history endpoint. Inspecton history<br>screen. /report/inspecton PDF<br>generaton via ReportLab.|PDF downloads with<br>image, bounding boxes,<br>defect, reliability, and<br>Gemma explanaton.<br>History list shows past 10<br>inspectons.|
|Day 4 (July<br>10–11)|Deploy + Demo +<br>Submit|Docker containerisaton. AMD Cloud<br>deployment. Demo video recording.<br>GitHub README. lablab.ai submission.|App running live on AMD<br>Cloud URL. 3-minute demo<br>video uploaded.<br>Submission complete.|



## **14.1 Features Explicitly Cut from MVP** 

- Voice interaction: adds browser API complexity, low judging impact relative to engineering depth 

- Real-time continuous video stream: replaced by snapshot mode — same demo impact, far simpler 

- Analytics dashboard: inspection history view is sufficient for the demo. Full dashboard is Phase 2. 

- Multi-language support: English only for MVP. Mentioned in roadmap slide as Phase 3. 

- Edge/offline ONNX mode: requires separate model export and service worker. Future scope. 

💡 

Cutting these features is a deliberate product decision, not a shortcut. A polished, fully working core loop (detect → evaluate → explain → log → report) is more impressive than a fragmented demo of 10 half-built features. 

## **15. Future Scope & Product Roadmap** 

|**Feature**|**Business Value**|**Efort**|**Phase**|
|---|---|---|---|
|Analytcs Dashboard|Managers get actonable trend<br>data without manual reportng|Medium|Phase 2|
|Voice Q&A with Gemma 4|Removes literacy barrier —<br>critcal for non-English-reading<br>workers|Medium|Phase 2|
|Real-Time Contnuous Video|True contnuous inspecton vs<br>current snapshot mode|High|Phase 2|
|Edge Ofine Mode (ONNX)|Works in factories with zero<br>internet connectvity|High|Phase 2|
|Hindi / Tamil / Telugu UI|Reaches 90%+ of India's MSME<br>workforce in their natve<br>language|Low|Phase 3|
|ERP Webhook Integraton|SAP/Tally defect push — zero<br>manual data entry for<br>managers|High|Phase 3|
|AI Quality Certfcate|Shipment certfcate signed by<br>AI inspecton hash — OEM<br>diferentator|Low|Phase 3|
|Custom Model Fine-Tuning|Factory uploads own defect<br>images — Nika fne-tunes a<br>custom model|Very High|Phase 4|
|Predictve Maintenance Signal|Defect patern spike →<br>maintenance alert before<br>machine failure|High|Phase 4|
|SaaS Billing (₹999/month)|Per-factory subscripton —<br>sustainable product business|Medium|Phase 4|



## **16. Demo Flow — 3-Minute Script** 

|**Timestamp**|**Acton / Script**|**What Judges See**|
|---|---|---|
|0:00 – 0:30|Opening hook: 'Every MSME factory loses money<br>to missed defects. Industrial vision systems cost<br>$40,000. Nika AI costs nothing — just the phone<br>in your worker's pocket.' Show the problem stat:<br>$2.9T global defect cost.|Stakes set. Real market problem<br>established.|
|0:30 – 1:00|Open Nika AI on smartphone (or browser<br>webcam). Point camera at a defectve steel part.<br>Real-tme bounding box appears: 'Surface Crack<br>— 91% — HIGH confdence — REJECT'. Speak the<br>result.|Live YOLO detecton working in real tme.<br>Not pre-recorded.|
|1:00 – 1:30|Tap 'Why?' buton. Gemma 4 explanaton panel<br>slides up. Read aloud: 'Cause: rapid thermal<br>cycling. Repairability: Not Repairable. Acton:<br>Reject part, inspect adjacent batch.' Close panel.|Gemma 4 integraton live. Structured<br>domain-expert output.|
|1:30 – 2:00|Show borderline part — confdence 48%.<br>Hallucinaton Shield fres: 'UNCERTAIN — Human<br>Review Required'. Explain: 'This is the<br>Hallucinaton Shield. It tells you when NOT to<br>trust the AI. No other system does this.'|Unique diferentator moment. Judges<br>with ML background will immediately<br>recognise MC Dropout uncertainty.|
|2:00 – 2:30|Open inspecton history — 3 logged inspectons<br>visible. Tap one. Click 'Download PDF' —<br>inspecton report opens with image, bounding<br>box, defect, Gemma explanaton.|Complete system demonstrated. Not just<br>a detector — a logged, reportable QC<br>workfow.|
|2:30 – 3:00|Closing: 'Nika AI runs on AMD GPU. Gemma 4 is<br>the reasoning brain. One smartphone. Zero<br>hardware cost. Enterprise-grade quality control<br>for every MSME factory on the planet.'|Clear product vision. AMD and Gemma 4<br>both highlighted for judges. Memorable<br>closing.|



## **17. Why Nika AI Should Win** 

## **17.1 Judging Criteria Alignment** 

|**Judging Criterion**|**Nika AI's Argument**|**Score**|
|---|---|---|
|Innovaton|MC Dropout Hallucinaton Shield + Gemma 4 expert reasoning<br>in an industrial context. No other hackathon project will have<br>this combinaton.|★★★★★|
|Technical Executon|83% mAP YOLOv8 on 29k real images. FastAPI + React +<br>Gemma 4 + SQLite + ReportLab PDF. Full stack, fully working.|★★★★★|
|AMD GPU Usage|Deployed on AMD Developer Cloud. ROCm-compatble<br>inference pipeline using the provided $100 credits.|★★★★☆|
|Gemma 4 Integraton|Gemma 4 is the core reasoning engine — not a chatbot add-<br>on. Central to the product value propositon. Directly targets<br>$6,000 bonus.|★★★★★|
|Real-World Impact|$2.9T global defect cost. 63M MSMEs in India alone. Zero<br>hardware cost. Clear, defensible monetsaton path.|★★★★★|
|Demo Quality|Live webcam → real detecton → real Gemma explanaton →<br>PDF download. Full product loop in 3 minutes.|★★★★★|



## **17.2 The Five Unique Selling Points** 

USP 1 — The Hallucination Shield: Every other submission shows a confidence score. Nika AI shows you when to distrust the AI. MC Dropout uncertainty quantification is graduate🏆 level ML engineering. Judges with ML backgrounds will immediately recognise this as technically significant. 

USP 2 — Gemma 4 as a Domain Expert: Not a chatbot. A manufacturing quality engineer 🏆 with structured output — causes, severity, repairability, prevention, action. Precisely what the $6,000 bonus prize is designed for. 

USP 3 — Real Pre-Trained Model: 29,354 industrial images. 7 datasets merged. 17 defect 🏆 classes. 83% mAP. This is production-ready ML work completed before the hackathon. Not a demo model on 200 images. 

USP 4 — Genuine Market: 63 million MSMEs in India. $40,000 minimum for enterprise 🏆 alternatives. Nika AI's barrier to entry is a smartphone already in the worker's pocket. This is a multi-billion-dollar addressable market. 

🏆 

USP 5 — Complete Product: Detection + uncertainty evaluation + AI explanation + inspection logging + PDF reports + inspection history. A working product, not a proof of concept. 

💡 

## **17.3 The One Moment Judges Will Remember** 

When the Hallucination Shield fires — when the AI says 'I am uncertain, do not trust me on this one' — that moment is singular. Every other project will claim 95% accuracy. Nika AI is honest about its limits. That intellectual honesty is memorable, technically impressive, and practically critical for industrial safety applications where a false rejection is expensive but a false acceptance is dangerous. 

## **17.4 Dual Prize Strategy** 

Nika AI is positioned to win in two prize categories simultaneously: 

- Track 3 (Unicorn): Strongest candidate — full-stack AI application with genuine novelty (Hallucination Shield), real pre-trained model, and a billion-dollar market problem. 

- Bonus: Best Use of Gemma 4: Gemma 4 is not decorative in Nika AI. It is the system's reasoning brain — the element that turns ML output into quality engineering guidance that a factory worker can act on. This is exactly the integration the bonus prize is designed to recognise. 

