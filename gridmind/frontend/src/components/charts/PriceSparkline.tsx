/** Compact 12-hour price bar chart for the dashboard. */

import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getPriceColor } from '@/types/domain'
import type { PriceOut } from '@/types/api'

interface PriceSparklineProps {
  prices: PriceOut[]
}

export default function PriceSparkline({ prices }: PriceSparklineProps) {
  if (!prices.length) {
    return <div className="h-20 flex items-center justify-center text-xs text-muted-foreground">No price data</div>
  }

  const data = prices.slice(0, 24).map(p => ({
    time: new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
    price: p.price_pence,
    classification: p.classification,
  }))

  return (
    <ResponsiveContainer width="100%" height={80}>
      <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} interval={3} />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)}p`, 'Price']}
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 4 }}
          labelStyle={{ color: '#94a3b8' }}
        />
        <Bar dataKey="price" radius={[2, 2, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={getPriceColor(entry.classification)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
