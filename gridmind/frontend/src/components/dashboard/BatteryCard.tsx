/** Battery SoC gauge card with mode indicator. */

import { Battery } from 'lucide-react'

interface BatteryCardProps {
  soc: number | null
  mode: string | null
}

export default function BatteryCard({ soc, mode }: BatteryCardProps) {
  const pct = soc ?? 0
  const color = pct > 60 ? 'bg-green-500' : pct > 20 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Battery className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Battery</span>
      </div>
      <div className="text-3xl font-bold text-foreground mb-2">
        {soc !== null ? `${soc.toFixed(0)}%` : '—'}
      </div>
      <div className="w-full bg-secondary rounded-full h-2 mb-2">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="text-xs text-muted-foreground">{mode ?? 'Unknown'}</div>
    </div>
  )
}
