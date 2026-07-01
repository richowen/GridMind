import { Zap } from 'lucide-react'
import { VppEvent } from '@/types/domain'
import Pill from '@/components/ui/Pill'

interface VppEventBannerProps {
  event: VppEvent
}

export default function VppEventBanner({ event }: VppEventBannerProps) {
  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } catch {
      return isoString
    }
  }

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  }

  const timeRangeStr = `${formatTime(event.start)} – ${formatTime(event.end)} on ${formatDate(event.start)}`

  if (!event.is_active && !event.is_upcoming) return null

  return (
    <div
      className={`flex items-center gap-3 rounded-lg border p-4 ${
        event.is_active ? 'border-signal/40 bg-signal/10' : 'border-border bg-card'
      }`}
    >
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-pill ${
        event.is_active ? 'bg-signal text-signal-foreground' : 'bg-fog text-signal'
      }`}>
        <Zap className={`h-4 w-4 ${event.is_active ? 'animate-pulse' : ''}`} fill="currentColor" />
      </span>
      <div className="flex-1 text-sm">
        <div className="flex items-center gap-2 mb-0.5">
          <Pill variant={event.is_active ? 'signal' : 'outline'} size="xs">
            {event.is_active ? 'Active' : 'Upcoming'}
          </Pill>
          <span className="font-medium text-foreground">
            {event.is_active ? 'VPP export event active' : 'VPP event starting soon'}
          </span>
        </div>
        <span className="text-muted-foreground">
          {event.is_active ? 'Earning premium export rates' : 'Scheduled export event'} — {timeRangeStr}
        </span>
      </div>
    </div>
  )
}
