/**
 * pages/AuditLogs.tsx
 * ───────────────────
 * Supervisor compliance logs panel.
 * Shows detailed user actions, IP targets, request IDs, and state differences (old/new values).
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import { getAuditLogs } from '../lib/apiClient'
import type { AuditLogItem } from '../types'

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [total, setTotal] = useState(0)

  // Filters State
  const [actionFilter, setActionFilter] = useState('')
  const [requestId, setRequestId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const limit = 15

  useEffect(() => {
    fetchLogs()
  }, [actionFilter, requestId, dateFrom, dateTo, page])

  const fetchLogs = async () => {
    try {
      const offset = (page - 1) * limit
      const filters = {
        action: actionFilter || undefined,
        request_id: requestId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit,
        offset
      }
      const res = await getAuditLogs(filters)
      setLogs(res.results)
      setTotal(res.total)
    } catch (err) {
      console.error('Failed to load compliance audit logs', err)
    }
  }

  const handleResetFilters = () => {
    setActionFilter('')
    setRequestId('')
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
              Supervisor Controls
            </span>
            <h1 className="font-headline-lg text-2xl text-on-surface">Compliance Audit Logs</h1>
          </div>
          
          <button
            onClick={handleResetFilters}
            className="font-label-sm text-xs bg-surface-variant/30 hover:bg-surface-variant border border-outline-variant/30 text-on-surface px-5 py-2.5 rounded-full transition-all"
          >
            Clear Filters
          </button>
        </div>

        {/* Filter Toolbar */}
        <GlassCard rimLight className="p-5 border-t border-primary/30 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex flex-col gap-1">
            <span className="font-display-mono text-[10px] text-on-surface-variant uppercase">Action Type</span>
            <input
              type="text"
              value={actionFilter}
              onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
              placeholder="e.g. switch_model, delete"
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-primary placeholder-on-surface-variant/30"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="font-display-mono text-[10px] text-on-surface-variant uppercase">Request ID</span>
            <input
              type="text"
              value={requestId}
              onChange={(e) => { setRequestId(e.target.value); setPage(1); }}
              placeholder="UUID"
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-primary placeholder-on-surface-variant/30"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="font-display-mono text-[10px] text-on-surface-variant uppercase">Start Date</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-primary"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="font-display-mono text-[10px] text-on-surface-variant uppercase">End Date</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
              className="bg-surface-container/60 border border-outline-variant/30 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-primary"
            />
          </div>
        </GlassCard>

        {/* Audit Log Table */}
        <GlassCard rimLight className="border-t border-primary/30 overflow-hidden flex-1 flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-outline-variant/30 bg-surface-container/40 text-on-surface-variant font-display-mono uppercase tracking-wider">
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">User</th>
                  <th className="p-4">Action</th>
                  <th className="p-4">Entity</th>
                  <th className="p-4">Details</th>
                  <th className="p-4">IP Address</th>
                  <th className="p-4">Request ID</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center opacity-40 font-display-mono">
                      No compliance records registered matching search criteria.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="border-b border-outline-variant/10 hover:bg-surface-variant/10 transition-colors">
                      <td className="p-4 font-display-mono text-on-surface-variant">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-4 font-semibold text-white">
                        {log.username || 'System Daemon'}
                      </td>
                      <td className="p-4">
                        <span className="font-display-mono text-[10px] px-2.5 py-0.5 rounded bg-primary-container/20 text-primary border border-primary/20 uppercase">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 font-display-mono text-on-surface-variant">
                        {log.entity_type ? `${log.entity_type} [${log.entity_id?.substring(0, 8)}]` : 'N/A'}
                      </td>
                      <td className="p-4 max-w-xs truncate text-on-surface-variant" title={log.description || ''}>
                        {log.description || 'N/A'}
                        {log.old_value && (
                          <div className="text-[10px] opacity-75 font-display-mono mt-1">
                            <span className="text-error">-{log.old_value}</span> / <span className="text-primary">+{log.new_value}</span>
                          </div>
                        )}
                      </td>
                      <td className="p-4 font-display-mono text-on-surface-variant">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                      <td className="p-4 font-display-mono text-[10px] text-on-surface-variant">
                        {log.request_id ? log.request_id.substring(0, 8) : 'N/A'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination controls */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 py-4 border-t border-outline-variant/30 bg-surface-container/20">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 text-[10px] font-display-mono uppercase rounded-full border border-outline-variant/35 disabled:opacity-40 hover:bg-surface-variant transition-all cursor-pointer"
              >
                Prev
              </button>
              <span className="font-display-mono text-[10px] text-on-surface-variant">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 text-[10px] font-display-mono uppercase rounded-full border border-outline-variant/35 disabled:opacity-40 hover:bg-surface-variant transition-all cursor-pointer"
              >
                Next
              </button>
            </div>
          )}
        </GlassCard>
      </main>
      <BottomNav />
    </div>
  )
}
