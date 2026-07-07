/**
 * pages/LiveInspection.tsx
 * ─────────────────────────
 * Enhanced Full-screen Inspection UI. Supports webcam live streaming with real-time YOLO
 * bounding box overlays, parameter tuning, camera selection, and a drag-and-drop file upload interface.
 */

import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

// Hooks
import { useCamera } from '../hooks/useCamera'
import { useInference } from '../hooks/useInference'
import { useImageUpload } from '../hooks/useImageUpload'
import { useBackendHealth } from '../hooks/useBackendHealth'
import { useNotifications } from '../hooks/useNotifications'

// Stores
import { useInspectionStore } from '../store/inspectionStore'
import { useMetricsStore } from '../store/metricsStore'

// Components
import PredictionCanvas from '../components/PredictionCanvas'
import MetricsBar from '../components/MetricsBar'
import ImageUploadZone from '../components/ImageUploadZone'
import LedPulse from '../components/LedPulse'

// API
import { predict } from '../lib/apiClient'
import { fileToDataUrl } from '../lib/imageUtils'

export default function LiveInspection() {
  const navigate = useNavigate()
  const notify = useNotifications()

  // Tabs: 'camera' | 'upload'
  const [activeTab, setActiveTab] = useState<'camera' | 'upload'>('camera')

  // Real-time parameters
  const [inferenceInterval, setInferenceInterval] = useState(1000) // ms
  const [isRealtimeActive, setIsRealtimeActive] = useState(true)

  // Polling backend health regularly
  useBackendHealth({ pollIntervalMs: 10_000 })

  // Pull store data
  const {
    lastResult,
    isProcessing,
    setProcessing,
    setResult,
    setError,
    error: sessionError,
    sessionId,
    modelLoaded,
    backendOnline,
    backendUptime,
  } = useInspectionStore()

  const {
    fps,
    latencyMs,
    inferenceTimeMs,
    detectionCount,
    modelVersion,
  } = useMetricsStore()

  // Hook 1: Camera
  const camera = useCamera()
  const {
    status: camStatus,
    devices: camDevices,
    activeDeviceId,
    videoRef,
    startCamera,
    stopCamera,
    pauseCamera,
    resumeCamera,
    switchCamera,
  } = camera

  // Hook 2: Real-time inference loop
  const inference = useInference({
    videoRef,
    isActive: activeTab === 'camera' && isRealtimeActive && camStatus === 'active',
    intervalMs: inferenceInterval,
    quality: 0.8,
    maxDimension: 640,
  })

  // Hook 3: File uploader pipeline
  const uploader = useImageUpload()
  const { uploaded, processFile, removeImage } = uploader

  // Auto trigger camera when entering camera tab
  useEffect(() => {
    if (activeTab === 'camera') {
      startCamera()
    } else {
      stopCamera()
    }
  }, [activeTab, startCamera, stopCamera])

  // Cleanup stream on unmount
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [stopCamera])

  // Handle manual capture in live stream
  const handleManualCapture = async () => {
    const video = videoRef.current
    if (!video || camStatus !== 'active' || isProcessing) return

    setProcessing(true)
    setError(null)
    notify.info('Capturing inspection snapshot...')

    try {
      // Create canvas snapshot
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Could not initialize capture canvas context')

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      
      // Convert to blob
      canvas.toBlob(async (blob) => {
        if (!blob) {
          setError('Failed to capture frame.')
          setProcessing(false)
          return
        }

        try {
          const res = await predict(blob)
          const dataUrl = await fileToDataUrl(blob)
          setResult(res, dataUrl)
          notify.success('Snapshot analyzed successfully!')
          navigate('/inspect/result')
        } catch (err: any) {
          setError(err.message || 'Capture analysis failed.')
          notify.error('Analysis failed', err.message)
        }
      }, 'image/jpeg', 0.9)

    } catch (err: any) {
      setError(err.message)
      setProcessing(false)
      notify.error('Capture failed', err.message)
    }
  }

  // Trigger GPU inference on uploaded image file
  const handleUploadScan = async () => {
    if (!uploaded || uploaded.status !== 'ready' || isProcessing) return

    setProcessing(true)
    setError(null)
    notify.info('Analyzing uploaded target...')

    const fileToUpload = uploaded.compressedBlob || uploaded.file

    try {
      const res = await predict(fileToUpload)
      setResult(res, uploaded.previewUrl)
      notify.success('Defect scan completed!')
      navigate('/inspect/result')
    } catch (err: any) {
      setError(err.message || 'Defect analysis failed.')
      setProcessing(false)
      notify.error('Scan failed', err.message)
    }
  }

  return (
    <div className="relative w-full h-screen overflow-hidden bg-black flex flex-col justify-between">
      
      {/* ── Top Header ────────────────────────────────────────────────── */}
      <header className="w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-primary/30 flex justify-between items-center px-margin-mobile h-16 shadow-glass flex-shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full border border-primary/40 p-0.5 overflow-hidden flex items-center justify-center bg-surface-container">
              <span className="material-symbols-outlined text-primary-fixed-dim text-[20px]">engineering</span>
            </div>
            <h1 className="font-display-mono text-display-mono tracking-widest text-primary-fixed-dim select-none">
              NIKA AI
            </h1>
          </Link>
        </div>

        {/* Tab switchers */}
        <div className="flex bg-surface-container-high/60 border border-white/5 rounded-full p-1 max-w-xs">
          <button
            onClick={() => setActiveTab('camera')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-label-sm text-[11px] uppercase tracking-wider transition-all duration-300 ${
              activeTab === 'camera'
                ? 'bg-primary text-on-primary shadow-lg font-bold'
                : 'text-on-surface-variant hover:text-white'
            }`}
          >
            <span className="material-symbols-outlined text-sm">photo_camera</span>
            Live Stream
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-full font-label-sm text-[11px] uppercase tracking-wider transition-all duration-300 ${
              activeTab === 'upload'
                ? 'bg-primary text-on-primary shadow-lg font-bold'
                : 'text-on-surface-variant hover:text-white'
            }`}
          >
            <span className="material-symbols-outlined text-sm">cloud_upload</span>
            Upload File
          </button>
        </div>

        {/* Status indicator info */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
            <LedPulse size="sm" color={camStatus === 'active' ? 'primary' : 'error'} />
            <span className="font-label-sm text-[10px] text-primary uppercase font-display-mono">
              {camStatus === 'active' ? 'Feed Connected' : 'Feed Inactive'}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Workspace Canvas ────────────────────────────────────── */}
      <main className="flex-1 w-full relative flex items-center justify-center p-4">
        
        {/* Session ID display */}
        <div className="absolute top-4 left-6 z-20 glass-panel border border-white/10 px-3 py-1.5 rounded-lg text-left hidden md:block">
          <p className="text-[9px] font-display-mono text-on-surface-variant/60 uppercase">Session ID</p>
          <p className="text-xs font-display-mono text-white font-bold">{sessionId}</p>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'camera' ? (
            /* Tab 1: Live Webcam Pipeline */
            <motion.div
              key="camera-tab"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="w-full h-full max-w-4xl max-h-[70vh] rounded-2xl overflow-hidden border border-primary/10 bg-surface-container-lowest relative flex items-center justify-center"
            >
              {camStatus === 'denied' && (
                <div className="p-6 text-center z-10 max-w-sm">
                  <span className="material-symbols-outlined text-error text-6xl mb-3">block</span>
                  <h3 className="font-headline-lg-mobile text-white mb-2">Camera Access Blocked</h3>
                  <p className="text-on-surface-variant text-sm mb-6 leading-relaxed">
                    Camera permissions were declined. Please check site permissions in your browser address bar.
                  </p>
                  <button
                    onClick={() => startCamera()}
                    className="px-6 py-2.5 rounded-full copper-gradient text-on-primary font-label-sm uppercase tracking-wider font-bold"
                  >
                    Request Permissions
                  </button>
                </div>
              )}

              {camStatus === 'unavailable' && (
                <div className="p-6 text-center z-10 max-w-sm">
                  <span className="material-symbols-outlined text-error text-6xl mb-3">videocam_off</span>
                  <h3 className="font-headline-lg-mobile text-white mb-2">No Camera Found</h3>
                  <p className="text-on-surface-variant text-sm mb-6 leading-relaxed">
                    We could not find an active camera device on your system. Connect a webcam and try again.
                  </p>
                  <button
                    onClick={() => startCamera()}
                    className="px-6 py-2.5 rounded-full copper-gradient text-on-primary font-label-sm uppercase tracking-wider font-bold"
                  >
                    Detect Webcam
                  </button>
                </div>
              )}

              {camStatus === 'requesting' && (
                <div className="text-center z-10 flex flex-col items-center">
                  <span className="material-symbols-outlined text-primary animate-spin text-4xl mb-2">
                    sync
                  </span>
                  <p className="text-on-surface font-display-mono text-xs uppercase tracking-wider">
                    Initializing Video Pipeline...
                  </p>
                </div>
              )}

              {/* Active webcam display & overlays */}
              {camStatus === 'active' && (
                <PredictionCanvas
                  src={null}
                  videoRef={videoRef}
                  detections={lastResult ? lastResult.detections : []}
                  sourceWidth={videoRef.current?.videoWidth || 640}
                  sourceHeight={videoRef.current?.videoHeight || 480}
                  className="w-full h-full"
                />
              )}

              {/* Video control toolbar */}
              {camStatus === 'active' && (
                <div className="absolute top-4 right-4 z-20 flex gap-2">
                  {/* Select camera if multiple exist */}
                  {camDevices.length > 1 && (
                    <select
                      value={activeDeviceId || ''}
                      onChange={(e) => switchCamera(e.target.value)}
                      className="bg-black/60 border border-white/10 text-white font-display-mono text-[10px] px-3 py-1.5 rounded-lg outline-none cursor-pointer"
                    >
                      {camDevices.map((d) => (
                        <option key={d.deviceId} value={d.deviceId}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  )}

                  {/* Pause / Resume */}
                  <button
                    onClick={() => (isRealtimeActive ? setIsRealtimeActive(false) : setIsRealtimeActive(true))}
                    className="w-9 h-9 rounded-lg bg-black/60 border border-white/10 text-white flex items-center justify-center hover:bg-black/80 transition-colors"
                    title={isRealtimeActive ? 'Pause loop' : 'Resume loop'}
                  >
                    <span className="material-symbols-outlined text-[20px]">
                      {isRealtimeActive ? 'pause' : 'play_arrow'}
                    </span>
                  </button>
                </div>
              )}

              {/* Scanline overlay animation */}
              {camStatus === 'active' && isRealtimeActive && (
                <div className="scan-effect" />
              )}
            </motion.div>
          ) : (
            /* Tab 2: Upload File Pipeline */
            <motion.div
              key="upload-tab"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="w-full max-w-xl text-center space-y-6"
            >
              <ImageUploadZone
                uploaded={uploaded}
                onFileSelect={processFile}
                onRemove={removeImage}
                isProcessing={isProcessing}
              />

              {/* Upload scan trigger */}
              {uploaded?.status === 'ready' && (
                <motion.button
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  onClick={handleUploadScan}
                  disabled={isProcessing}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-sm uppercase tracking-wider font-bold shadow-primary-glow flex items-center justify-center gap-2"
                >
                  {isProcessing ? (
                    <>
                      <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
                      Running Deep GPU Defect Analysis...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[18px]">verified</span>
                      Execute GPU Defect Scan
                    </>
                  )}
                </motion.button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* ── Footer Panel & Tuning Controls ───────────────────────────── */}
      <div className="w-full z-40 bg-gradient-to-t from-black via-black/90 to-transparent p-4 md:p-6 flex flex-col items-center gap-4 flex-shrink-0">
        
        {/* Controls layout: Live controls / capture / upload fallbacks */}
        {activeTab === 'camera' && camStatus === 'active' && (
          <div className="w-full max-w-4xl flex flex-col md:flex-row items-center justify-between gap-4 border-b border-white/5 pb-4 mb-2">
            
            {/* Interval tuning slider */}
            <div className="flex items-center gap-4 w-full md:w-auto">
              <span className="font-label-sm text-[10px] text-on-surface-variant/60 uppercase font-display-mono">
                Scan Rate ({inferenceInterval}ms):
              </span>
              <input
                type="range"
                min={500}
                max={5000}
                step={250}
                value={inferenceInterval}
                onChange={(e) => setInferenceInterval(Number(e.target.value))}
                className="flex-1 md:w-48 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-primary"
              />
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-4 w-full md:w-auto justify-end">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={handleManualCapture}
                disabled={isProcessing}
                className="w-full md:w-auto px-6 py-2.5 rounded-full copper-gradient text-on-primary font-label-sm uppercase tracking-wider font-bold shadow-lg flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">photo_camera</span>
                Capture Snapshot
              </motion.button>
            </div>
          </div>
        )}

        {/* Global error message toast banner */}
        {sessionError && (
          <div className="bg-error-container/30 border border-error/30 text-error px-4 py-2 rounded-xl text-xs font-display-mono mb-2">
            {sessionError}
          </div>
        )}

        {/* Bottom KPIs indicators bar */}
        <div className="w-full max-w-4xl">
          <MetricsBar
            fps={fps}
            latencyMs={latencyMs}
            inferenceTimeMs={inferenceTimeMs}
            detectionCount={detectionCount}
            backendOnline={backendOnline}
            modelLoaded={modelLoaded}
            modelVersion={modelVersion}
            isLive={activeTab === 'camera' && isRealtimeActive && camStatus === 'active'}
          />
        </div>
      </div>

      {/* ── Bottom Mobile Navigation ──────────────────────────────────── */}
      <nav className="fixed bottom-6 left-0 right-0 z-50 flex justify-around items-center h-16
                      max-w-md mx-auto bg-surface-container-low/80 backdrop-blur-[20px]
                      rounded-full border border-primary/20 shadow-glass md:hidden">
        <Link to="/inspect" className="flex flex-col items-center justify-center text-primary-fixed-dim bg-primary-container/20 rounded-full px-6 py-2 shadow-primary-glow scale-90 transition-all">
          <span className="material-symbols-outlined">photo_camera</span>
          <span className="font-label-sm text-label-sm mt-0.5">Camera</span>
        </Link>
        <Link to="/history" className="flex flex-col items-center justify-center text-on-surface-variant/60 px-6 py-2 hover:text-primary-fixed transition-all">
          <span className="material-symbols-outlined">history</span>
          <span className="font-label-sm text-label-sm mt-0.5">History</span>
        </Link>
        <Link to="/dashboard" className="flex flex-col items-center justify-center text-on-surface-variant/60 px-6 py-2 hover:text-primary-fixed transition-all">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-label-sm text-label-sm mt-0.5">Dashboard</span>
        </Link>
      </nav>
    </div>
  )
}
