/**
 * src/components/SkeletonLoader.tsx
 * ─────────────────────────────────
 * Reusable skeleton elements styled with a premium amber-tinted shimmer.
 */

import { motion } from 'framer-motion'

interface SkeletonProps {
  className?: string
  variant?: 'card' | 'text' | 'rect' | 'circle'
}

export default function SkeletonLoader({
  className = '',
  variant = 'card',
}: SkeletonProps) {
  // Shimmer pulse animation setting
  const shimmerClass =
    'relative overflow-hidden before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-white/5 before:to-transparent'

  const baseStyles = 'bg-surface-container-high/40 rounded-xl ' + shimmerClass

  if (variant === 'circle') {
    return <div className={`${baseStyles} rounded-full ${className}`} />
  }

  if (variant === 'text') {
    return <div className={`${baseStyles} h-4 w-3/4 rounded ${className}`} />
  }

  if (variant === 'rect') {
    return <div className={`${baseStyles} h-24 w-full ${className}`} />
  }

  // Default "card" block
  return (
    <div className={`${baseStyles} p-6 border border-white/5 flex flex-col gap-3 ${className}`}>
      <div className="h-4 w-1/3 bg-white/5 rounded" />
      <div className="h-8 w-2/3 bg-white/10 rounded" />
      <div className="h-3 w-full bg-white/5 rounded mt-4" />
    </div>
  )
}
