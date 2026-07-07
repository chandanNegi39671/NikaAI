/**
 * src/components/EmptyState.tsx
 * ─────────────────────────────
 * Reusable premium empty state block with icon, headline, description, and action button.
 */

import { motion } from 'framer-motion'

interface EmptyStateProps {
  icon: string
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-10 rounded-2xl text-center max-w-sm mx-auto border border-white/5"
    >
      <span className="material-symbols-outlined text-primary/40 text-5xl mb-4 block">
        {icon}
      </span>
      <h3 className="font-headline-lg-mobile text-on-surface font-semibold text-lg mb-2">
        {title}
      </h3>
      <p className="text-on-surface-variant/60 text-sm leading-relaxed mb-6">
        {description}
      </p>
      {actionLabel && onAction && (
        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={onAction}
          className="px-6 py-2.5 rounded-full copper-gradient text-on-primary font-label-sm uppercase tracking-wider font-bold shadow-lg"
        >
          {actionLabel}
        </motion.button>
      )}
    </motion.div>
  )
}
