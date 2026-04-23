import {api} from './client'

export interface ConditionTrace {
  type:'price'|'soc'|'solar'|'temp'|'time'
  enabled:boolean
  skipped:boolean
  actual_value:number|null
  operator:string|null
  threshold:number|null
  passed:boolean|null
}
export interface RuleTrace {
  rule_name:string
  priority:number
  enabled:boolean
  action:string
  logic_operator:string
  matched:boolean
  conditions:ConditionTrace[]
}
export interface DeviceDebugResult {
  device_name:string
  device_id:number
  switch_entity_id:string
  temp_c:number|null
  active_override:string|null
  final_decision:{action:boolean;source:string;reason:string}
  rule_traces:RuleTrace[]
}
export interface LpDecisionTrace {
  mode:string
  reason:string
  status:string
  current_slot_price_pence:number|null
  battery_soc:number|null
  solar_power_kw:number|null
  objective_value:number|null
  optimization_time_ms:number|null
  last_run:string|null
}
export interface WhyResponse {
  timestamp:string
  readings:Record<string,number|string|null>
  lp_decision:LpDecisionTrace
  immersion_devices:DeviceDebugResult[]
}

export async function fetchWhy():Promise<WhyResponse> {
  return api.get<WhyResponse>('/dev/why')
}

export async function switchImmersion(device_id:number, state:boolean):Promise<{success:boolean;entity_id:string;state:boolean}> {
  return api.post('/dev/immersion-switch',{device_id,state})
}
