/**
 * src/lib/apiClient.ts
 * ─────────────────────
 * Production-quality Axios client with:
 *  - Request/response interceptors
 *  - Automatic retry (3x exponential backoff)
 *  - AbortController cancellation support
 *  - 30s request timeout
 *  - Typed error normalization
 *  - Central loading flag (via metricsStore)
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosError } from 'axios'
import type { HealthResponse, PredictResponse } from '../types'

// ── Axios Instance ─────────────────────────────────────────────────────────────

const apiClient: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
})

// ── Normalized API Error ───────────────────────────────────────────────────────

export class ApiError extends Error {
  public readonly status: number
  public readonly code: string

  constructor(message: string, status: number, code = 'UNKNOWN') {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

// ── Error Normalizer ──────────────────────────────────────────────────────────

function normalizeError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const axiosErr = err as AxiosError<{ detail?: string; message?: string }>
    if (axiosErr.response) {
      const status = axiosErr.response.status
      const detail =
        axiosErr.response.data?.detail ??
        axiosErr.response.data?.message ??
        `Request failed with status ${status}`
      return new ApiError(detail, status, axiosErr.code ?? 'HTTP_ERROR')
    }
    if (axiosErr.code === 'ERR_CANCELED') {
      return new ApiError('Request cancelled', 0, 'CANCELLED')
    }
    if (axiosErr.code === 'ECONNABORTED') {
      return new ApiError('Request timed out. Backend may be unavailable.', 0, 'TIMEOUT')
    }
    return new ApiError('Network error. Check backend connection.', 0, 'NETWORK_ERROR')
  }
  if (err instanceof Error) {
    return new ApiError(err.message, 0, 'UNKNOWN')
  }
  return new ApiError('An unexpected error occurred', 0, 'UNKNOWN')
}

// ── Retry Logic ────────────────────────────────────────────────────────────────

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

async function withRetry<T>(
  fn: () => Promise<T>,
  retries = 2,
  baseDelayMs = 500,
): Promise<T> {
  let lastErr: unknown
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn()
    } catch (err) {
      const normalized = normalizeError(err)
      // Don't retry on cancellations or 4xx client errors
      if (
        normalized.code === 'CANCELLED' ||
        (normalized.status >= 400 && normalized.status < 500)
      ) {
        throw normalized
      }
      lastErr = normalized
      if (attempt < retries) {
        await sleep(baseDelayMs * 2 ** attempt)
      }
    }
  }
  throw normalizeError(lastErr)
}

// ── Request & Response Interceptors ────────────────────────────────────────────

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('nika_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    throw normalizeError(err)
  },
)

// ── API Functions ──────────────────────────────────────────────────────────────

/**
 * GET /api/v1/health
 * Returns liveness and model-readiness information.
 */
export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return withRetry(async () => {
    const res = await apiClient.get<HealthResponse>('/health', { signal })
    return res.data
  })
}

/**
 * POST /api/v1/predict
 * Uploads an image and returns YOLOv8 defect detections.
 *
 * @param image   - File or Blob (JPEG / PNG / WEBP, max 10 MB)
 * @param signal  - Optional AbortController signal for cancellation
 */
export async function predict(
  image: File | Blob,
  signal?: AbortSignal,
  config?: AxiosRequestConfig,
): Promise<PredictResponse> {
  const formData = new FormData()
  formData.append('image', image)

  const res = await apiClient.post<PredictResponse>('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal,
    ...config,
  })
  return res.data
}

/**
 * GET /api/v1/inspections
 * List historical inspections with paginated filtering.
 */
export async function getInspections(params?: {
  status_filter?: string
  machine_id?: string
  worker_id?: string
  limit?: number
  offset?: number
}): Promise<{ total: number; results: any[] }> {
  const res = await apiClient.get('/inspections', { params })
  return res.data
}

/**
 * GET /api/v1/inspections/{id}
 * Retrieve details for a specific inspection.
 */
export async function getInspectionDetails(id: string): Promise<any> {
  const res = await apiClient.get(`/inspections/${id}`)
  return res.data
}

/**
 * DELETE /api/v1/inspections/{id}
 * Soft-delete an inspection.
 */
export async function deleteInspection(id: string): Promise<any> {
  const res = await apiClient.delete(`/inspections/${id}`)
  return res.data
}

/**
 * GET /api/v1/analytics/dashboard
 * Retrieve aggregated analytics and KPIs.
 */
export async function getDashboardAnalytics(): Promise<any> {
  const res = await apiClient.get('/analytics/dashboard')
  return res.data
}

/**
 * GET /api/v1/factory-memory
 * List defect patterns guidelines.
 */
export async function getFactoryMemories(query?: string): Promise<any[]> {
  const res = await apiClient.get('/factory-memory', { params: { query } })
  return res.data
}

/**
 * GET /api/v1/machines
 * List all factory machines.
 */
export async function getMachines(): Promise<any[]> {
  const res = await apiClient.get('/machines')
  return res.data
}

/**
 * GET /api/v1/workers
 * List all active workers.
 */
export async function getWorkers(): Promise<any[]> {
  const res = await apiClient.get('/workers')
  return res.data
}

export { normalizeError }
export default apiClient

// ── Sprint 7: Maintenance Intelligence API ─────────────────────────────────

import type {
  FleetOverview,
  MaintenancePrediction,
  MachineHistoryResponse,
  TrendDay,
  TrendWeek,
  TrendMonth,
  DefectTypeTrend,
  MachineTrend,
  TrendSummary,
} from '../types'

/**
 * GET /api/v1/maintenance/fleet
 * Returns the latest health prediction for every machine in the fleet.
 */
export async function getFleetOverview(): Promise<FleetOverview> {
  const res = await apiClient.get<FleetOverview>('/maintenance/fleet')
  return res.data
}

/**
 * GET /api/v1/maintenance/predict/{machine_id}
 * Runs the maintenance engine for a machine and persists the result.
 */
export async function predictMachineHealth(machineId: string): Promise<MaintenancePrediction> {
  const res = await apiClient.get<MaintenancePrediction>(`/maintenance/predict/${machineId}`)
  return res.data
}

/**
 * GET /api/v1/maintenance/history/{machine_id}
 * Returns paginated prediction history for a machine.
 */
export async function getMachineMaintenanceHistory(
  machineId: string,
  limit = 30,
  offset = 0,
): Promise<MachineHistoryResponse> {
  const res = await apiClient.get<MachineHistoryResponse>(
    `/maintenance/history/${machineId}`,
    { params: { limit, offset } },
  )
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/daily
 * Returns daily inspection trend data.
 */
export async function getDailyTrend(days = 30): Promise<TrendDay[]> {
  const res = await apiClient.get<TrendDay[]>('/maintenance/trend/daily', { params: { days } })
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/weekly
 * Returns weekly aggregated trend data.
 */
export async function getWeeklyTrend(weeks = 12): Promise<TrendWeek[]> {
  const res = await apiClient.get<TrendWeek[]>('/maintenance/trend/weekly', { params: { weeks } })
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/monthly
 * Returns monthly aggregated trend data.
 */
export async function getMonthlyTrend(months = 6): Promise<TrendMonth[]> {
  const res = await apiClient.get<TrendMonth[]>('/maintenance/trend/monthly', { params: { months } })
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/defects
 * Returns defect type frequency for the specified period.
 */
export async function getDefectTypeTrend(days = 30): Promise<DefectTypeTrend[]> {
  const res = await apiClient.get<DefectTypeTrend[]>('/maintenance/trend/defects', { params: { days } })
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/machines
 * Returns per-machine failure trend.
 */
export async function getMachineTrend(days = 30): Promise<MachineTrend[]> {
  const res = await apiClient.get<MachineTrend[]>('/maintenance/trend/machines', { params: { days } })
  return res.data
}

/**
 * GET /api/v1/maintenance/trend/summary
 * Returns fleet-wide KPI summary.
 */
export async function getTrendSummary(days = 30): Promise<TrendSummary> {
  const res = await apiClient.get<TrendSummary>('/maintenance/trend/summary', { params: { days } })
  return res.data
}

// ── Sprint 8: AI Manufacturing Intelligence API ───────────────────────────

import type {
  ModelVersion,
  KnowledgeDocument,
  ConversationMessage,
  InferenceLogItem,
  AuditLogItem,
  VisualizationReport
} from '../types'

/**
 * POST /api/v1/assistant/ask
 * Ask Factory Copilot a question with history session tracking.
 */
export async function askCopilot(question: string, sessionKey?: string): Promise<{
  question: string
  answer: string
  sources: string[]
  adapter: string
  confidence: number
}> {
  const res = await apiClient.post('/assistant/ask', { question, session_key: sessionKey })
  return res.data
}

/**
 * GET /api/v1/assistant/history/{session_key}
 * Retrieve chat history for session.
 */
export async function getCopilotHistory(sessionKey: string): Promise<ConversationMessage[]> {
  const res = await apiClient.get(`/assistant/history/${sessionKey}`)
  return res.data
}

/**
 * DELETE /api/v1/assistant/history/{session_key}
 * Clear chat history.
 */
export async function clearCopilotHistory(sessionKey: string): Promise<any> {
  const res = await apiClient.delete(`/assistant/history/${sessionKey}`)
  return res.data
}

/**
 * GET /api/v1/models
 * Fetch all model version checkpoints inside model registry database.
 */
export async function listModelVersions(): Promise<{ models: ModelVersion[] }> {
  const res = await apiClient.get('/models')
  return res.data
}

/**
 * POST /api/v1/models/register
 * Register a new model version entry.
 */
export async function registerModelVersion(data: Partial<ModelVersion>): Promise<ModelVersion> {
  const res = await apiClient.post('/models/register', data)
  return res.data
}

/**
 * POST /api/v1/models/switch
 * Switch weights and promote model version.
 */
export async function switchModelVersion(versionName: string): Promise<{ success: boolean, detail: string }> {
  const res = await apiClient.post('/models/switch', null, { params: { version_name: versionName } })
  return res.data
}

/**
 * POST /api/v1/models/status
 * Update model status.
 */
export async function updateModelStatus(versionName: string, status: string): Promise<ModelVersion> {
  const res = await apiClient.post('/models/status', { version_name: versionName, status })
  return res.data
}

/**
 * GET /api/v1/inference/history
 * Fetch paginated visual log log list.
 */
export async function getInferenceHistory(params?: {
  machine_id?: string
  worker_id?: string
  shift_id?: string
  date_from?: string
  date_to?: string
  min_confidence?: number
  defect_class?: string
  status?: string
  limit?: number
  offset?: number
}): Promise<{ total: number; results: InferenceLogItem[] }> {
  const res = await apiClient.get('/inference/history', { params })
  return res.data
}

/**
 * GET /api/v1/inference/history/{id}
 * Fetch detail inspection info.
 */
export async function getInferenceDetails(id: string): Promise<InferenceLogItem> {
  const res = await apiClient.get(`/inference/history/${id}`)
  return res.data
}

/**
 * GET /api/v1/audit
 * Fetch paginated compliance audit logs.
 */
export async function getAuditLogs(params?: {
  date_from?: string
  date_to?: string
  user_id?: string
  action?: string
  ip_address?: string
  entity_type?: string
  request_id?: string
  limit?: number
  offset?: number
}): Promise<{ total: number; results: AuditLogItem[] }> {
  const res = await apiClient.get('/audit', { params })
  return res.data
}

/**
 * GET /api/v1/visualization/report/{inspection_id}
 * Retrieve structured diagnostic heatmap coordinates.
 */
export async function getVisualizationReport(inspectionId: string): Promise<VisualizationReport> {
  const res = await apiClient.get(`/visualization/report/${inspectionId}`)
  return res.data
}

