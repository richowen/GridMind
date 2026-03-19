/** History page — SOC, solar, price, and decisions charts over configurable time range. */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { historyApi } from '@/api/history'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { getPriceColor } from '@/types/domain'

const RANGES = [
  { label: '24h', hours: 24 },
  { label: '7d', hours: 168 },
  { label: '30d', hours: 720 },
]

export default function History() {
  const [hours, setHours] = useState(24)

  const { data: states } = useQuery({
    queryKey: ['states', hours],
    queryFn: () => historyApi.getStates(hours),
    refetchInterval: 60_000,
  })

  const { data: decisions } = useQuery({
    queryKey: ['decisions', hours],
    queryFn: () => historyApi.getRecommendations(hours),
    refetchInterval: 60_000,
  })

  const stateData = (states ?? []).reverse().map(s => ({
    time: new Date(s.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    soc: s.battery_soc,
    solar: s.solar_power_kw,
    price: s.current_price_pence,
    classification: null,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">History & Analytics</h1>
        <div className="flex gap-2">
          {RANGES.map(r => (
            <button
              key={r.hours}
              onClick={() => setHours(r.hours)}
              className={`px-3 py-1 text-sm rounded ${hours === r.hours ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'}`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* SOC Chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Battery State of Charge</h2>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={stateData}>
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} interval={Math.floor(stateData.length / 8)} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="%" domain={[0, 100]} />
            <Tooltip formatter={(v: number) => [`${v?.toFixed(0)}%`, 'SoC']} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4 }} />
            <Line type="monotone" dataKey="soc" stroke="#3b82f6" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Solar Chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Solar Generation</h2>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={stateData}>
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} interval={Math.floor(stateData.length / 8)} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="kW" />
            <Tooltip formatter={(v: number) => [`${v?.toFixed(1)}kW`, 'Solar']} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4 }} />
            <Area type="monotone" dataKey="solar" stroke="#eab308" fill="#eab30820" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Price Chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Electricity Price</h2>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={stateData}>
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} interval={Math.floor(stateData.length / 8)} />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="p" />
            <Tooltip formatter={(v: number) => [`${v?.toFixed(1)}p`, 'Price']} contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4 }} />
            <Bar dataKey="price" radius={[1, 1, 0, 0]}>
              {stateData.map((_, i) => <Cell key={i} fill="#3b82f6" />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Decisions Table */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">Decisions Log</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border">
                <th className="pb-2 pr-4">Time</th>
                <th className="pb-2 pr-4">Mode</th>
                <th className="pb-2 pr-4">SoC</th>
                <th className="pb-2 pr-4">Price</th>
                <th className="pb-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              {(decisions ?? []).slice(0, 50).map(d => (
                <tr key={d.id} className="border-b border-border/50">
                  <td className="py-1.5 pr-4 text-muted-foreground text-xs">
                    {new Date(d.timestamp).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-1.5 pr-4 font-medium">{d.recommended_mode ?? '—'}</td>
                  <td className="py-1.5 pr-4">{d.current_soc !== null ? `${d.current_soc.toFixed(0)}%` : '—'}</td>
                  <td className="py-1.5 pr-4">{d.current_price_pence !== null ? `${d.current_price_pence.toFixed(1)}p` : '—'}</td>
                  <td className="py-1.5 text-xs text-muted-foreground truncate max-w-xs">{d.decision_reason ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
