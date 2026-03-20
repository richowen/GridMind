/** Battery mode recommendation card. */

import { Activity } from 'lucide-react'

interface ModeCardProps {
  mode: string | null
  reason: string | null
}

export default function ModeCard({ mode, reason }: ModeCardProps) {
  const isForceCharge = mode === 'Force Charge'
  const isForceDischarge = mode === 'Force Discharge'

  const modeColor = isForceCharge
    ? 'text-blue-400'
    : isForceDischarge
    ? 'text-orange-400'
    : 'text-foreground'

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Activity className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Mode</span>
      </div>
      <div className={`text-xl font-bold mb-1 ${modeColor}`}>
        {mode ?? '—'}
      </div>
      <div className="text-xs text-muted-foreground truncate" title={reason ?? ''}>
        {reason ?? 'No recommendation'}
      </div>
    </div>
  )
}
