/**
 * src/components/Notification.tsx
 * ───────────────────────────────
 * Toast notification widget supporting success, info, warning, and error types.
 */

import { useEffect } from 'react'
import { motion } from 'framer-motion'
import type { NotificationItem } from '../types'

interface NotificationProps {
  item: NotificationItem
  onDismiss: (id: string) => void
}

const typeConfigs = {
  success: {
    icon: 'check_circle',
    color: 'text-primary bg-primary/10 border-primary/20',
  },
  error: {
    icon: 'error',
    color: 'text-error bg-error-container/20 border-error/30',
  },
  warning: {
    icon: 'warning',
    color: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
  },
  info: {
    icon: 'info',
    color: 'text-tertiary bg-tertiary/10 border-tertiary/20',
  },
}

export default function Notification({ item, onDismiss }: NotificationProps) {
  const config = typeConfigs[item.type]

  useEffect(() => {
    if (item.durationMs && item.durationMs > 0) {
      const t = setTimeout(() => {
        onDismiss(item.id)
      }, item.durationMs)
      return () => clearTimeout(t)
    }
  }, [item, onDismiss])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      className={`glass-panel border px-5 py-4 rounded-xl flex items-start gap-4 shadow-glass max-w-sm w-full pointer-events-auto ${config.color}`}
    >
      <span className="material-symbols-outlined flex-shrink-0 mt-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>
        {config.icon}
      </span>
      <div className="flex-1 text-left min-w-0">
        <h5 className="font-semibold text-sm leading-tight text-white">{item.title}</h5>
        {item.message && <p className="text-xs text-on-surface-variant/80 mt-1 leading-normal">{item.message}</p>}
      </div>
      <button
        onClick={() => onDismiss(item.id)}
        className="text-on-surface-variant/40 hover:text-white transition-colors duration-200 mt-0.5 flex-shrink-0"
      >
        <span className="material-symbols-outlined text-[18px]">close</span>
      </button>
    </motion.div>
  )
}
