import { Zap } from 'lucide-react'
import { VppEvent } from '@/types/domain'

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
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  };

  const timeRangeStr = `${formatTime(event.start)} – ${formatTime(event.end)} on ${formatDate(event.start)}`;

  if (event.is_active) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-500 dark:border-red-500/20 dark:bg-red-500/5">
        <Zap className="h-5 w-5 fill-current animate-pulse shrink-0" />
        <div className="flex-1 text-sm font-medium">
          <span className="font-bold uppercase tracking-wide mr-2 text-xs bg-red-500 text-white dark:bg-red-600 px-1.5 py-0.5 rounded">Active</span>
          <span className="font-semibold text-red-900 dark:text-red-400">VPP Export Event Active:</span>{' '}
          <span className="text-red-700 dark:text-red-300">Earn premium export rates during {timeRangeStr}.</span>
        </div>
      </div>
    );
  }

  if (event.is_upcoming) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-500 dark:border-amber-500/20 dark:bg-amber-500/5">
        <Zap className="h-5 w-5 shrink-0" />
        <div className="flex-1 text-sm font-medium">
          <span className="font-bold uppercase tracking-wide mr-2 text-xs bg-amber-500 text-white dark:bg-amber-600 px-1.5 py-0.5 rounded">Upcoming</span>
          <span className="font-semibold text-amber-900 dark:text-amber-400">VPP Event Starting Soon:</span>{' '}
          <span className="text-amber-700 dark:text-amber-300">An export event is scheduled for {timeRangeStr}.</span>
        </div>
      </div>
    );
  }

  return null;
}
