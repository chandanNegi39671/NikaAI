/**
 * pages/FactoryMemory.tsx
 * ────────────────────────
 * Production-ready Factory Memory & Inspection History.
 * Supports chronological timeline view, full sorting, search, filtering, and pattern insights.
 */

import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

// Stores / Components
import { useInspectionStore } from '../store/inspectionStore'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import StatusBadge from '../components/StatusBadge'
import LedPulse from '../components/LedPulse'
import EmptyState from '../components/EmptyState'

import { getInspections } from '../lib/apiClient'
import type { HistoryEntry, Severity } from '../types'

// Mock fallback static entries when local history is unpopulated
const MOCK_STATIC_HISTORY: HistoryEntry[] = [
  {
    id: '#NK-4821-AX',
    timestamp: 'Oct 24, 02:22:05 PM',
    severity: 'Critical',
    defectName: 'Surface Crack',
    imageDataUrl: null,
    result: {
      success: true,
      image: { width: 1280, height: 720 },
      inference_time_ms: 32,
      detections: [
        {
          class: 'surface_crack',
          confidence: 0.88,
          bounding_box: { x1: 100, y1: 150, x2: 300, y2: 400 },
        },
      ],
    },
  },
  {
    id: '#NK-4819-BZ',
    timestamp: 'Oct 24, 12:05:41 PM',
    severity: 'Warning',
    defectName: 'Scratch',
    imageDataUrl: null,
    result: {
      success: true,
      image: { width: 1280, height: 720 },
      inference_time_ms: 28,
      detections: [
        {
          class: 'scratch',
          confidence: 0.65,
          bounding_box: { x1: 50, y1: 80, x2: 120, y2: 250 },
        },
      ],
    },
  },
  {
    id: '#NK-4817-CQ',
    timestamp: 'Oct 24, 09:14:18 AM',
    severity: 'Resolved',
    defectName: 'No Defects Found',
    imageDataUrl: null,
    result: {
      success: true,
      image: { width: 1280, height: 720 },
      inference_time_ms: 25,
      detections: [],
    },
  },
]

// Timeline card component
function HistoryCard({
  entry,
  index,
  onViewDetails,
}: {
  entry: HistoryEntry
  index: number
  onViewDetails: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const isPass = entry.result?.detections && entry.result.detections.length === 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.04 }}
      className="relative pl-12 text-left"
    >
      {/* Timeline indicator node */}
      <div className={`absolute left-3.5 top-6 w-3 h-3 rounded-full border z-10 ${
        isPass
          ? 'bg-primary border-primary shadow-[0_0_8px_rgba(251,186,100,0.5)]'
          : entry.severity === 'Critical'
          ? 'bg-error border-error shadow-[0_0_8px_rgba(255,180,171,0.5)]'
          : 'bg-secondary border-secondary'
      }`} />

      <div className="glass-card rounded-2xl p-5 border border-white/5 hover:border-primary/20 transition-all duration-300">
        
        {/* Core summary details row */}
        <div className="flex gap-4 items-start">
          
          {/* Thumb preview container */}
          <div className="w-16 h-16 rounded-xl overflow-hidden bg-surface-container-high border border-white/10 flex-shrink-0 flex items-center justify-center">
            {entry.imageDataUrl ? (
              <img src={entry.imageDataUrl} alt="Inspection thumbnail" className="w-full h-full object-cover" />
            ) : (
              <span className="material-symbols-outlined text-on-surface-variant/40 text-2xl">
                image
              </span>
            )}
          </div>

          {/* Details header */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap justify-between items-center gap-2">
              <span className="font-display-mono text-[9px] text-on-surface-variant/50 uppercase">
                {entry.id} · {entry.timestamp}
              </span>
              <StatusBadge severity={entry.severity} />
            </div>
            
            <h4 className="font-bold text-white text-base mt-1 capitalize leading-tight">
              {entry.defectName}
            </h4>

            {/* Expansion controls toggle */}
            <div className="mt-3 flex gap-3">
              <button
                onClick={onViewDetails}
                className="px-4 py-1.5 rounded-lg border border-primary/20 hover:bg-primary/10 text-primary font-label-sm text-[11px] uppercase tracking-wider transition-colors"
              >
                Inspection Report
              </button>
              <button
                onClick={() => setExpanded(!expanded)}
                className="px-4 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white font-label-sm text-[11px] uppercase tracking-wider flex items-center gap-1 transition-colors"
              >
                Diagnostics
                <span className="material-symbols-outlined text-xs">
                  {expanded ? 'keyboard_arrow_up' : 'keyboard_arrow_down'}
                </span>
              </button>
            </div>
          </div>

        </div>

        {/* Expandable details panel */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden mt-4 pt-4 border-t border-white/5 space-y-3 font-display-mono text-xs text-on-surface-variant/80"
            >
              <div className="flex justify-between">
                <span>Inference time:</span>
                <span className="text-white font-bold">{entry.result?.inference_time_ms.toFixed(1) ?? '--'} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Resolution dimensions:</span>
                <span className="text-white font-bold">
                  {entry.result?.image.width ?? 1280} × {entry.result?.image.height ?? 720}
                </span>
              </div>

              {/* Bounding box list */}
              {entry.result?.detections && entry.result.detections.length > 0 && (
                <div className="pt-2">
                  <p className="text-[10px] text-primary uppercase font-bold mb-2">Defect Detections:</p>
                  <div className="space-y-1.5">
                    {entry.result.detections.map((d, i) => (
                      <div key={i} className="flex justify-between bg-black/25 px-3 py-1.5 rounded-lg border border-white/5 capitalize">
                        <span className="text-white">{d.class.replace(/_/g, ' ')}</span>
                        <span className="text-primary font-bold">{(d.confidence * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </motion.div>
  )
}

export default function FactoryMemory() {
  const navigate = useNavigate()
  const { history } = useInspectionStore()
  const [dbInspections, setDbInspections] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)

  // Sorting and Filtering State
  const [searchTerm, setSearchTerm] = useState('')
  const [filterSeverity, setFilterSeverity] = useState<'All' | Severity>('All')
  const [sortBy, setSortBy] = useState<'Newest' | 'Oldest' | 'Severity'>('Newest')

  useEffect(() => {
    let active = true
    async function loadInspections() {
      try {
        setLoading(true)
        const response = await getInspections({ limit: 100 })
        const mapped: HistoryEntry[] = response.results.map((item: any) => {
          const isPass = item.status === 'PASS'
          const severity: Severity = isPass
            ? 'Resolved'
            : item.confidence > 0.8
            ? 'Critical'
            : 'Warning'
          
          const defectName = item.detections.length > 0
            ? item.detections[0].class.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
            : 'No Defects Found'

          return {
            id: item.id,
            timestamp: item.timestamp,
            severity,
            defectName,
            imageDataUrl: item.image_path,
            result: {
              success: true,
              image: { width: 640, height: 640 },
              detections: item.detections.map((d: any) => ({
                class: d.class,
                confidence: d.confidence,
                bounding_box: d.bounding_box
              })),
              inference_time_ms: item.inference_time_ms
            },
            inferenceTimeMs: item.inference_time_ms,
            latencyMs: item.latency_ms
          }
        })
        if (active) {
          setDbInspections(mapped)
        }
      } catch (err) {
        console.error('Failed to load inspections from backend:', err)
      } finally {
        if (active) setLoading(false)
      }
    }
    loadInspections()
    return () => {
      active = false
    }
  }, [])

  // Unified list combining actual history with mock logs if empty
  const activeList = useMemo(() => {
    const list = dbInspections.length > 0 ? dbInspections : history
    return list.length > 0 ? list : MOCK_STATIC_HISTORY
  }, [dbInspections, history])

  // Pattern Insights Discovery (Module 8)
  const patternAnalysis = useMemo(() => {
    const counts: Record<string, number> = {}
    let totalCritical = 0

    activeList.forEach((e) => {
      if (e.severity === 'Critical') {
        counts[e.defectName] = (counts[e.defectName] || 0) + 1
        totalCritical++
      }
    })

    const items = Object.entries(counts).map(([name, count]) => ({
      name,
      pct: totalCritical > 0 ? Math.round((count / totalCritical) * 100) : 0,
    }))

    return items.sort((a, b) => b.pct - a.pct).slice(0, 3)
  }, [activeList])

  // Filtered and Sorted Timeline Lists
  const processedList = useMemo(() => {
    let result = [...activeList]

    // 1. Search Query
    if (searchTerm.trim() !== '') {
      const q = searchTerm.toLowerCase()
      result = result.filter(
        (item) =>
          item.id.toLowerCase().includes(q) ||
          item.defectName.toLowerCase().includes(q)
      )
    }

    // 2. Severity Filters
    if (filterSeverity !== 'All') {
      result = result.filter((item) => item.severity === filterSeverity)
    }

    // 3. Sorting Parameters
    if (sortBy === 'Newest') {
      // Handled by default sorting list order
    } else if (sortBy === 'Oldest') {
      result.reverse()
    } else if (sortBy === 'Severity') {
      const order: Record<Severity, number> = { Critical: 3, Warning: 2, Resolved: 1 }
      result.sort((a, b) => order[b.severity] - order[a.severity])
    }

    return result
  }, [activeList, searchTerm, filterSeverity, sortBy])

  return (
    <div className="bg-background text-on-background font-body-md min-h-screen">
      <TopBar />

      <main className="pt-24 pb-32 px-margin-mobile max-w-3xl mx-auto space-y-8">
        
        {/* Pattern Discovery Panel */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-white font-bold">
              Defect Distribution Insights
            </h2>
            <div className="flex items-center gap-2 bg-surface-container-high px-3 py-1 rounded-full border border-white/5">
              <LedPulse size="sm" />
              <span className="font-display-mono text-[9px] text-primary-fixed-dim uppercase tracking-wider font-bold">
                Pattern Scan
              </span>
            </div>
          </div>

          <GlassCard rimLight className="p-6 rounded-3xl space-y-5">
            <div className="space-y-4">
              {patternAnalysis.length > 0 ? (
                patternAnalysis.map((defect, i) => (
                  <div key={defect.name} className="space-y-2 text-left">
                    <div className="flex justify-between text-xs font-display-mono uppercase text-on-surface-variant/80">
                      <span>{defect.name} frequency</span>
                      <span className="text-primary font-bold">{defect.pct}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${defect.pct}%` }}
                        transition={{ duration: 0.8, delay: i * 0.1 }}
                        className="h-full bg-gradient-to-r from-primary to-secondary rounded-full"
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-on-surface-variant/40 italic">
                  Plotting distributions when defects are recorded...
                </p>
              )}
            </div>
            <p className="text-[10px] font-display-mono text-on-surface-variant/50 text-left">
              * Calculations computed based on the active queue of {activeList.length} component runs.
            </p>
          </GlassCard>
        </section>

        {/* Timeline lists section */}
        <section className="space-y-6">
          <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-white font-bold text-left">
            Inspection Database Timeline
          </h2>

          {/* Search, Sort and Filter Toolbar */}
          <div className="glass-card p-4 rounded-2xl border border-white/5 space-y-4">
            
            {/* Search inputs */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search database by defect name or Session ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-black/30 border border-white/10 px-10 py-2.5 rounded-xl text-sm outline-none focus:border-primary/40 text-white placeholder:text-on-surface-variant/30"
              />
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant/40 text-lg">
                search
              </span>
            </div>

            {/* Filter categories & sorts */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              
              {/* Severity Category switchers */}
              <div className="flex bg-black/20 p-1 rounded-lg border border-white/5 gap-1">
                {(['All', 'Critical', 'Warning', 'Resolved'] as const).map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setFilterSeverity(sev)}
                    className={`px-3 py-1 rounded text-[11px] font-display-mono uppercase font-bold transition-all ${
                      filterSeverity === sev
                        ? 'bg-primary text-black'
                        : 'text-on-surface-variant/60 hover:text-white'
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>

              {/* Sort selector */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-display-mono uppercase text-on-surface-variant/40">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-black/30 border border-white/10 text-white font-display-mono text-[11px] px-3 py-1.5 rounded-lg outline-none cursor-pointer"
                >
                  <option value="Newest">Newest First</option>
                  <option value="Oldest">Oldest First</option>
                  <option value="Severity">Severity Priority</option>
                </select>
              </div>

            </div>

          </div>

          {/* Timeline Stack */}
          <div className="relative space-y-4">
            {/* Vertical connector guide */}
            {processedList.length > 0 && (
              <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-gradient-to-b from-primary/30 via-white/5 to-transparent pointer-events-none" />
            )}

            <AnimatePresence>
              {processedList.length > 0 ? (
                processedList.map((entry, index) => (
                  <HistoryCard
                    key={entry.id}
                    entry={entry}
                    index={index}
                    onViewDetails={() => {
                      // Navigate to inspectionResult if entry contains a result
                      if (entry.result) {
                        useInspectionStore.setState({ lastResult: entry.result, capturedImageUrl: entry.imageDataUrl, sessionId: entry.id })
                        navigate('/inspect/result')
                      }
                    }}
                  />
                ))
              ) : (
                <EmptyState
                  icon="database"
                  title="Timeline Unresolved"
                  description="No recorded checks match your current searches or filters."
                  actionLabel="Clear Filters"
                  onAction={() => {
                    setSearchTerm('')
                    setFilterSeverity('All')
                    setSortBy('Newest')
                  }}
                />
              )}
            </AnimatePresence>
          </div>
        </section>

      </main>

      <BottomNav />
    </div>
  )
}
