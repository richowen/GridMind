/**LP schedule table: SOC + charge/discharge/import/export per half-hour period.*/
import type { SimPeriodResult } from '@/api/dev'

interface Props { periods: SimPeriodResult[]; capacityKwh: number }

function slot(iso: string) {
  try {
    const d = new Date(iso)
    return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}`
  } catch {
    return ''
  }
}

export default function ResultChart({ periods }: Props) {
  if (!periods.length) {
    return <div className="h-24 flex items-center justify-center text-xs text-muted-foreground">No data</div>
  }

  return (
    <div className="overflow-x-auto max-h-80">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-card">
          <tr className="text-left text-muted-foreground uppercase tracking-wide border-b border-border">
            <th className="py-2 pr-3 font-medium">Time</th>
            <th className="py-2 pr-3 font-medium">Price</th>
            <th className="py-2 pr-3 font-medium">Charge</th>
            <th className="py-2 pr-3 font-medium">Discharge</th>
            <th className="py-2 pr-3 font-medium">Import</th>
            <th className="py-2 pr-3 font-medium">Export</th>
            <th className="py-2 font-medium">SOC</th>
          </tr>
        </thead>
        <tbody>
          {periods.map((p, i) => (
            <tr key={i} className="border-b border-border/50 last:border-0">
              <td className="py-1.5 pr-3 text-muted-foreground whitespace-nowrap">{slot(p.valid_from)}</td>
              <td className="py-1.5 pr-3 text-foreground">{p.price_pence.toFixed(1)}p</td>
              <td className="py-1.5 pr-3 text-foreground">{p.charge_kw > 0 ? `${p.charge_kw.toFixed(2)}kW` : '—'}</td>
              <td className="py-1.5 pr-3 text-foreground">{p.discharge_kw > 0 ? `${p.discharge_kw.toFixed(2)}kW` : '—'}</td>
              <td className="py-1.5 pr-3 text-foreground">{p.grid_import_kw > 0 ? `${p.grid_import_kw.toFixed(2)}kW` : '—'}</td>
              <td className="py-1.5 pr-3 text-foreground">{p.grid_export_kw > 0 ? `${p.grid_export_kw.toFixed(2)}kW` : '—'}</td>
              <td className="py-1.5 font-medium text-foreground">{p.soc_pct.toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
