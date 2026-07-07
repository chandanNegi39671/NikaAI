/**
 * pages/InspectionResult.tsx
 * ───────────────────────────
 * Production-quality AI Inspection Copilot Report.
 * Displays annotated results, confidence chart, root cause diagnostics, and report downloads.
 */

import { useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'

// Stores
import { useInspectionStore } from '../store/inspectionStore'
import { useNotifications } from '../hooks/useNotifications'

// Components
import PredictionCanvas from '../components/PredictionCanvas'
import ConfidenceChart from '../components/ConfidenceChart'

// Utilities
import { downloadInspectionReport, exportToPDF } from '../lib/reportUtils'
import type { Detection } from '../types'

// Helper selectors
function getRootCause(detections: Detection[]): string {
  if (detections.length === 0) return 'Component passed all industrial quality standards. No anomalies detected.'
  const cls = detections[0].class.toLowerCase()
  const causes: Record<string, string> = {
    surface_crack: 'Rapid thermal cooling cycles or micro-fractures in raw ingot processing.',
    crack: 'Fatigue stress from excessive pressure cycles or crystallization flaws.',
    scratch: 'Contact friction against conveyor belts or gripper alignment slippage.',
    pit: 'Localized chemical corrosion, micro-oxidation, or particulate indentation.',
    dent: 'Mechanical impact collision during robotic tool changes or packaging.',
    defect: 'Material impurity or density inconsistency within the alloy batch.',
  }
  return causes[cls] ?? `Surface anomaly located in ${cls.replace(/_/g, ' ')} zone.`
}

function getRiskLevel(confidence: number): 'High' | 'Medium' | 'Low' {
  if (confidence >= 0.82) return 'High'
  if (confidence >= 0.55) return 'Medium'
  return 'Low'
}

function getRecommendation(detections: Detection[]): string {
  if (detections.length === 0) return 'Cleared for production assembly. Route to packaging line.'
  const risk = getRiskLevel(detections[0].confidence)
  if (risk === 'High') return 'Quarantine component immediately. Halt batch flow and isolate serial line.'
  if (risk === 'Medium') return 'Flag component for secondary manual audit. Restrict batch velocity.'
  return 'Mark as safe. Double-check calibration profiles on the next inspection loop.'
}

function getMaintenanceAdvice(detections: Detection[]): string {
  if (detections.length === 0) return 'Calibration profile is nominal. Schedule standard monthly audit.'
  const cls = detections[0].class.toLowerCase()
  if (cls.includes('crack')) return 'Review temperature parameters. Increase hot annealing cycles by 10%.'
  if (cls.includes('scratch')) return 'Calibrate robotic arm vacuum grippers and clear transport paths.'
  if (cls.includes('pit')) return 'Inspect chemical cleaning sprays and coolant filtration grids on Line 2.'
  return 'Execute sensor alignment checks and recalibrate camera aperture offsets.'
}

export default function InspectionResult() {
  const navigate = useNavigate()
  const notify = useNotifications()
  const { lastResult, capturedImageUrl, sessionId, clearSession } = useInspectionStore()

  useEffect(() => {
    if (!lastResult) {
      navigate('/inspect')
    }
  }, [lastResult, navigate])

  if (!lastResult) return null

  const detections = lastResult.detections
  const topDetection = detections[0]
  const confidence = topDetection ? Math.round(topDetection.confidence * 100) : 100
  const rootCause = getRootCause(detections)
  const risk = topDetection ? getRiskLevel(topDetection.confidence) : 'Low'
  const recommendation = getRecommendation(detections)
  const maintenance = getMaintenanceAdvice(detections)
  const hasDefect = detections.length > 0

  const handleExportJSON = () => {
    downloadInspectionReport(lastResult, sessionId)
    notify.success('JSON Report downloaded successfully!')
  }

  const handleExportPDF = () => {
    if (!lastResult.id) {
      notify.error('Cannot generate PDF: No database record found.')
      return
    }
    const link = document.createElement('a')
    link.href = `/api/v1/analytics/report/pdf/${lastResult.id}`
    link.setAttribute('download', `inspection_report_${lastResult.id}.pdf`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    notify.success('PDF report download initiated!')
  }

  return (
    <div className="min-h-screen bg-background text-on-background flex flex-col justify-between overflow-x-hidden">
      
      {/* ── Top Header Bar ────────────────────────────────────────────── */}
      <header className="w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-primary/30 flex justify-between items-center px-margin-mobile h-16 shadow-glass flex-shrink-0">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full border border-primary-fixed-dim overflow-hidden flex items-center justify-center bg-surface-container">
            <span className="material-symbols-outlined text-primary-fixed-dim text-[18px]">security</span>
          </div>
          <h1 className="font-display-mono text-display-mono tracking-widest text-primary-fixed-dim uppercase select-none">
            NIKA AI
          </h1>
        </Link>
        <div className="flex items-center gap-4">
          <span className="font-display-mono text-[10px] text-on-surface-variant/60 uppercase">
            {sessionId}
          </span>
          <span className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors duration-300 cursor-pointer">
            settings
          </span>
        </div>
      </header>

      {/* ── Main Workspace ────────────────────────────────────────────── */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-margin-mobile md:px-margin-desktop py-8 grid grid-cols-1 lg:grid-cols-12 gap-gutter items-start">
        
        {/* Left Side: Annotated Prediction Canvas Card */}
        <section className="lg:col-span-7 flex flex-col gap-6">
          <div className="glass-card rounded-3xl overflow-hidden border border-white/5 shadow-2xl relative">
            <div className="aspect-video w-full bg-black relative flex items-center justify-center">
              <PredictionCanvas
                src={capturedImageUrl}
                detections={detections}
                sourceWidth={lastResult.image.width}
                sourceHeight={lastResult.image.height}
                className="w-full h-full"
              />
            </div>
            
            <div className="p-6 bg-surface-container-low flex justify-between items-center border-t border-white/5">
              <div>
                <p className="font-display-mono text-[9px] text-on-surface-variant/40 uppercase">Image resolution</p>
                <p className="text-xs text-white font-display-mono">
                  {lastResult.image.width}px × {lastResult.image.height}px
                </p>
              </div>
              <div>
                <p className="font-display-mono text-[9px] text-on-surface-variant/40 uppercase">Inference velocity</p>
                <p className="text-xs text-primary font-display-mono">
                  {lastResult.inference_time_ms.toFixed(1)} ms
                </p>
              </div>
            </div>
          </div>

          {/* Action buttons list */}
          <div className="flex gap-4 flex-wrap">
            <button
              onClick={() => {
                clearSession()
                navigate('/inspect')
              }}
              className="flex-1 min-w-[150px] py-3.5 rounded-xl border border-primary/20 text-primary font-label-sm uppercase tracking-wider font-bold hover:bg-primary/10 transition-colors flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">replay</span>
              New Inspection
            </button>

            <button
              onClick={handleExportJSON}
              className="flex-1 min-w-[150px] py-3.5 rounded-xl copper-gradient text-on-primary font-label-sm uppercase tracking-wider font-bold shadow-lg flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">download</span>
              Export JSON Report
            </button>

            <button
              onClick={handleExportPDF}
              className="flex-1 min-w-[150px] py-3.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white font-label-sm uppercase tracking-wider font-bold flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
              Download PDF
            </button>
          </div>
        </section>

        {/* Right Side: Copilot Analysis Bento Details */}
        <section className="lg:col-span-5 flex flex-col gap-6">
          
          {/* Header Analysis block */}
          <div className="glass-card p-6 rounded-3xl border-t border-primary/30">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <p className="font-display-mono text-[9px] text-primary uppercase tracking-widest">
                Root Cause Analysis
              </p>
            </div>
            <h2 className="text-xl text-white font-bold leading-tight capitalize">
              {hasDefect ? topDetection.class.replace(/_/g, ' ') : 'Defect Check Completed'}
            </h2>
            <p className="text-on-surface-variant text-sm mt-3 leading-relaxed">
              {rootCause}
            </p>
          </div>

          {/* Bento Stats row */}
          <div className="grid grid-cols-2 gap-4">
            
            {/* KPI 1: Risk level */}
            <div className="glass-card p-5 rounded-2xl flex flex-col items-center justify-center text-center relative overflow-hidden border border-white/5">
              {hasDefect && <div className="absolute inset-0 bg-error/5 opacity-20 pointer-events-none" />}
              <span
                className={`material-symbols-outlined text-3xl mb-2 ${hasDefect ? 'text-error animate-pulse' : 'text-primary'}`}
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                {hasDefect ? 'warning' : 'verified'}
              </span>
              <p className={`font-headline-lg font-bold text-2xl uppercase ${hasDefect ? 'text-error' : 'text-primary'}`}>
                {risk}
              </p>
              <p className="font-display-mono text-[9px] text-on-surface-variant/60 uppercase mt-1">
                Risk Classification
              </p>
            </div>

            {/* KPI 2: Top confidence percentage */}
            <div className="glass-card p-5 rounded-2xl flex flex-col items-center justify-center text-center border border-white/5">
              <span className="material-symbols-outlined text-primary-fixed-dim text-3xl mb-2">
                speed
              </span>
              <p className="font-headline-lg font-bold text-2xl text-white">
                {confidence}%
              </p>
              <p className="font-display-mono text-[9px] text-on-surface-variant/60 uppercase mt-1">
                Engine Confidence
              </p>
            </div>

          </div>

          {/* Bento grid section: Recommendation, Maintenance, and Confidence Recharts plot */}
          <div className="glass-card p-6 rounded-3xl space-y-6 border border-white/5">
            
            {/* Recommendation */}
            <div>
              <h4 className="font-display-mono text-[10px] text-on-surface-variant/40 uppercase mb-2">
                Operational Recommendation
              </h4>
              <p className="text-white font-semibold text-sm leading-relaxed">
                {recommendation}
              </p>
            </div>

            <div className="h-px bg-white/5" />

            {/* Maintenance Instructions */}
            <div>
              <h4 className="font-display-mono text-[10px] text-on-surface-variant/40 uppercase mb-2">
                Automated Shield Action
              </h4>
              <p className="text-white text-sm leading-relaxed">
                {maintenance}
              </p>
            </div>
          </div>

          {/* Recharts chart component card */}
          {hasDefect && (
            <div className="glass-card p-6 rounded-3xl border border-white/5 flex flex-col">
              <h4 className="font-display-mono text-[10px] text-on-surface-variant/40 uppercase mb-4 text-left">
                Defect confidence breakdown
              </h4>
              <ConfidenceChart detections={detections} />
            </div>
          )}

        </section>

      </main>

      {/* ── Footer Navigation ─────────────────────────────────────────── */}
      <footer className="py-6 border-t border-white/5 bg-surface-dim/40 flex flex-col md:flex-row justify-between items-center gap-4 px-margin-mobile md:px-margin-desktop text-center md:text-left flex-shrink-0">
        <span className="text-[10px] font-display-mono text-on-surface-variant/40">
          © 2026 NIKA INTELLIGENCE SYSTEMS INC.
        </span>
        <span className="text-[10px] font-display-mono text-on-surface-variant/40">
          SYSTEM STATUS: ONLINE
        </span>
      </footer>

      {/* Mobile-only Bottom Navigation */}
      <nav className="fixed bottom-6 left-0 right-0 z-50 flex justify-around items-center h-16
                      max-w-md mx-auto bg-surface-container-low/80 backdrop-blur-[20px]
                      rounded-full border border-primary/20 shadow-glass md:hidden">
        <Link to="/inspect" className="flex flex-col items-center justify-center text-on-surface-variant/60 px-6 py-2 hover:text-primary-fixed transition-all">
          <span className="material-symbols-outlined">photo_camera</span>
          <span className="font-label-sm text-label-sm mt-0.5">Camera</span>
        </Link>
        <Link to="/history" className="flex flex-col items-center justify-center text-on-surface-variant/60 px-6 py-2 hover:text-primary-fixed transition-all">
          <span className="material-symbols-outlined">history</span>
          <span className="font-label-sm text-label-sm mt-0.5">History</span>
        </Link>
        <Link to="/dashboard" className="flex flex-col items-center justify-center text-primary-fixed-dim bg-primary-container/20 rounded-full px-6 py-2 shadow-primary-glow scale-90 transition-all">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-label-sm text-label-sm mt-0.5">Dashboard</span>
        </Link>
      </nav>
    </div>
  )
}
