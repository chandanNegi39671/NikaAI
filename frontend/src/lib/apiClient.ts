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

// ── Response Interceptors ──────────────────────────────────────────────────────

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
