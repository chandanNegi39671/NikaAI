# Sprint 2 — NikaAI Frontend Implementation Plan

## Overview
Build a production-ready **React + Vite + TypeScript + Tailwind CSS + Framer Motion** frontend that faithfully converts the Stitch UI export into reusable React components, connected to the existing FastAPI backend at `http://localhost:8000`.

## Design Analysis

The design folder contains **16 design variants** across 4 core screens + cinematic/v2 alternatives. The canonical screens (source of truth) are:

| Screen | Design File | Route |
|---|---|---|
| Home / Landing | `nika_ai_home/code.html` | `/` |
| Live Inspection (Camera) | `live_inspection/code.html` | `/inspect` |
| AI Copilot Detail | `ai_copilot_detail/code.html` | `/inspect/result` |
| Factory Memory / History | `factory_memory/code.html` | `/history` |
| Manager Dashboard | `manager_dashboard/code.html` | `/dashboard` |

### Design Token System (from Stitch export)
- **Color palette**: Industrial luxury — amber primary (`#fbba64`), orange secondary (`#ff6a00`), dark surface (`#17130d`), deep background (`#0D1117`)
- **Typography**: Inter (body/headlines) + Geist (mono/labels)
- **Icons**: Material Symbols Outlined (Google)
- **Effects**: Glassmorphism cards, rim-light borders, LED pulse animations, copper gradients, scan line animations

### Backend API Contract
- `GET /api/v1/health` — liveness probe (model_loaded, uptime, version)
- `POST /api/v1/predict` — multipart image upload → `{ success, image: {width, height}, detections: [{class, confidence, bounding_box: {x1,y1,x2,y2}}], inference_time_ms }`

---

## Proposed Changes

### Project Scaffold

#### [NEW] `frontend/` (Vite + React + TS + Tailwind)
Bootstrap with `npm create vite@latest . -- --template react-ts`

---

### Configuration Layer

#### [NEW] `frontend/tailwind.config.ts`
Full design token extraction:
- All 30+ colors from Stitch (primary, surface, error, tertiary...)
- Custom spacing (xs/sm/md/base/gutter/xl/margin-mobile/margin-desktop/lg)
- Font families (body-md → Inter, display-mono → Geist, label-sm → Geist)
- Font sizes with line-height + tracking (body-md, headline-lg, display-mono, etc.)
- Border radius (DEFAULT, lg, xl, full)

#### [NEW] `frontend/src/index.css`
- Google Fonts import (Inter + Geist + Material Symbols Outlined)
- Base body styles matching design
- Custom CSS utilities: `.glass-card`, `.glass-panel`, `.rim-light`, `.copper-gradient`, `.led-pulse`, `.scan-effect`, `.gradient-text`, `.magnetic-button`
- Scrollbar styles

---

### API Service Layer

#### [NEW] `frontend/src/lib/api.ts`
Type-safe fetch wrapper:
```ts
// Types
BoundingBox, Detection, PredictResponse, HealthResponse

// Functions
getHealth(): Promise<HealthResponse>
predict(image: File): Promise<PredictResponse>
```

---

### Shared Components

#### [NEW] `frontend/src/components/TopBar.tsx`
Fixed header: NIKA AI logo, nav links (Dashboard/History/Camera), settings icon, avatar. Active-state highlighting per route. Responsive (hides nav on mobile).

#### [NEW] `frontend/src/components/BottomNav.tsx`
Mobile pill nav bar: Camera / History / Dashboard icons. Active state with amber glow + scale animation. Hidden on desktop (`md:hidden`).

#### [NEW] `frontend/src/components/GlassCard.tsx`
Reusable glassmorphism container with optional rim-light top border, custom className prop.

#### [NEW] `frontend/src/components/LedPulse.tsx`
Pulsing dot indicator component with configurable color.

#### [NEW] `frontend/src/components/StatusBadge.tsx`
Pill-style badge component (Critical / Warning / Resolved / Optimal) with correct color coding.

---

### Page Components

#### [NEW] `frontend/src/pages/Home.tsx`
- Hero section: NIKA AI heading (120px), monospaced subtitle, magnetic CTA button → navigates to `/inspect`
- Floating glass stats card (live factory stats: 99.8% accuracy, 12.4k inspected)
- Scroll indicator
- Product story section (2-col grid: text + image with progress bar)
- Bento grid tech specs (3 cards: Predictive Failure Modeling, Vault-Grade Security, Adaptive Learning)
- Footer with nav links
- Framer Motion: `fadeInUp` staggered entrance animations, magnetic button effect

#### [NEW] `frontend/src/pages/LiveInspection.tsx`
- Full-screen camera canvas background (dark bg + circuit board image + scan line animation)
- Bounding box overlays (animated detection boxes from API result)
- Fixed top bar with "Live Feed" pulsing badge
- Left side tabs (Copilot / Memory)
- Status badge (PASS/FAIL + session ID)
- Bottom footer panel: Capture button group (close / main capture / history), glassmorphic info panel (Confidence %, Latency, FPS, Active Profile)
- Mobile bottom nav
- Image upload via `<input type="file">` hidden behind capture button → calls `POST /api/v1/predict` → routes to `/inspect/result`

#### [NEW] `frontend/src/pages/InspectionResult.tsx`  
- Background: grayscale inspection image
- Slide-up glassmorphic bottom sheet (Framer Motion spring animation)
- Root Cause Analysis header with pulsing dot
- Actionable bento grid (Recommendation card with "Log Action" / "Override" buttons + Maintenance Advice card)
- Secondary data row: confidence circle meter, risk indicator, historical refs gallery
- Top bar + bottom nav shared components

#### [NEW] `frontend/src/pages/FactoryMemory.tsx`
- Pattern Discovery section: glass card with defect-frequency progress bars (Scratches 42%, Cracks 28%, Surface Impurities 15%)
- Inspection History timeline with vertical gradient line, timeline dots, glass cards with thumbnail + severity badge + "View Detail" button
- "Load Older Inspections" button
- Uses mock data (populated from API history if available)

#### [NEW] `frontend/src/pages/Dashboard.tsx`
- Factory Overview header + "Download Shift Report PDF" copper-gradient button
- 4 KPI glass cards: Total Inspections, Acceptance Rate, Top Defect, Shield Triggers (connected to `/api/v1/health`)
- Quality Trends SVG area chart (animated, 7D/30D toggle)
- Bottom split: Recent Escalations list (2/3 width) + Shift Intelligence panel (1/3 width)
- Uses mock data + real health API data

---

### State Management

#### [NEW] `frontend/src/store/inspectionStore.ts`
Zustand store:
```ts
{
  lastResult: PredictResponse | null,
  capturedImage: string | null,  // base64 data URL
  isProcessing: boolean,
  sessionId: string,
  history: HistoryEntry[],
}
```

---

### Routing

#### [NEW] `frontend/src/App.tsx`
React Router v6 routes:
```
/           → Home
/inspect    → LiveInspection
/inspect/result → InspectionResult
/history    → FactoryMemory
/dashboard  → Dashboard
```

---

### Assets & Icons

#### [NEW] `frontend/src/components/icons/`
Re-export Material Symbols as inline SVG React components for critical icons, or use the Google Fonts CDN link approach via global CSS.

---

## Verification Plan

### Automated (build check)
```bash
cd frontend && npm run build
```
No TypeScript errors, no Vite build failures.

### Manual Verification
1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Visit `http://localhost:5173` — verify Home page renders identical to design
4. Navigate to `/inspect` — verify camera UI renders, capture button works
5. Upload an image — verify API call to `POST /api/v1/predict`, loading state, bounding box overlays
6. Verify navigation to result page with slide-up animation
7. Verify `/history` timeline and pattern discovery bars
8. Verify `/dashboard` KPI cards and chart
9. Verify mobile responsive layout (BottomNav visible, TopBar nav hidden)
