/**
 * src/hooks/useBackendHealth.ts
 * ─────────────────────────────
 * Custom hook to poll the FastAPI backend health endpoint.
 * Syncs online status, model loading, and uptime to metricsStore and inspectionStore.
 */

import { useEffect, useCallback, useRef } from 'react'
import { getHealth } from '../lib/apiClient'
import { useMetricsStore } from '../store/metricsStore'
import { useInspectionStore } from '../store/inspectionStore'

interface HealthOptions {
  pollIntervalMs?: number
}

export function useBackendHealth({ pollIntervalMs = 15_000 }: HealthOptions = {}) {
  const setBackendStatus = useMetricsStore((s) => s.setBackendStatus)
  const { setHealthStatus, setBackendOnline } = useInspectionStore()
  const timerRef = useRef<any>(null)
  const isRequestingRef = useRef(false)

  const checkHealth = useCallback(async () => {
    if (isRequestingRef.current) return
    isRequestingRef.current = true

    try {
      const h = await getHealth()
      setBackendStatus(true, h.model_loaded, h.uptime, h.version)
      setHealthStatus(h.model_loaded, h.uptime)
      setBackendOnline(true)
    } catch (err) {
      setBackendStatus(false, false, '--')
      setHealthStatus(false, '--')
      setBackendOnline(false)
    } finally {
      isRequestingRef.current = false
    }
  }, [setBackendStatus, setHealthStatus, setBackendOnline])

  useEffect(() => {
    // Initial health check
    checkHealth()

    // Poll interval
    timerRef.current = setInterval(() => {
      checkHealth()
    }, pollIntervalMs)

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [checkHealth, pollIntervalMs])

  return {
    checkHealth,
  }
}
