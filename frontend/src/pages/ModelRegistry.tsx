/**
 * pages/ModelRegistry.tsx
 * ───────────────────────
 * Model Registry Dashboard.
 * Integrates deployment lifecycle tracking, weight hot-swaps, and full metadata specifications.
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import LedPulse from '../components/LedPulse'
import { listModelVersions, switchModelVersion, updateModelStatus } from '../lib/apiClient'
import type { ModelVersion } from '../types'

export default function ModelRegistry() {
  const [models, setModels] = useState<ModelVersion[]>([])
  const [selectedModel, setSelectedModel] = useState<ModelVersion | null>(null)
  const [loading, setLoading] = useState(false)
  const [showStatusModal, setShowStatusModal] = useState(false)
  const [statusToUpdate, setStatusToUpdate] = useState('')

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const res = await listModelVersions()
      setModels(res.models)
      if (res.models.length > 0 && !selectedModel) {
        setSelectedModel(res.models[0])
      } else if (res.models.length > 0) {
        // Refresh selected model reference
        const ref = res.models.find(m => m.id === selectedModel?.id)
        if (ref) setSelectedModel(ref)
      }
    } catch (err) {
      console.error('Failed to list model registry versions', err)
    }
  }

  const handleHotSwap = async (versionName: string) => {
    if (!window.confirm(`Switch active network weights to: ${versionName}?`)) return
    setLoading(true)
    try {
      await switchModelVersion(versionName)
      await fetchModels()
      alert(`Model successfully switched to ${versionName}`)
    } catch (err) {
      console.error(err)
      alert('Failed to deploy weights checkpoint. Verify file path.')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!selectedModel) return
    setLoading(true)
    try {
      await updateModelStatus(selectedModel.version_name, newStatus)
      setShowStatusModal(false)
      await fetchModels()
    } catch (err) {
      console.error(err)
      alert('Failed to update deployment lifecycle state.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col pt-20 pb-24 md:pb-8">
      <TopBar />

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 md:px-margin-desktop grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left column: Model version lists */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <GlassCard rimLight className="p-6 border-t border-primary/30">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-headline-lg text-xl text-on-surface flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">view_in_ar</span>
                Model Checkpoints
              </h2>
              <span className="text-[10px] font-display-mono text-primary bg-primary-container/20 border border-primary/30 px-2 py-0.5 rounded">
                DB Tracker
              </span>
            </div>

            <div className="flex flex-col gap-3 max-h-[55vh] overflow-y-auto pr-1">
              {models.map((m) => {
                const isActive = m.deployment_status === 'production'
                const isSelected = selectedModel?.id === m.id
                return (
                  <motion.div
                    key={m.id}
                    onClick={() => setSelectedModel(m)}
                    whileHover={{ scale: 1.01 }}
                    className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer flex flex-col gap-2 relative ${
                      isSelected
                        ? 'bg-primary-container/20 border-primary shadow-glass'
                        : 'bg-surface-variant/15 border-outline-variant/10 hover:border-outline-variant/40'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-display-mono text-sm font-semibold truncate max-w-[75%] text-on-surface">
                        {m.version_name}
                      </span>
                      <span className={`text-[10px] font-display-mono uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                        isActive
                          ? 'bg-secondary-container/25 text-secondary border-secondary/40 shadow-primary-glow'
                          : m.deployment_status === 'staging'
                          ? 'bg-primary-container/15 text-primary border-primary/30'
                          : m.deployment_status === 'validated'
                          ? 'bg-tertiary-container/15 text-tertiary border-tertiary/30'
                          : 'bg-surface-variant text-on-surface-variant/60 border-outline-variant/20'
                      }`}>
                        {m.deployment_status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-on-surface-variant">
                      <span className="font-display-mono">mAP: {m.map_score?.toFixed(3) || 'N/A'}</span>
                      <span className="font-display-mono text-[10px]">
                        {m.model_size_mb ? `${m.model_size_mb} MB` : 'N/A'}
                      </span>
                    </div>

                    {isActive && (
                      <div className="absolute right-3 bottom-3 flex items-center gap-1.5 text-secondary">
                        <LedPulse active={true} />
                        <span className="text-[9px] font-display-mono font-bold uppercase tracking-wider">Active</span>
                      </div>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </GlassCard>
        </div>

        {/* Right column: Selected Model Specs */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {selectedModel ? (
            <GlassCard rimLight className="p-6 border-t border-primary/30 flex flex-col gap-6 flex-1">
              
              {/* Header section */}
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-outline-variant/30">
                <div>
                  <span className="font-display-mono text-[11px] text-primary uppercase tracking-widest block mb-1">
                    Checkpoint Specifications
                  </span>
                  <h1 className="font-headline-lg text-2xl text-on-surface truncate">{selectedModel.version_name}</h1>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setStatusToUpdate(selectedModel.deployment_status)
                      setShowStatusModal(true)
                    }}
                    className="font-label-sm text-xs bg-surface-variant/30 hover:bg-surface-variant border border-outline-variant/40 text-on-surface rounded-full px-5 py-2.5 transition-all cursor-pointer"
                  >
                    Change Status
                  </button>

                  <button
                    onClick={() => handleHotSwap(selectedModel.version_name)}
                    disabled={selectedModel.deployment_status === 'production' || loading}
                    className="font-label-sm text-xs bg-primary hover:bg-primary-container disabled:opacity-40 disabled:cursor-not-allowed border border-primary/30 text-on-primary rounded-full px-5 py-2.5 transition-all cursor-pointer shadow-primary-glow font-semibold"
                  >
                    Deploy (Hot-Swap)
                  </button>
                </div>
              </div>

              {/* Grid content specs */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Visual statistics */}
                <div className="space-y-4">
                  <h3 className="font-display-mono text-xs text-primary uppercase tracking-wider">Evaluation Metrics</h3>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-surface-variant/10 border border-outline-variant/20 p-3 rounded-xl text-center">
                      <span className="text-[10px] font-display-mono text-on-surface-variant uppercase">mAP</span>
                      <p className="font-headline-lg text-lg text-primary mt-1">{selectedModel.map_score?.toFixed(3) || 'N/A'}</p>
                    </div>
                    <div className="bg-surface-variant/10 border border-outline-variant/20 p-3 rounded-xl text-center">
                      <span className="text-[10px] font-display-mono text-on-surface-variant uppercase">Precision</span>
                      <p className="font-headline-lg text-lg text-primary mt-1">{selectedModel.precision?.toFixed(3) || 'N/A'}</p>
                    </div>
                    <div className="bg-surface-variant/10 border border-outline-variant/20 p-3 rounded-xl text-center">
                      <span className="text-[10px] font-display-mono text-on-surface-variant uppercase">Recall</span>
                      <p className="font-headline-lg text-lg text-primary mt-1">{selectedModel.recall?.toFixed(3) || 'N/A'}</p>
                    </div>
                  </div>

                  <div className="bg-surface-variant/5 border border-outline-variant/20 rounded-xl p-4 space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Training Date</span>
                      <span className="font-display-mono">{selectedModel.training_date ? new Date(selectedModel.training_date).toLocaleDateString() : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Trained By</span>
                      <span className="font-display-mono">{selectedModel.trained_by || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Dataset</span>
                      <span className="font-display-mono truncate max-w-[180px]">{selectedModel.dataset_name || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                {/* Technical specifications */}
                <div className="space-y-4">
                  <h3 className="font-display-mono text-xs text-primary uppercase tracking-wider">Model Lineage</h3>
                  <div className="bg-surface-variant/5 border border-outline-variant/20 rounded-xl p-4 space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Framework</span>
                      <span className="font-display-mono">{selectedModel.framework || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">File Size</span>
                      <span className="font-display-mono">{selectedModel.model_size_mb ? `${selectedModel.model_size_mb} MB` : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Parameters</span>
                      <span className="font-display-mono">{selectedModel.parameter_count ? selectedModel.parameter_count.toLocaleString() : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-on-surface-variant">Commit Reference</span>
                      <code className="text-xs bg-surface-container-lowest/50 px-1.5 py-0.5 rounded font-display-mono text-primary">
                        {selectedModel.commit_hash || 'N/A'}
                      </code>
                    </div>
                  </div>
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2 mt-auto">
                <span className="font-display-mono text-xs text-primary uppercase tracking-wider block">Training Notes</span>
                <div className="bg-surface-container-lowest/50 border border-outline-variant/25 rounded-xl p-4 text-sm text-on-surface-variant leading-relaxed">
                  {selectedModel.notes || 'No registration notes entered.'}
                </div>
              </div>

            </GlassCard>
          ) : (
            <div className="flex-1 flex items-center justify-center opacity-40">
              <p className="font-display-mono text-sm tracking-wider">Select a checkpoint to view specs</p>
            </div>
          )}
        </div>
      </main>

      {/* Status Lifecycle Modal */}
      <AnimatePresence>
        {showStatusModal && selectedModel && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card max-w-md w-full border border-primary/40 rounded-2xl p-6 relative overflow-hidden"
            >
              <h3 className="font-headline-lg text-lg text-on-surface mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">edit_document</span>
                Update Deployment State
              </h3>
              <p className="text-xs text-on-surface-variant mb-4">
                Enforcing model promotion updates state logs. Switching status to 'production' triggers a hot-swap.
              </p>

              <div className="flex flex-col gap-2 mb-6">
                {['training', 'validated', 'staging', 'production', 'archived'].map((statusOption) => (
                  <button
                    key={statusOption}
                    onClick={() => setStatusToUpdate(statusOption)}
                    className={`p-3 rounded-lg text-left text-sm font-display-mono capitalize border transition-all ${
                      statusToUpdate === statusOption
                        ? 'bg-primary-container/20 border-primary text-primary font-bold'
                        : 'bg-surface-variant/20 border-outline-variant/20 hover:border-outline-variant/40 text-on-surface'
                    }`}
                  >
                    {statusOption}
                  </button>
                ))}
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowStatusModal(false)}
                  className="font-label-sm text-xs bg-surface-variant/30 border border-outline-variant/30 text-on-surface px-4 py-2 rounded-full hover:bg-surface-variant transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleStatusChange(statusToUpdate)}
                  className="font-label-sm text-xs bg-primary text-on-primary px-5 py-2 rounded-full hover:bg-primary-container transition-all cursor-pointer shadow-primary-glow font-bold"
                >
                  Apply State change
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <BottomNav />
    </div>
  )
}
