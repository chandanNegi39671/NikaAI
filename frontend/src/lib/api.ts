/**
 * src/lib/api.ts
 * ──────────────
 * Backward-compatible re-export layer.
 * Sprint 1/2 code imports from this file — keep it intact.
 * New Sprint 3 code imports directly from '../types' or '../lib/apiClient'.
 */

export type {
  HealthResponse,
  BoundingBox,
  Detection,
  ImageDimensions,
  PredictResponse,
} from '../types'

export { getHealth, predict, default } from './apiClient'
