/** Prices page — 48-hour price forecast list with stats. */

import { useQuery, useMutation } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { optimizationApi } from '@/api/optimization'
import { useLiveState } from '@/hooks/useLiveState'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import PriceList from '@/components/prices/PriceList'

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl tracking-display text-foreground">48-Hour Price Forecast</h1>
        <Button
          variant="outline"
          onClick={() => { refreshMutation.mutate(); refetch() }}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Min', value: `${stats.min_price.toFixed(1)}p` },
            { label: 'Max', value: `${stats.max_price.toFixed(1)}p` },
            { label: 'Avg', value: `${stats.mean_price.toFixed(1)}p` },
            { label: 'Negative', value: `${stats.negative_count} periods` },
          ].map(({ label, value }) => (
            <Card key={label} padding="sm" className="text-center">
              <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">{label}</div>
              <div className="font-display text-xl tracking-display text-foreground">{value}</div>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <PriceList prices={prices ?? []} vppEvent={state.vpp_event} />
      </Card>
    </div>
  )
}
