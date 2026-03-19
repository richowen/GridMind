/** Solar power and forecast card. */

import { Sun } from 'lucide-react'

interface SolarCardProps {
  powerKw: number | null
  forecastKwh: number | null
}

export default function SolarCard({ powerKw, forecastKwh }: SolarCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sun className="h-4 w-4 text-yellow-400" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Solar</span>
      </div>
      <div className="text-3xl font-bold text-foreground mb-1">
        {powerKw !== null ? `${powerKw.toFixed(1)} kW` : '—'}
      </div>
      <div className="text-xs text-muted-foreground">
        Today remaining: {forecastKwh !== null ? `${forecastKwh.toFixed(1)} kWh` : '—'}
      </div>
    </div>
  )
}
