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

// ── Sprint 7: Maintenance Intelligence Types ───────────────────────────────

export type RiskLevel = 'low' | 'moderate' | 'high' | 'critical'
export type MaintenancePriority = 'low' | 'medium' | 'high' | 'urgent'
export type HealthTrend = 'improving' | 'stable' | 'degrading'

export interface MaintenancePrediction {
  id: string
  machine_id: string | null
  machine_name: string | null
  machine_location: string | null
  health_score: number
  risk_level: RiskLevel
  rul_days: number
  defect_rate: number
  recommendation: string | null
  recommendation_code: string | null
  priority: MaintenancePriority
  trend: HealthTrend
  total_inspections: number
  failed_inspections: number
  computed_at: string | null
  created_at: string | null
}

export interface FleetOverview {
  total_machines: number
  machines_critical: number
  machines_high: number
  machines_moderate: number
  machines_healthy: number
  fleet: MaintenancePrediction[]
}

export interface MachineHistoryResponse {
  machine_id: string
  machine_name: string
  total: number
  predictions: MaintenancePrediction[]
}

export interface TrendDay {
  date: string
  iso_date: string
  total_inspections: number
  failed_inspections: number
  pass_rate: number
  avg_confidence: number
  avg_latency_ms: number
}

export interface TrendWeek {
  week: string
  week_start: string
  week_end: string
  total_inspections: number
  failed_inspections: number
  pass_rate: number
  avg_confidence: number
}

export interface TrendMonth {
  month: string
  month_start: string
  total_inspections: number
  failed_inspections: number
  pass_rate: number
  avg_confidence: number
}

export interface DefectTypeTrend {
  defect_class: string
  defect_name: string
  count: number
  percentage: number
  severity: 'low' | 'moderate' | 'high' | 'critical'
}

export interface MachineTrend {
  machine_id: string
  machine_name: string
  machine_location: string
  total_inspections: number
  failed_inspections: number
  defect_rate: number
  defect_rate_pct: number
  status: 'normal' | 'warning' | 'critical' | 'no_data'
}

export interface TrendSummary {
  period_days: number
  total_inspections: number
  failed_inspections: number
  pass_rate: number
  avg_confidence: number
  avg_latency_ms: number
  machines_at_risk: number
  total_machines: number
  top_defect_class: string | null
  top_defect_name: string
  top_defect_count: number
}

// ── Sprint 8: AI Manufacturing Intelligence Types ─────────────────────────

export interface ModelVersion {
  id: string
  version_name: string
  file_path?: string
  deployment_status: 'training' | 'validated' | 'staging' | 'production' | 'archived'
  map_score?: number
  precision?: number
  recall?: number
  training_date?: string
  dataset_name?: string
  trained_by?: string
  framework?: string
  commit_hash?: string
  artifact_path?: string
  model_size_mb?: number
  parameter_count?: number
  parent_version?: string
  notes?: string
  created_at?: string
}

export interface KnowledgeDocument {
  id: string
  title: string
  content: string
  doc_type: 'manual' | 'sop' | 'faq' | 'maintenance'
  tags?: string
  is_active: boolean
}

export interface ConversationMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface DetectionDetail {
  defect_class: string
  confidence: number
  bounding_box: {
    x1: number
    y1: number
    x2: number
    y2: number
  }
}

export interface InferenceLogItem {
  id: string
  session_id?: string
  machine_id?: string
  machine_name?: string
  worker_name?: string
  shift_name?: string
  image_path?: string
  status: 'PASS' | 'FAIL'
  confidence: number
  inference_time_ms: number
  created_at?: string
  detections: DetectionDetail[]
}

export interface AuditLogItem {
  id: string
  user_id?: string
  username?: string
  action: string
  entity_type?: string
  entity_id?: string
  description?: string
  ip_address?: string
  old_value?: string
  new_value?: string
  request_id?: string
  created_at?: string
}

export interface HeatmapRegion {
  region_id: string
  x: number
  y: number
  radius: number
  intensity: number
  label: string
}

export interface VisualizationReport {
  inspection_id: string
  status: 'PASS' | 'FAIL'
  overall_confidence: number
  inference_latency_ms: number
  trust_score: number
  explanation: string
  structured_reasoning: {
    defect?: string
    severity?: string
    causes?: string[]
    repairability?: string
    prevention?: string
    recommended_action?: string
  }
  visualization_type: 'simulated_explainability'
  heatmap_regions: HeatmapRegion[]
  model_metadata: {
    model_architecture: string
    weights_version: string
    classes: string[]
  }
}

