/** Scannable list of price periods — pill rows, no charting library.
 * Used by the Dashboard ("next few hours") and the Prices page (full forecast). */

import Pill from '@/components/ui/Pill'
import { getPriceVariant } from '@/types/domain'
import type { PriceOut } from '@/types/api'

interface PriceListProps {
  prices: PriceOut[]
  vppEvent?: { start: string; end: string } | null
  /** Cap the number of rows rendered (e.g. dashboard shows fewer than the full Prices page). */
  limit?: number
}

function isVppSlot(validFrom: string, validTo: string, vppEvent?: { start: string; end: string } | null) {
  if (!vppEvent) return false
  const start = new Date(vppEvent.start).getTime()
  const end = new Date(vppEvent.end).getTime()
  const slotFrom = new Date(validFrom).getTime()
  const slotTo = new Date(validTo).getTime()
  return slotFrom < end && slotTo > start
}

export default function PriceList({ prices, vppEvent, limit }: PriceListProps) {
  const rows = limit ? prices.slice(0, limit) : prices

  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No price data available.</p>
  }

  return (
    <div className="divide-y divide-border/60">
      {rows.map(p => {
        const vpp = isVppSlot(p.valid_from, p.valid_to, vppEvent)
        return (
          <div
            key={p.id}
            className={`flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0 ${
              vpp ? 'bg-signal/5 -mx-2 px-2 rounded-md' : ''
            }`}
          >
            <span className="text-sm text-muted-foreground whitespace-nowrap">
              {new Date(p.valid_from).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
              {' – '}
              {new Date(p.valid_to).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
            </span>
            <span className="font-display text-sm tracking-display text-foreground flex-1 text-right pr-2">
              {p.price_pence.toFixed(1)}p
            </span>
            <div className="flex items-center gap-1.5 shrink-0">
              {vpp && <Pill variant="signal" size="xs">VPP</Pill>}
              <Pill variant={getPriceVariant(p.classification)} size="xs">
                {p.classification ?? 'normal'}
              </Pill>
            </div>
          </div>
        )
      })}
    </div>
  )
}
