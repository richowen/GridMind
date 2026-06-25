/** Prices page — 48-hour price forecast chart with stats and table. */

import { useQuery, useMutation } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { optimizationApi } from '@/api/optimization'
import { getPriceColor } from '@/types/domain'
import { useLiveState } from '@/hooks/useLiveState'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'

export default function Prices() {
  const { state } = useLiveState()

  const { data: prices, refetch } = useQuery({
    queryKey: ['prices', 48],
    queryFn: () => optimizationApi.getCurrentPrices(48),
    refetchInterval: 300_000,
  })

  const { data: stats } = useQuery({
    queryKey: ['price-stats'],
    queryFn: optimizationApi.getPriceStats,
    refetchInterval: 300_000,
  })

  const refreshMutation = useMutation({ mutationFn: optimizationApi.refreshPrices })

  const isVppSlot = (validFrom: string, validTo: string) => {
    if (!state.vpp_event) return false
    const start = new Date(state.vpp_event.start).getTime()
    const end = new Date(state.vpp_event.end).getTime()
    const slotFrom = new Date(validFrom).getTime()
    const slotTo = new Date(validTo).getTime()
    return slotFrom < end && slotTo > start
  }

  const chartData = (prices ?? []).map(p => ({
    time: new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    price: p.price_pence,
    classification: p.classification,
    valid_from: p.valid_from,
    valid_to: p.valid_to,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">48-Hour Price Forecast</h1>
        <button
          onClick={() => { refreshMutation.mutate(); refetch() }}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} interval={5} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="p" />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(1)}p`, 'Price']}
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4 }}
            />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
            <Bar dataKey="price" radius={[2, 2, 0, 0]}>
              {chartData.map((entry, index) => {
                const isVpp = isVppSlot(entry.valid_from, entry.valid_to)
                return (
                  <Cell
                    key={index}
                    fill={getPriceColor(entry.classification)}
                    stroke={isVpp ? '#f59e0b' : undefined}
                    strokeWidth={isVpp ? 2 : 0}
                  />
                )
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {stats && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Min', value: `${stats.min_price.toFixed(1)}p` },
            { label: 'Max', value: `${stats.max_price.toFixed(1)}p` },
            { label: 'Avg', value: `${stats.mean_price.toFixed(1)}p` },
            { label: 'Negative', value: `${stats.negative_count} periods` },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-lg border border-border bg-card p-3 text-center">
              <div className="text-xs text-muted-foreground">{label}</div>
              <div className="text-lg font-bold">{value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50">
            <tr className="text-left text-xs text-muted-foreground">
              <th className="px-4 py-2">Time</th>
              <th className="px-4 py-2">Price</th>
              <th className="px-4 py-2">Classification</th>
            </tr>
          </thead>
          <tbody>
            {(prices ?? []).map(p => {
              const isVpp = isVppSlot(p.valid_from, p.valid_to)
              return (
                <tr
                  key={p.id}
                  className={`border-t border-border/50 hover:bg-accent/20 transition-colors ${
                    isVpp ? 'bg-amber-500/10 hover:bg-amber-500/15 dark:bg-amber-500/5 dark:hover:bg-amber-500/10' : ''
                  }`}
                >
                  <td className="px-4 py-2 text-muted-foreground">
                    {new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                    {' – '}
                    {new Date(p.valid_to).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-4 py-2 font-medium" style={{ color: getPriceColor(p.classification) }}>
                    {p.price_pence.toFixed(1)}p
                  </td>
                  <td className="px-4 py-2 capitalize text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <span>{p.classification ?? 'normal'}</span>
                      {isVpp && (
                        <span className="text-[10px] bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30 px-1.5 py-0.5 rounded font-bold uppercase tracking-wide">
                          VPP Event
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
