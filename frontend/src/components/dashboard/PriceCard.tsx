/** Current electricity price card with classification colour. */

import { Zap } from 'lucide-react'
import { getPriceColor } from '@/types/domain'
import type { PriceClassification } from '@/types/domain'

interface PriceCardProps {
  pricePence: number | null
  classification: PriceClassification | null
}

export default function PriceCard({ pricePence, classification }: PriceCardProps) {
  const color = getPriceColor(classification)
  const label = classification
    ? classification.charAt(0).toUpperCase() + classification.slice(1)
    : 'Unknown'

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Price Now</span>
      </div>
      <div className="text-3xl font-bold mb-1" style={{ color }}>
        {pricePence !== null ? `${pricePence.toFixed(1)}p` : '—'}
      </div>
      <div className="text-xs" style={{ color }}>{label}</div>
    </div>
  )
}
