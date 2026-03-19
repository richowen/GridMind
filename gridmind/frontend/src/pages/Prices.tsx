/** Prices page — 48-hour price forecast chart with stats and table. */

import { useQuery, useMutation } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { optimizationApi } from '@/api/optimization'
import { getPriceColor } from '@/types/domain'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts'

export default function Prices() {
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

  const chartData = (prices ?? []).map(p => ({
    time: new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    price: p.price_pence,
    classification: p.classification,
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
              {chartData.map((entry, index) => (
                <Cell key={index} fill={getPriceColor(entry.classification)} />
              ))}
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
            {(prices ?? []).map(p => (
              <tr key={p.id} className="border-t border-border/50 hover:bg-accent/20">
                <td className="px-4 py-2 text-muted-foreground">
                  {new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                  {' – '}
                  {new Date(p.valid_to).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                </td>
                <td className="px-4 py-2 font-medium" style={{ color: getPriceColor(p.classification) }}>
                  {p.price_pence.toFixed(1)}p
                </td>
                <td className="px-4 py-2 capitalize text-muted-foreground">{p.classification ?? 'normal'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
