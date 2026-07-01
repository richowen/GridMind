/** Battery SoC metric card — big value, thin progress rail, mode label. */

import { Battery } from 'lucide-react'
import Card from '@/components/ui/Card'

interface BatteryCardProps {
  soc: number | null
  mode: string | null
}

export default function BatteryCard({ soc, mode }: BatteryCardProps) {
  const pct = soc ?? 0

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-pill bg-signal/15 text-signal">
          <Battery className="h-3.5 w-3.5" />
        </span>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Battery</span>
      </div>
      <div className="font-display text-4xl tracking-display text-foreground mb-3">
        {soc !== null ? `${soc.toFixed(0)}%` : '—'}
      </div>
      <div className="w-full bg-fog rounded-pill h-1.5 mb-3 overflow-hidden">
        <div className="h-full rounded-pill bg-signal transition-all" style={{ width: `${pct}%` }} />
      </div>
      <div className="text-xs text-muted-foreground">{mode ?? 'Unknown'}</div>
    </Card>
  )
}
