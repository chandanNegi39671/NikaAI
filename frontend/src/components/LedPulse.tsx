/**
 * components/LedPulse.tsx
 * ────────────────────────
 * Pulsing dot status indicator.
 */

interface LedPulseProps {
  color?: 'primary' | 'error' | 'secondary' | 'tertiary'
  size?: 'sm' | 'md'
}

const colorMap = {
  primary:  'bg-primary shadow-[0_0_8px_rgba(251,186,100,0.8)]',
  error:    'bg-error shadow-[0_0_8px_rgba(255,180,171,0.8)]',
  secondary:'bg-secondary shadow-[0_0_8px_rgba(255,182,148,0.8)]',
  tertiary: 'bg-tertiary shadow-[0_0_8px_rgba(144,205,255,0.8)]',
}

const sizeMap = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
}

export default function LedPulse({ color = 'primary', size = 'md' }: LedPulseProps) {
  return (
    <div className={`rounded-full ${colorMap[color]} ${sizeMap[size]} animate-led-pulse flex-shrink-0`} />
  )
}
