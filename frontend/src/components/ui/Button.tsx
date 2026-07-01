/** Pill-shaped button — filled (primary/signal), outlined (secondary), or ghost. */

import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'filled' | 'signal' | 'outline' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  filled: 'bg-primary text-primary-foreground hover:opacity-90',
  signal: 'bg-signal text-signal-foreground hover:opacity-90',
  outline: 'bg-transparent text-foreground border border-border hover:bg-accent',
  ghost: 'bg-transparent text-muted-foreground hover:text-foreground hover:bg-accent',
  danger: 'bg-red-600 text-white hover:bg-red-500',
}

export default function Button({ children, variant = 'filled', className = '', ...rest }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-pill px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  )
}
