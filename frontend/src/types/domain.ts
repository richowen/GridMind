/** Domain types for UI state — derived from API types but UI-friendly. */

export type PriceClassification = 'negative' | 'cheap' | 'normal' | 'expensive'

export interface LiveState {
  battery_soc: number | null
  battery_mode: string | null
  solar_power_kw: number | null
  solar_forecast_today_kwh: number | null
  solar_forecast_next_hour_kw: number | null
  current_price_pence: number | null
  price_classification: PriceClassification | null
  recommended_mode: string | null
  decision_reason: string | null
  live_charge_rate_kw: number | null
  last_updated: string | null
}

export type WSMessage =
  | { type: 'state'; data: LiveState }
  | { type: 'optimization_result'; data: LiveState }
  | { type: 'prices_updated'; data: unknown[] }
  | { type: 'immersion_action'; data: unknown }
  | { type: 'ping'; data: null }

export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6

/**
 * Day names using Python weekday() convention: 0=Monday, 6=Sunday.
 * This matches the backend days_of_week storage format.
 */
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

// Note: classifyPrice() removed — use the `classification` field returned by the
// backend on every price record instead. Frontend thresholds would diverge from
// the DB settings that users configure in the Settings page.
