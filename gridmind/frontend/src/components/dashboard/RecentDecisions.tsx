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
          <tr className="text-left text-xs text-muted-foreground border-b border-border">
            <th className="pb-2 pr-4">Time</th>
            <th className="pb-2 pr-4">Mode</th>
            <th className="pb-2 pr-4">SoC</th>
            <th className="pb-2 pr-4">Price</th>
            <th className="pb-2 pr-4">Solar</th>
            <th className="pb-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {decisions.slice(0, 10).map((d) => (
            <tr key={d.id} className="border-b border-border/50 hover:bg-accent/20">
              <td className="py-1.5 pr-4 text-muted-foreground">
                {new Date(d.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              </td>
              <td className="py-1.5 pr-4 font-medium">{d.recommended_mode ?? '—'}</td>
              <td className="py-1.5 pr-4">{d.current_soc !== null ? `${d.current_soc.toFixed(0)}%` : '—'}</td>
              <td className="py-1.5 pr-4">{d.current_price_pence !== null ? `${d.current_price_pence.toFixed(1)}p` : '—'}</td>
              <td className="py-1.5 pr-4">{d.current_solar_kw !== null ? `${d.current_solar_kw.toFixed(1)}kW` : '—'}</td>
              <td className="py-1.5 text-muted-foreground text-xs truncate max-w-xs">{d.decision_reason ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
