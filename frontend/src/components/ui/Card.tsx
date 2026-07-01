/** Paper-surface card — the base building block of the Ventriloc-derived design system. */

import type { ReactNode, HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  padding?: 'none' | 'sm' | 'md'
}

export default function Card({ children, padding = 'md', className = '', ...rest }: CardProps) {
  const pad = padding === 'none' ? '' : padding === 'sm' ? 'p-4' : 'p-6'
  return (
    <div
      className={`rounded-lg border border-border bg-card shadow-card ${pad} ${className}`}
      {...rest}
    >
      {children}
    </div>
  )
}
