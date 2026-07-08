/**
 * pages/VisualizationViewer.tsx
 * ─────────────────────────────
 * Diagnostic visual overlay screen (renamed from ExplainabilityViewer).
 * Combines camera defect captures, coordinate SVG overlays, trust scoring gauges,
 * and standard defect SOP diagnostic panels.
 */

import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import LedPulse from '../components/LedPulse'
import { getVisualizationReport } from '../lib/apiClient'
import type { VisualizationReport } from '../types'

export default function VisualizationViewer() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<VisualizationReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetchReport(id)
    }
  }, [id])

  const fetchReport = async (inspectionId: string) => {
    try {
      const res = await getVisualizationReport(inspectionId)
      setReport(res)
    } catch (err) {
      console.error('Failed to load visualization report', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-dashed border-primary rounded-full animate-spin" />
        <p className="font-display-mono text-xs text-on-surface-variant uppercase tracking-wider">
          Compiling Diagnostic Heatmap...
        </p>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-background text-on-surface flex flex-col pt-20">
        <TopBar />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <span className="material-symbols-outlined text-[60px] text-error">warning</span>
          <p className="font-display-mono text-sm tracking-wider uppercase">Inference Record Not Found</p>
          <Link to="/history" className="text-xs text-primary underline">Back to History</Link>
        </div>
        <BottomNav />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col pt-20 pb-24 md:pb-8">
      <TopBar />

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 md:px-margin-desktop flex flex-col gap-6">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <span className="font-display-mono text-[11px] text-primary uppercase tracking-widest block mb-1">
              Visualization Engine
            </span>
            <h1 className="font-headline-lg text-2xl text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">analytics</span>
              Visual Diagnostics
            </h1>
          </div>
          
          {/* Simulated explainability warning badge */}
          <div className="flex items-center gap-2 bg-error-container/20 border border-error/30 text-error px-4 py-2 rounded-full">
            <LedPulse active={true} />
            <span className="font-display-mono text-[10px] uppercase font-bold tracking-wider">
              Simulated Explainability
            </span>
          </div>
        </div>

        {/* Diagnostic Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          
          {/* Left panel: SVG Heatmap Coordinate Overlay */}
          <div className="lg:col-span-3 flex flex-col gap-6">
            <GlassCard rimLight className="p-6 border-t border-primary/30 flex flex-col gap-4">
              <div className="flex justify-between items-center pb-3 border-b border-outline-variant/30">
                <span className="font-display-mono text-xs uppercase tracking-wider text-on-surface-variant">
                  Inspection Frame Capture
                </span>
                <span className="text-[10px] font-display-mono text-primary bg-primary-container/20 border border-primary/30 px-2 py-0.5 rounded">
                  {report.status}
                </span>
              </div>

              {/* Render Image overlay with simulated heat spot mapping */}
              <div className="relative aspect-video rounded-xl overflow-hidden border border-outline-variant/20 bg-black/60 shadow-glass">
                <img
                  src={report.inspection_id ? `/static/uploads/default.jpg` : ''} // fallback default visual
                  alt="inspection visual log"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360"><rect width="640" height="360" fill="%23141414"/><text x="320" y="190" fill="%23ece0d6" font-size="14" font-family="monospace" text-anchor="middle">VISUAL ANOMALY CAPTURE FRAME</text></svg>'
                  }}
                />

                {/* SVG Overlay representing heatmap regions */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {report.heatmap_regions.map((region) => (
                    <g key={region.region_id}>
                      {/* Outer diagnostic glow halo */}
                      <circle
                        cx={region.x * 100}
                        cy={region.y * 100}
                        r={region.radius * 120}
                        fill="rgba(251, 186, 100, 0.25)"
                        className="animate-pulse"
                      />
                      {/* Inner defect core bounding center */}
                      <circle
                        cx={region.x * 100}
                        cy={region.y * 100}
                        r={region.radius * 30}
                        fill="rgba(255, 106, 0, 0.65)"
                      />
                      {/* Defect Bounding Square */}
                      <rect
                        x={(region.x - region.radius) * 100}
                        y={(region.y - region.radius) * 100}
                        width={region.radius * 200}
                        height={region.radius * 200}
                        fill="none"
                        stroke="#ffb694"
                        strokeWidth="1.5"
                      />
                      {/* SVG label text details */}
                      <text
                        x={(region.x - region.radius) * 100}
                        y={(region.y - region.radius) * 100 - 2}
                        fill="#ffb694"
                        fontSize="3"
                        fontFamily="monospace"
                      >
                        {region.label.replace('_', ' ').toUpperCase()} ({(region.intensity * 100).toFixed(0)}%)
                      </text>
                    </g>
                  ))}
                </svg>
              </div>

              <div className="flex justify-between items-center text-xs text-on-surface-variant font-display-mono">
                <span>Inference time: <strong>{report.inference_latency_ms.toFixed(1)} ms</strong></span>
                <span>Active Model: <strong>{report.model_metadata.weights_version}</strong></span>
              </div>
            </GlassCard>
          </div>

          {/* Right panel: Trust Scoring & AI reasoning */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <GlassCard rimLight className="p-6 border-t border-primary/30 flex flex-col gap-5">
              
              {/* Trust Score Gauge */}
              <div className="flex flex-col gap-2">
                <span className="font-display-mono text-xs uppercase tracking-wider text-on-surface-variant">
                  Diagnostic Integrity Score
                </span>
                <div className="flex items-baseline gap-2">
                  <h3 className="font-headline-lg text-4xl text-primary font-bold">
                    {(report.trust_score * 100).toFixed(0)}%
                  </h3>
                  <span className="text-xs text-on-surface-variant">Confidence Match</span>
                </div>
                
                {/* Visual score slider bar */}
                <div className="h-1.5 w-full bg-surface-variant/40 rounded-full overflow-hidden mt-1">
                  <div
                    className="h-full bg-primary shadow-primary-glow"
                    style={{ width: `${report.trust_score * 100}%` }}
                  />
                </div>
              </div>

              <div className="border-t border-outline-variant/30 my-1" />

              {/* Accordion detail diagnostic items */}
              <div className="space-y-4">
                <h4 className="font-display-mono text-xs text-primary uppercase tracking-wider">
                  SOP Action Plan
                </h4>

                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-xs font-semibold text-white block">Diagnostic Summary</span>
                    <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                      {report.explanation}
                    </p>
                  </div>

                  {report.structured_reasoning.recommended_action && (
                    <div className="bg-primary-container/10 border border-primary/20 rounded-xl p-3">
                      <span className="text-xs font-display-mono text-primary uppercase font-bold block mb-1">
                        Recommended Action
                      </span>
                      <p className="text-xs text-on-surface leading-relaxed">
                        {report.structured_reasoning.recommended_action}
                      </p>
                    </div>
                  )}

                  {report.structured_reasoning.prevention && (
                    <div className="bg-surface-variant/10 border border-outline-variant/20 rounded-xl p-3">
                      <span className="text-xs font-semibold text-white block mb-1">
                        SOP Prevention Routine
                      </span>
                      <p className="text-xs text-on-surface-variant leading-relaxed">
                        {report.structured_reasoning.prevention}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="border-t border-outline-variant/30 my-1" />

              <Link
                to="/copilot"
                className="font-label-sm text-xs bg-surface-variant/20 hover:bg-surface-variant border border-outline-variant/30 text-primary hover:text-white rounded-full py-3 text-center transition-all cursor-pointer"
              >
                Consult Copilot Assistant
              </Link>
            </GlassCard>
          </div>
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
