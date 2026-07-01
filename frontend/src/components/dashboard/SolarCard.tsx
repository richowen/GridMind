/** Solar power and forecast metric card. */

import { Sun } from 'lucide-react'
import Card from '@/components/ui/Card'

interface SolarCardProps {
  powerKw: number | null
  forecastKwh: number | null
}

export default function SolarCard({ powerKw, forecastKwh }: SolarCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-pill bg-signal/15 text-signal">
          <Sun className="h-3.5 w-3.5" />
        </span>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Solar</span>
      </div>
      <div className="font-display text-4xl tracking-display text-foreground mb-3">
        {powerKw !== null ? `${powerKw.toFixed(1)}kW` : '—'}
      </div>
      <div className="text-xs text-muted-foreground">
        Today remaining: {forecastKwh !== null ? `${forecastKwh.toFixed(1)} kWh` : '—'}
      </div>
    </Card>
  )
}
