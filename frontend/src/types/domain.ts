/** Domain types for UI state — derived from API types but UI-friendly. */

export type PriceClassification = 'negative' | 'cheap' | 'normal' | 'expensive'

export interface LiveState {
  battery_soc: number | null
  battery_mode: string | null
  battery_discharge_current: number | null
  solar_power_kw: number | null
  solar_forecast_today_kwh: number | null
  current_price_pence: number | null
  price_classification: PriceClassification | null
  recommended_mode: string | null
  decision_reason: string | null
  last_updated: string | null
}

export type WSMessage =
  | { type: 'state'; data: LiveState }
  | { type: 'optimization_result'; data: LiveState }
  | { type: 'prices_updated'; data: unknown[] }
  | { type: 'immersion_action'; data: unknown }
  | { type: 'ping'; data: null }
  | { type: 'pong' }

export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6

export const DAY_NAMES: Record<DayOfWeek, string> = {
  0: 'Mon',
  1: 'Tue',
  2: 'Wed',
  3: 'Thu',
  4: 'Fri',
  5: 'Sat',
  6: 'Sun',
}

export function parseDaysOfWeek(csv: string): DayOfWeek[] {
  return csv.split(',').map(Number) as DayOfWeek[]
}

export function formatDaysOfWeek(days: DayOfWeek[]): string {
  return days.map(d => DAY_NAMES[d]).join(', ')
}

export function getPriceColor(classification: PriceClassification | null): string {
  switch (classification) {
    case 'negative': return '#22c55e'   // green
    case 'cheap': return '#eab308'      // yellow
    case 'expensive': return '#ef4444'  // red
    default: return '#3b82f6'           // blue (normal)
  }
}

export function classifyPrice(
  pence: number,
  negThreshold = 0,
  cheapThreshold = 10,
  expThreshold = 25,
): PriceClassification {
  if (pence < negThreshold) return 'negative'
  if (pence < cheapThreshold) return 'cheap'
  if (pence > expThreshold) return 'expensive'
  return 'normal'
}
