/**
 * components/StatusBadge.tsx
 * ───────────────────────────
 * Pill-style severity/status badge.
 */

type Severity = 'Critical' | 'Warning' | 'Resolved' | 'Optimal' | 'Live' | 'Pass' | 'Fail'

interface StatusBadgeProps {
  severity: Severity
  className?: string
}

const configs: Record<Severity, { text: string; classes: string }> = {
  Critical: {
    text: 'CRITICAL',
    classes: 'text-error bg-error-container/20 border border-error/30',
  },
  Warning: {
    text: 'WARNING',
    classes: 'text-primary-fixed-dim bg-primary-container/10 border border-primary/20',
  },
  Resolved: {
    text: 'RESOLVED',
    classes: 'text-on-surface-variant/60 bg-surface-variant/40 border border-outline-variant/40',
  },
  Optimal: {
    text: 'OPTIMAL',
    classes: 'text-secondary bg-secondary-container/10 border border-secondary/20',
  },
  Live: {
    text: 'LIVE',
    classes: 'text-primary bg-primary/10 border border-primary/20',
  },
  Pass: {
    text: 'PASS',
    classes: 'text-primary bg-primary/10 border border-primary/30',
  },
  Fail: {
    text: 'FAIL',
    classes: 'text-error bg-error-container/20 border border-error/30',
  },
}

export default function StatusBadge({ severity, className = '' }: StatusBadgeProps) {
  const { text, classes } = configs[severity]
  return (
    <span className={`font-display-mono text-[10px] px-2 py-0.5 rounded ${classes} ${className}`}>
      {text}
    </span>
  )
}
