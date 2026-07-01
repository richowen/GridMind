/** History page — decisions log over a configurable time range. Charts live in Grafana. */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { historyApi } from '@/api/history'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

const RANGES = [
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
]

export default function History() {
  const [hours, setHours] = useState(24)

  const { data: decisions } = useQuery({
    queryKey: ['decisions', hours],
    queryFn: () => historyApi.getRecommendations(hours),
    refetchInterval: 60_000,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl tracking-display text-foreground">Decisions Log</h1>
        <div className="flex gap-1.5 rounded-nav border border-border bg-card p-1">
          {RANGES.map(r => (
            <Button
              key={r.hours}
              variant={hours === r.hours ? 'signal' : 'ghost'}
              onClick={() => setHours(r.hours)}
              className="px-3 py-1 text-xs"
            >
              {r.label}
            </Button>
          ))}
        </div>
      </div>

      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground uppercase tracking-wide border-b border-border">
                <th className="p-4 font-medium">Time</th>
                <th className="p-4 font-medium">Mode</th>
                <th className="p-4 font-medium">SoC</th>
                <th className="p-4 font-medium">Price</th>
                <th className="p-4 font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {(decisions ?? []).slice(0, 100).map(d => (
                <tr key={d.id} className="border-b border-border/60 last:border-0 hover:bg-accent/40 transition-colors">
                  <td className="p-4 text-muted-foreground text-xs whitespace-nowrap">
                    {new Date(d.timestamp).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="p-4 font-medium text-foreground whitespace-nowrap">{d.recommended_mode ?? '—'}</td>
                  <td className="p-4 text-foreground">{d.current_soc !== null ? `${d.current_soc.toFixed(0)}%` : '—'}</td>
                  <td className="p-4 text-foreground">{d.current_price_pence !== null ? `${d.current_price_pence.toFixed(1)}p` : '—'}</td>
                  <td className="p-4 text-xs text-muted-foreground truncate max-w-xs">{d.decision_reason ?? '—'}</td>
                </tr>
              ))}
              {(!decisions || decisions.length === 0) && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-sm text-muted-foreground">
                    No decisions recorded for this range.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
