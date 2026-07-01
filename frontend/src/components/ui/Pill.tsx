/** Pill badge/tag — filled or outlined, neutral or signal-orange accent. */

import type { ReactNode } from 'react'

type PillVariant = 'neutral' | 'outline' | 'signal' | 'success' | 'danger'
type PillSize = 'xs' | 'sm'

interface PillProps {
  children: ReactNode
  variant?: PillVariant
  size?: PillSize
  className?: string
}

const VARIANT_CLASSES: Record<PillVariant, string> = {
  neutral: 'bg-secondary text-secondary-foreground border border-transparent',
  outline: 'bg-transparent text-muted-foreground border border-border',
  signal: 'bg-signal text-signal-foreground border border-transparent',
  success: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
  danger: 'bg-red-500/15 text-red-400 border border-red-500/25',
}

const SIZE_CLASSES: Record<PillSize, string> = {
  xs: 'text-[11px] px-2 py-0.5',
  sm: 'text-xs px-2.5 py-1',
}

export default function Pill({ children, variant = 'neutral', size = 'sm', className = '' }: PillProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-pill font-medium uppercase tracking-wide whitespace-nowrap ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
    >
      {children}
    </span>
  )
}
