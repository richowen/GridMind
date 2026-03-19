/** Dashboard page — live overview of battery, solar, price, and immersion status. */

import { useQuery } from '@tanstack/react-query'
import { useLiveState } from '@/hooks/useLiveState'
import { optimizationApi } from '@/api/optimization'
import { historyApi } from '@/api/history'
import BatteryCard from '@/components/dashboard/BatteryCard'
import SolarCard from '@/components/dashboard/SolarCard'
import PriceCard from '@/components/dashboard/PriceCard'
import ModeCard from '@/components/dashboard/ModeCard'
import PriceSparkline from '@/components/charts/PriceSparkline'
import RecentDecisions from '@/components/dashboard/RecentDecisions'

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
          dischargeAmps={state.battery_discharge_current}
        />
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          Next 12 Hours — Price Forecast
        </h2>
        <PriceSparkline prices={prices ?? []} />
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          Recent Decisions
        </h2>
        <RecentDecisions decisions={decisions ?? []} />
      </div>
    </div>
  )
}
