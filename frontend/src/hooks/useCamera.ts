/**
 * src/hooks/useCamera.ts
 * ──────────────────────
 * Production-ready camera management hook.
 * Integrates with MediaDevices API and useCameraStore.
 */

import { useCallback, useEffect, useRef } from 'react'
import { useCameraStore } from '../store/cameraStore'
import type { CameraDevice, CameraStatus } from '../types'

export function useCamera() {
  const {
    status,
    devices,
    activeDeviceId,
    stream,
    error,
    setStatus,
    setDevices,
    setActiveDevice,
    setStream,
    setCameraError,
    reset,
  } = useCameraStore()

  const videoRef = useRef<HTMLVideoElement | null>(null)

  // Enumerate available video input devices
  const enumerateDevices = useCallback(async () => {
    try {
      const allDevices = await navigator.mediaDevices.enumerateDevices()
      const videoDevices = allDevices
        .filter((d) => d.kind === 'videoinput')
        .map((d) => ({
          deviceId: d.deviceId,
          label: d.label || `Camera ${d.deviceId.slice(0, 5)}...`,
        }))
      setDevices(videoDevices)
      return videoDevices
    } catch (err) {
      console.warn('Failed to enumerate devices:', err)
      return []
    }
  }, [setDevices])

  // Stop active stream tracks
  const stopStreamTracks = useCallback((streamToStop: MediaStream | null) => {
    if (streamToStop) {
      streamToStop.getTracks().forEach((track) => track.stop())
    }
  }, [])

  // Stop camera action
  const stopCamera = useCallback(() => {
    stopStreamTracks(stream)
    setStream(null)
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setStatus('stopped')
  }, [stream, stopStreamTracks, setStream, setStatus])

  // Start camera action with optional deviceId
  const startCamera = useCallback(
    async (deviceId?: string) => {
      // Clean up previous stream first
      stopStreamTracks(stream)
      setStatus('requesting')
      setCameraError(null)

      const constraints: MediaStreamConstraints = {
        video: deviceId
          ? { deviceId: { exact: deviceId } }
          : { facingMode: 'environment' }, // Default to back camera on mobile
        audio: false,
      }

      try {
        const newStream = await navigator.mediaDevices.getUserMedia(constraints)
        setStream(newStream)
        setStatus('active')

        if (videoRef.current) {
          videoRef.current.srcObject = newStream
        }

        // Re-enumerate to get labels if permission was just granted
        const enumerated = await enumerateDevices()

        // Sync active device ID
        const activeTrack = newStream.getVideoTracks()[0]
        if (activeTrack) {
          const settings = activeTrack.getSettings()
          const matchedDevice = enumerated.find(
            (d) => d.deviceId === settings.deviceId || d.label === activeTrack.label
          )
          setActiveDevice(matchedDevice?.deviceId ?? settings.deviceId ?? null)
        }
      } catch (err: any) {
        let finalStatus: CameraStatus = 'error'
        let errorMessage = 'Could not access camera.'

        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          finalStatus = 'denied'
          errorMessage = 'Camera permission denied.'
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          finalStatus = 'unavailable'
          errorMessage = 'No camera device found.'
        } else {
          errorMessage = err.message || errorMessage
        }

        setStatus(finalStatus)
        setCameraError(errorMessage)
        setStream(null)
      }
    },
    [stream, stopStreamTracks, setStream, setStatus, setCameraError, enumerateDevices, setActiveDevice]
  )

  // Pause camera stream (tracks remain enabled but paused visual output)
  const pauseCamera = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.pause()
      setStatus('paused')
    }
  }, [setStatus])

  // Resume camera stream
  const resumeCamera = useCallback(() => {
    if (videoRef.current && status === 'paused') {
      videoRef.current.play().catch((err) => {
        setCameraError(err.message)
      })
      setStatus('active')
    }
  }, [status, setCameraError, setStatus])

  // Switch camera device
  const switchCamera = useCallback(
    async (deviceId: string) => {
      if (deviceId === activeDeviceId) return
      await startCamera(deviceId)
    },
    [activeDeviceId, startCamera]
  )

  // Auto clean up and check permissions on mount/unmount
  useEffect(() => {
    enumerateDevices()
    return () => {
      // Note: We don't call stopCamera here directly to keep stream active
      // across routes if needed, but for safe auto cleanup of the component:
      // useCamera caller should call stopCamera.
    }
  }, [enumerateDevices])

  return {
    status,
    devices,
    activeDeviceId,
    stream,
    error,
    videoRef,
    startCamera,
    pauseCamera,
    resumeCamera,
    stopCamera,
    switchCamera,
    enumerateDevices,
    reset,
  }
}
