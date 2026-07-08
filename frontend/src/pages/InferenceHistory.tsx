/**
 * pages/InferenceHistory.tsx
 * ──────────────────────────
 * Filterable visual inspection audit log page.
 * Implements pagination, multi-key filter queries, and direct navigation links
 * to the VisualizationViewer.
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import StatusBadge from '../components/StatusBadge'
import { getInferenceHistory, getMachines, getWorkers } from '../lib/apiClient'
import type { InferenceLogItem } from '../types'

export default function InferenceHistory() {
  const [logs, setLogs] = useState<InferenceLogItem[]>([])
  const [total, setTotal] = useState(0)
  const [machines, setMachines] = useState<any[]>([])
  const [workers, setWorkers] = useState<any[]>([])

  // Filters State
  const [machineId, setMachineId] = useState('')
  const [workerId, setWorkerId] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [defectClass, setDefectClass] = useState('')
  const [minConfidence, setMinConfidence] = useState<number | ''>('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const limit = 12

  useEffect(() => {
    fetchFilterOptions()
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [machineId, workerId, statusFilter, defectClass, minConfidence, dateFrom, dateTo, page])

  const fetchFilterOptions = async () => {
    try {
      const machs = await getMachines()
      const works = await getWorkers()
      setMachines(machs)
      setWorkers(works)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchLogs = async () => {
    try {
      const offset = (page - 1) * limit
      const filters = {
        machine_id: machineId || undefined,
        worker_id: workerId || undefined,
        status: statusFilter || undefined,
        defect_class: defectClass || undefined,
        min_confidence: minConfidence !== '' ? minConfidence : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit,
        offset
      }
      const res = await getInferenceHistory(filters)
      setLogs(res.results)
      setTotal(res.total)
    } catch (err) {
      console.error('Failed to load inference logs', err)
    }
  }

  const handleResetFilters = () => {
    setMachineId('')
    setWorkerId('')
    setStatusFilter('')
    setDefectClass('')
    setMinConfidence('')
    setDateFrom('')
    setDateTo('')
    setPage(1)
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col pt-20 pb-24 md:pb-8">
      <TopBar />

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 md:px-margin-desktop flex flex-col gap-6">
        
        {/* Title */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <span className="font-display-mono text-[11px] text-primary uppercase tracking-widest block mb-1">
              Visual Audit Logs
            </span>
            <h1 className="font-headline-lg text-2xl text-on-surface">Inference History</h1>
          </div>
          
          <button
            onClick={handleResetFilters}
            className="font-label-sm text-xs bg-surface-variant/30 hover:bg-surface-variant border border-outline-variant/30 text-on-surface px-5 py-2.5 rounded-full transition-all"
          >
            Clear Filters
          </button>
        </div>

        {/* Filters Panel */}
        <GlassCard rimLight className="p-6 border-t border-primary/30 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Machine</label>
            <select
              value={machineId}
              onChange={(e) => { setMachineId(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            >
              <option value="">All Machines</option>
              {machines.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Operator</label>
            <select
              value={workerId}
              onChange={(e) => { setWorkerId(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            >
              <option value="">All Workers</option>
              {workers.map(w => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            >
              <option value="">All</option>
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Defect Category</label>
            <input
              type="text"
              value={defectClass}
              onChange={(e) => { setDefectClass(e.target.value); setPage(1); }}
              placeholder="e.g. crack, scratch"
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary placeholder-on-surface-variant/30"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Min Confidence</label>
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={minConfidence}
              onChange={(e) => { setMinConfidence(e.target.value === '' ? '' : parseFloat(e.target.value)); setPage(1); }}
              placeholder="0.0 - 1.0"
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">Start Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-display-mono text-[10px] text-on-surface-variant uppercase tracking-wider">End Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-primary"
            />
          </div>
        </GlassCard>

        {/* Logs Table Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {logs.length === 0 ? (
            <div className="col-span-full py-16 text-center opacity-40">
              <span className="material-symbols-outlined text-[50px] mb-2">find_in_page</span>
              <p className="font-display-mono text-sm tracking-wider">No Inspection Matches</p>
            </div>
          ) : (
            logs.map((log) => (
              <Link to={`/visualization/${log.id}`} key={log.id}>
                <GlassCard hover className="h-full p-5 flex flex-col gap-3 group">
                  <div className="flex justify-between items-start">
                    <div className="flex flex-col">
                      <span className="font-display-mono text-[10px] text-primary uppercase tracking-wider">
                        {log.machine_name || 'Generic Machine'}
                      </span>
                      <span className="font-display-mono text-xs text-on-surface-variant">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                    <StatusBadge severity={log.status === 'PASS' ? 'Pass' : 'Fail'} />
                  </div>

                  {log.image_path ? (
                    <div className="relative aspect-video rounded-lg overflow-hidden border border-outline-variant/20 bg-black/40">
                      <img
                        src={`/static/uploads/${log.image_path.split('/').pop()}`}
                        alt="inspection frame"
                        className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%231a1a1a"/><text x="50" y="55" fill="%23ffffff" font-size="8" font-family="monospace" text-anchor="middle">IMAGE MISSING</text></svg>'
                        }}
                      />
                    </div>
                  ) : (
                    <div className="aspect-video rounded-lg border border-dashed border-outline-variant/30 flex items-center justify-center text-xs opacity-35 bg-surface">
                      No visual capture
                    </div>
                  )}

                  <div className="flex justify-between items-center text-xs pt-1">
                    <span className="font-display-mono text-on-surface-variant">
                      Detections: <strong className="text-white">{log.detections.length}</strong>
                    </span>
                    <span className="font-display-mono text-on-surface-variant">
                      Conf: <strong className="text-primary">{log.confidence.toFixed(2)}</strong>
                    </span>
                  </div>

                  {log.detections.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {Array.from(new Set(log.detections.map(d => d.defect_class))).map((cls, idx) => (
                        <span key={idx} className="text-[9px] font-display-mono uppercase px-2 py-0.5 rounded bg-error-container/20 text-error border border-error/20">
                          {cls.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </GlassCard>
              </Link>
            ))
          )}
        </div>

        {/* Pagination controls */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-4 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 text-xs font-display-mono uppercase rounded-full border border-outline-variant/35 disabled:opacity-40 hover:bg-surface-variant transition-all"
            >
              Prev
            </button>
            <span className="font-display-mono text-xs text-on-surface-variant">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 text-xs font-display-mono uppercase rounded-full border border-outline-variant/35 disabled:opacity-40 hover:bg-surface-variant transition-all"
            >
              Next
            </button>
          </div>
        )}
      </main>
      <BottomNav />
    </div>
  )
}
