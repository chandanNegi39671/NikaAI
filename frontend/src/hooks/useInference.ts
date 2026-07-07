/**
 * src/hooks/useInference.ts
 * ─────────────────────────
 * Continuous real-time inference loop hook.
 * Captures frames from a video element, compresses them, and calls predict API.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { predict } from '../lib/apiClient'
import { useMetricsStore } from '../store/metricsStore'
import { useInspectionStore } from '../store/inspectionStore'
import { captureFrame } from '../lib/imageUtils'

interface UseInferenceOptions {
  videoRef: React.RefObject<HTMLVideoElement | null>
  isActive: boolean
  intervalMs?: number // Adjustable interval
  quality?: number
  maxDimension?: number
}

export function useInference({
  videoRef,
  isActive,
  intervalMs = 1000,
  quality = 0.75,
  maxDimension = 640,
}: UseInferenceOptions) {
  const [isLooping, setIsLooping] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const timerRef = useRef<any>(null)
  const isFetchingRef = useRef(false)

  const recordInferenceResult = useMetricsStore((s) => s.recordInferenceResult)
  const { setResult, setError } = useInspectionStore()

  // Single iteration step
  const executeStep = useCallback(async () => {
    const video = videoRef.current
    if (!video || video.paused || video.ended || isFetchingRef.current) {
      return
    }

    isFetchingRef.current = true
    const startTime = Date.now()

    // Create fresh AbortController for this request
    abortControllerRef.current = new AbortController()

    try {
      // 1. Capture and compress frame
      const frameBlob = await captureFrame(video, quality, maxDimension)

      // 2. Call backend API
      const result = await predict(frameBlob, abortControllerRef.current.signal)

      const latencyMs = Date.now() - startTime

      // 3. Update Metrics and Result stores
      recordInferenceResult({
        inferenceTimeMs: result.inference_time_ms,
        latencyMs,
        detectionCount: result.detections.length,
      })

      // Convert frame Blob to object URL or data URL for rendering overlays
      const objectUrl = URL.createObjectURL(frameBlob)
      setResult(result, objectUrl)
    } catch (err: any) {
      if (err.name === 'AbortError' || err.code === 'CANCELLED') {
        // Ignored
      } else {
        setError(err.message || 'Real-time inference failed.')
      }
    } finally {
      isFetchingRef.current = false
    }
  }, [videoRef, quality, maxDimension, recordInferenceResult, setResult, setError])

  // Setup loop
  useEffect(() => {
    if (!isActive) {
      setIsLooping(false)
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
      isFetchingRef.current = false
      return
    }

    setIsLooping(true)

    // Trigger immediately first
    executeStep()

    // Setup interval
    timerRef.current = setInterval(() => {
      executeStep()
    }, intervalMs)

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
    }
  }, [isActive, intervalMs, executeStep])

  return {
    isLooping,
    isProcessing: isFetchingRef.current,
  }
}
