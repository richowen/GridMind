/** Battery mode recommendation metric card. */

import { Activity } from 'lucide-react'
import Card from '@/components/ui/Card'

interface ModeCardProps {
  mode: string | null
  reason: string | null
}

export default function ModeCard({ mode, reason }: ModeCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-pill bg-signal/15 text-signal">
          <Activity className="h-3.5 w-3.5" />
        </span>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Mode</span>
      </div>
      <div className="font-display text-2xl tracking-display text-foreground mb-3">
        {mode ?? '—'}
      </div>
      <div className="text-xs text-muted-foreground truncate" title={reason ?? ''}>
        {reason ?? 'No recommendation'}
      </div>
    </Card>
  )
}
