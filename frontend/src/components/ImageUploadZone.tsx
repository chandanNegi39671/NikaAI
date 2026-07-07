/**
 * src/components/ImageUploadZone.tsx
 * ──────────────────────────────────
 * Drag-and-drop zone component with file drop support, validations, preview, and control buttons.
 */

import { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { UploadedImage } from '../types'

interface ImageUploadZoneProps {
  uploaded: UploadedImage | null
  onFileSelect: (file: File) => void
  onRemove: () => void
  isProcessing?: boolean
}

export default function ImageUploadZone({
  uploaded,
  onFileSelect,
  onRemove,
  isProcessing = false,
}: ImageUploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      onFileSelect(file)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelect(file)
    }
  }

  const triggerSelect = () => {
    if (!isProcessing) {
      fileInputRef.current?.click()
    }
  }

  return (
    <div className="relative w-full max-w-lg aspect-video mx-auto">
      {/* Input element */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />

      <AnimatePresence mode="wait">
        {!uploaded ? (
          /* Empty upload zone */
          <motion.div
            key="empty"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={triggerSelect}
            className={`w-full h-full rounded-2xl border-2 border-dashed flex flex-col items-center justify-center cursor-pointer p-6 transition-all duration-300 ${
              isDragOver
                ? 'border-primary bg-primary/10 shadow-primary-glow scale-[1.01]'
                : 'border-outline-variant/40 bg-surface-container-low hover:border-primary/40 hover:bg-surface-container-high'
            }`}
          >
            <span className="material-symbols-outlined text-primary/60 text-5xl mb-3">
              cloud_upload
            </span>
            <h3 className="font-headline-lg-mobile text-on-surface font-semibold text-center mb-1">
              Drag & Drop Defect Image
            </h3>
            <p className="text-on-surface-variant/60 text-xs font-display-mono uppercase tracking-wider text-center">
              PNG, JPG, WEBP — Max 10MB
            </p>
          </motion.div>
        ) : (
          /* Upload loaded / Preview / Status card */
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="w-full h-full rounded-2xl overflow-hidden border border-primary/20 bg-surface-container relative flex items-center justify-center"
          >
            {uploaded.previewUrl && uploaded.status !== 'error' && (
              <img
                src={uploaded.previewUrl}
                alt="Selected component preview"
                className="w-full h-full object-cover"
              />
            )}

            {/* Overlays for processing states */}
            {uploaded.status === 'validating' && (
              <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center p-4">
                <span className="material-symbols-outlined text-primary animate-spin text-3xl mb-2">
                  progress_activity
                </span>
                <p className="text-on-surface font-display-mono text-xs uppercase tracking-wider">
                  Validating file...
                </p>
              </div>
            )}

            {uploaded.status === 'compressing' && (
              <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center p-4">
                <span className="material-symbols-outlined text-primary animate-spin text-3xl mb-2">
                  compress
                </span>
                <p className="text-on-surface font-display-mono text-xs uppercase tracking-wider">
                  Compressing for GPU upload...
                </p>
              </div>
            )}

            {uploaded.status === 'error' && (
              <div className="absolute inset-0 bg-error-container/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                <span className="material-symbols-outlined text-error text-5xl mb-2 animate-bounce">
                  error
                </span>
                <h4 className="text-on-error-container font-bold mb-2">Validation Failure</h4>
                <p className="text-on-error-container/80 text-sm mb-4">{uploaded.error}</p>
                <div className="flex gap-3">
                  <button
                    onClick={triggerSelect}
                    className="px-4 py-1.5 rounded-full bg-error text-on-error font-label-sm text-[11px] uppercase tracking-wider hover:bg-error/95"
                  >
                    Select Another
                  </button>
                  <button
                    onClick={onRemove}
                    className="px-4 py-1.5 rounded-full border border-error text-error font-label-sm text-[11px] uppercase tracking-wider hover:bg-error/10"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            )}

            {/* File info and Action bar overlay (only if ready) */}
            {uploaded.status === 'ready' && !isProcessing && (
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent flex items-center justify-between">
                <div className="text-left">
                  <p className="text-on-surface font-semibold text-xs truncate max-w-[200px]">
                    {uploaded.file.name}
                  </p>
                  <p className="text-on-surface-variant/60 text-[10px] font-display-mono uppercase">
                    {(uploaded.sizeBytes / 1024 / 1024).toFixed(2)} MB
                    {uploaded.compressedSizeBytes && (
                      <span className="text-primary font-bold">
                        {' '}
                        → {(uploaded.compressedSizeBytes / 1024 / 1024).toFixed(2)} MB
                      </span>
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={triggerSelect}
                    className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white"
                    title="Replace file"
                  >
                    <span className="material-symbols-outlined text-sm">autorenew</span>
                  </button>
                  <button
                    onClick={onRemove}
                    className="w-8 h-8 rounded-full bg-error-container/40 border border-error/30 hover:bg-error-container/60 flex items-center justify-center text-error"
                    title="Remove file"
                  >
                    <span className="material-symbols-outlined text-sm">delete</span>
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
