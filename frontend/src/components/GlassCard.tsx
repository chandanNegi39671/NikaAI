/**
 * components/GlassCard.tsx
 * ─────────────────────────
 * Reusable glassmorphism container.
 */

import { motion } from 'framer-motion'
import type { ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
  rimLight?: boolean
  hover?: boolean
  onClick?: () => void
  animationDelay?: number
}

export default function GlassCard({
  children,
  className = '',
  rimLight = false,
  hover = false,
  onClick,
  animationDelay = 0,
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: animationDelay, ease: [0.2, 0.8, 0.2, 1] }}
      onClick={onClick}
      className={`
        glass-card rounded-2xl relative overflow-hidden
        ${rimLight ? 'border-t border-primary/40' : ''}
        ${hover ? 'metallic-glow cursor-pointer' : ''}
        ${className}
      `}
    >
      {rimLight && (
        <div className="rim-light absolute inset-0 rounded-2xl pointer-events-none opacity-50" />
      )}
      {children}
    </motion.div>
  )
}
