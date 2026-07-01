/** Recent optimization decisions table. */

import type { OptimizationResultOut } from '@/types/api'

interface RecentDecisionsProps {
  decisions: OptimizationResultOut[]
}

export default function RecentDecisions({ decisions }: RecentDecisionsProps) {
  if (!decisions.length) {
    return <p className="text-sm text-muted-foreground">No decisions yet.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-muted-foreground uppercase tracking-wide border-b border-border">
            <th className="pb-3 pr-4 font-medium">Time</th>
            <th className="pb-3 pr-4 font-medium">Mode</th>
            <th className="pb-3 pr-4 font-medium">SoC</th>
            <th className="pb-3 pr-4 font-medium">Price</th>
            <th className="pb-3 pr-4 font-medium">Solar</th>
            <th className="pb-3 font-medium">Reason</th>
          </tr>
        </thead>
        <tbody>
          {decisions.slice(0, 10).map((d) => (
            <tr key={d.id} className="border-b border-border/60 last:border-0 hover:bg-accent/40 transition-colors">
              <td className="py-2.5 pr-4 text-muted-foreground whitespace-nowrap">
                {new Date(d.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              </td>
              <td className="py-2.5 pr-4 font-medium text-foreground whitespace-nowrap">{d.recommended_mode ?? '—'}</td>
              <td className="py-2.5 pr-4 text-foreground">{d.current_soc !== null ? `${d.current_soc.toFixed(0)}%` : '—'}</td>
              <td className="py-2.5 pr-4 text-foreground">{d.current_price_pence !== null ? `${d.current_price_pence.toFixed(1)}p` : '—'}</td>
              <td className="py-2.5 pr-4 text-foreground">{d.current_solar_kw !== null ? `${d.current_solar_kw.toFixed(1)}kW` : '—'}</td>
              <td className="py-2.5 text-muted-foreground truncate max-w-xs">{d.decision_reason ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
