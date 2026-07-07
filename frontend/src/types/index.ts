/**
 * src/types/index.ts
 * ──────────────────
 * Central shared TypeScript interfaces for the entire NikaAI frontend.
 * All API types, store types, component prop types and domain models live here.
 */

// ── API / Backend Types ────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  service: string
  version: string
  model_loaded: boolean
  uptime: string
}

export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface Detection {
  class: string
  confidence: number
  bounding_box: BoundingBox
}

export interface ImageDimensions {
  width: number
  height: number
}

export interface PredictResponse {
  success: boolean
  id?: string
  image: ImageDimensions
  detections: Detection[]
  inference_time_ms: number
}

// ── Inspection / History Domain ────────────────────────────────────────────────

export type Severity = 'Critical' | 'Warning' | 'Resolved'

export interface HistoryEntry {
  id: string
  timestamp: string
  severity: Severity
  defectName: string
  imageDataUrl: string | null
  result: PredictResponse | null
  inferenceTimeMs?: number
  latencyMs?: number
}

export interface InspectionSession {
  id: string
  startTime: number
  mode: 'camera' | 'upload'
  imageUrl: string | null
  result: PredictResponse | null
  isProcessing: boolean
  error: string | null
}

// ── Camera State ───────────────────────────────────────────────────────────────

export type CameraStatus =
  | 'idle'
  | 'requesting'
  | 'active'
  | 'paused'
  | 'stopped'
  | 'denied'
  | 'unavailable'
  | 'error'

export interface CameraDevice {
  deviceId: string
  label: string
}

export interface CameraState {
  status: CameraStatus
  devices: CameraDevice[]
  activeDeviceId: string | null
  stream: MediaStream | null
  error: string | null
}

// ── Metrics State ──────────────────────────────────────────────────────────────

export interface MetricsSnapshot {
  fps: number
  latencyMs: number
  inferenceTimeMs: number
  frameCount: number
  detectionCount: number
  overallStatus: 'PASS' | 'FAIL' | 'IDLE'
  backendOnline: boolean
  modelLoaded: boolean
  backendUptime: string
  modelVersion: string
  lastUpdated: number
}

// ── Notification Types ─────────────────────────────────────────────────────────

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message?: string
  durationMs?: number
  timestamp: number
}

// ── Upload Types ───────────────────────────────────────────────────────────────

export type UploadStatus = 'idle' | 'dragging' | 'validating' | 'compressing' | 'ready' | 'error'

export interface UploadedImage {
  file: File
  previewUrl: string
  compressedBlob: Blob | null
  sizeBytes: number
  compressedSizeBytes: number | null
  status: UploadStatus
  error: string | null
}

// ── Bounding Box Rendering ─────────────────────────────────────────────────────

export interface RenderedBox {
  detection: Detection
  left: number
  top: number
  width: number
  height: number
  isPrimary: boolean
  color: string
  labelColor: string
}

// ── Analytics / Dashboard ──────────────────────────────────────────────────────

export interface DailyStats {
  date: string
  totalInspections: number
  defectCount: number
  avgConfidence: number
  avgLatencyMs: number
  passRate: number
}

export interface DefectFrequency {
  class: string
  count: number
  pct: number
}
