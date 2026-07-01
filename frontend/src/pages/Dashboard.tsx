/** Dashboard page — live overview of battery, solar, price, and immersion status. */

import { useQuery } from '@tanstack/react-query'
import { useLiveState } from '@/hooks/useLiveState'
import { optimizationApi } from '@/api/optimization'
import { historyApi } from '@/api/history'
import Card from '@/components/ui/Card'
import BatteryCard from '@/components/dashboard/BatteryCard'
import SolarCard from '@/components/dashboard/SolarCard'
import PriceCard from '@/components/dashboard/PriceCard'
import ModeCard from '@/components/dashboard/ModeCard'
import PriceList from '@/components/prices/PriceList'
import RecentDecisions from '@/components/dashboard/RecentDecisions'
import VppEventBanner from '@/components/dashboard/VppEventBanner'

export default function Dashboard() {
  const { state } = useLiveState()

  const { data: prices } = useQuery({
    queryKey: ['prices', 12],
    queryFn: () => optimizationApi.getCurrentPrices(12),
    refetchInterval: 60_000,
  })

  const { data: decisions } = useQuery({
    queryKey: ['decisions', 2],
    queryFn: () => historyApi.getRecommendations(2),
    refetchInterval: 30_000,
  })

  return (
    <div className="space-y-6">
      {state.vpp_event && <VppEventBanner event={state.vpp_event} />}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <BatteryCard soc={state.battery_soc} mode={state.battery_mode} />
        <SolarCard
          powerKw={state.solar_power_kw}
          forecastKwh={state.solar_forecast_today_kwh}
        />
        <PriceCard
          pricePence={state.current_price_pence}
          classification={state.price_classification}
        />
        <ModeCard
          mode={state.recommended_mode}
          reason={state.decision_reason}
        />
      </div>

      <Card>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Next 6 Hours
        </h2>
        <PriceList prices={prices ?? []} vppEvent={state.vpp_event} limit={12} />
      </Card>

      <Card>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Recent Decisions
        </h2>
        <RecentDecisions decisions={decisions ?? []} />
      </Card>
    </div>
  )
}
