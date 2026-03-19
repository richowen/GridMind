/** API response types — mirrors backend Pydantic schemas exactly. */

export interface PriceOut {
  id: number
  valid_from: string
  valid_to: string
  price_pence: number
  classification: 'negative' | 'cheap' | 'normal' | 'expensive' | null
}

export interface PriceStats {
  min_price: number
  max_price: number
  mean_price: number
  median_price: number
  negative_count: number
  cheap_count: number
  expensive_count: number
  total_periods: number
}

export interface OptimizationResultOut {
  id: number
  timestamp: string
  current_soc: number | null
  current_solar_kw: number | null
  current_price_pence: number | null
  recommended_mode: string | null
  recommended_discharge_current: number | null
  optimization_status: string | null
  optimization_time_ms: number | null
  objective_value: number | null
  decision_reason: string | null
  next_action_time: string | null
}

export interface SystemStateOut {
  id: number
  timestamp: string
  battery_soc: number | null
  battery_mode: string | null
  battery_discharge_current: number | null
  solar_power_kw: number | null
  solar_forecast_today_kwh: number | null
  solar_forecast_next_hour_kw: number | null
  current_price_pence: number | null
  immersion_main_on: boolean | null
  immersion_lucy_on: boolean | null
}

export interface ImmersionDeviceOut {
  id: number
  name: string
  display_name: string
  switch_entity_id: string
  temp_sensor_entity_id: string | null
  is_enabled: boolean
  sort_order: number
}

export interface SmartRuleOut {
  id: number
  immersion_id: number
  rule_name: string
  is_enabled: boolean
  priority: number
  action: 'ON' | 'OFF'
  logic_operator: 'AND' | 'OR'
  price_enabled: boolean
  price_operator: string | null
  price_threshold_pence: number | null
  soc_enabled: boolean
  soc_operator: string | null
  soc_threshold_percent: number | null
  solar_enabled: boolean
  solar_operator: string | null
  solar_threshold_kw: number | null
  temp_enabled: boolean
  temp_operator: string | null
  temp_threshold_c: number | null
  time_enabled: boolean
  time_start: string | null
  time_end: string | null
}

export interface TempTargetOut {
  id: number
  immersion_id: number
  target_name: string
  target_temp_c: number
  target_time: string
  days_of_week: string
  heating_rate_c_per_hour: number
  buffer_minutes: number
  is_enabled: boolean
}

export interface ManualOverrideOut {
  id: number
  immersion_id: number
  immersion_name: string
  is_active: boolean
  desired_state: boolean
  source: string
  created_at: string
  expires_at: string
  cleared_at: string | null
  cleared_by: string | null
}

export interface OverrideStatusOut {
  immersion_id: number
  immersion_name: string
  has_active_override: boolean
  override: ManualOverrideOut | null
  time_remaining_minutes: number | null
}

export interface SettingOut {
  key: string
  value: string
  value_type: string
  category: string
  description: string | null
  updated_at: string | null
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  details: Record<string, unknown> | null
}

export interface SystemAction {
  id: number
  timestamp: string
  action_type: string
  entity_id: string
  old_value: string | null
  new_value: string
  source: string
  reason: string | null
  success: boolean
}
