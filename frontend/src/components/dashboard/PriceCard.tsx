/** Current electricity price metric card with classification pill. */

import { Zap } from 'lucide-react'
import Card from '@/components/ui/Card'
import Pill from '@/components/ui/Pill'
import { getPriceVariant } from '@/types/domain'
import type { PriceClassification } from '@/types/domain'

interface PriceCardProps {
  pricePence: number | null
  classification: PriceClassification | null
}

export default function PriceCard({ pricePence, classification }: PriceCardProps) {
  const label = classification
    ? classification.charAt(0).toUpperCase() + classification.slice(1)
    : 'Unknown'

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-pill bg-signal/15 text-signal">
          <Zap className="h-3.5 w-3.5" />
        </span>
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Price Now</span>
      </div>
      <div className="font-display text-4xl tracking-display text-foreground mb-3">
        {pricePence !== null ? `${pricePence.toFixed(1)}p` : '—'}
      </div>
      <Pill variant={getPriceVariant(classification)}>{label}</Pill>
    </Card>
  )
}
