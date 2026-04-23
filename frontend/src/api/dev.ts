import { api } from './client'

export interface SimPrice {valid_from:string;price_pence:number}
export interface SimImmersionRule {
  rule_name:string;priority:number;action:'ON'|'OFF';logic_operator:'AND'|'OR';is_enabled:boolean
  price_enabled:boolean;price_operator:string;price_threshold_pence:number
  soc_enabled:boolean;soc_operator:string;soc_threshold_percent:number
  solar_enabled:boolean;solar_operator:string;solar_threshold_kw:number
  temp_enabled:boolean;temp_operator:string;temp_threshold_c:number
  time_enabled:boolean;time_start:string;time_end:string
}
export interface SimImmersionInput {
  battery_soc:number;solar_power_kw:number;current_price_pence:number
  current_temp_c:number|null;rules:SimImmersionRule[]
}
export interface SimRequest {
  battery_soc:number;solar_power_kw:number
  live_charge_rate_kw:number|null;live_battery_voltage_v:number|null
  battery_capacity_kwh:number;battery_max_charge_kw:number
  battery_max_discharge_kw:number;battery_efficiency:number
  battery_min_soc:number;battery_max_soc:number;battery_voltage_v:number
  grid_import_limit_kw:number;grid_export_limit_kw:number
  export_price_pence:number;assumed_load_kw:number
  force_charge_threshold_kw:number;force_discharge_threshold_kw:number
  force_discharge_export_min_kw:number;optimization_horizon_hours:number
  prices:SimPrice[];immersion:SimImmersionInput|null
}
export interface SimPeriodResult {
  slot:number;valid_from:string;price_pence:number;solar_kw:number
  charge_kw:number;discharge_kw:number;grid_import_kw:number;grid_export_kw:number
  soc_kwh:number;soc_pct:number
}
export interface SimImmersionResult {action:boolean;source:string;reason:string}
export interface SimResponse {
  recommended_mode:string;decision_reason:string;optimization_status:string
  objective_value:number|null;optimization_time_ms:number
  recommended_discharge_current:number;periods:SimPeriodResult[]
  immersion:SimImmersionResult|null
}

export const DEFAULT_SIM_REQUEST: SimRequest = {
  battery_soc:50,solar_power_kw:3,live_charge_rate_kw:null,live_battery_voltage_v:null,
  battery_capacity_kwh:20,battery_max_charge_kw:10.5,battery_max_discharge_kw:5,
  battery_efficiency:0.95,battery_min_soc:10,battery_max_soc:100,battery_voltage_v:48,
  grid_import_limit_kw:15,grid_export_limit_kw:5,export_price_pence:15,assumed_load_kw:2,
  force_charge_threshold_kw:0.5,force_discharge_threshold_kw:0.5,
  force_discharge_export_min_kw:0.05,optimization_horizon_hours:24,
  prices:[],immersion:null,
}

export function generateFlatPrices(pence:number, n=48):SimPrice[] {
  const base = new Date()
  base.setMinutes(base.getMinutes()<30?0:30,0,0)
  return Array.from({length:n},(_,i)=>{
    const d = new Date(base.getTime()+i*30*60*1000)
    return {valid_from:d.toISOString(),price_pence:pence}
  })
}

export async function runSimulation(req:SimRequest):Promise<SimResponse> {
  return api.post<SimResponse>('/dev/simulate',req)
}
