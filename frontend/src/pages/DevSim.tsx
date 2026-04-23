/**Dev Simulator — manually set all inputs and see LP optimizer + rules engine output.*/
import {useState,type ReactNode} from 'react'
import {
  runSimulation,DEFAULT_SIM_REQUEST,SOLAR_PROFILES,
  type SimRequest,type SimResponse,type SimImmersionRule,type SolarProfile,
} from '@/api/dev'
import PriceGrid from '@/components/dev/PriceGrid'
import ResultChart from '@/components/dev/ResultChart'

const OPERATORS=['<','<=','>','>=','==']

function num(v:string,fallback:number){const n=parseFloat(v);return isNaN(n)?fallback:n}

function Field({label,value,onChange,step='1',min,max}:{
  label:string;value:number;onChange:(v:number)=>void;step?:string;min?:number;max?:number
}){
  return(
    <label className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <input type="number" step={step} min={min} max={max} value={value}
        onChange={e=>onChange(num(e.target.value,value))}
        className="w-full px-2 py-1 text-sm rounded border border-border bg-background focus:outline-none focus:ring-1 focus:ring-primary"/>
    </label>
  )
}

function Section({title,children}:{title:string;children:ReactNode}){
  return(
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {children}
    </div>
  )
}

function modeBadge(mode:string){
  if(mode==='Force Charge') return 'bg-green-500/20 text-green-300 border-green-500/30'
  if(mode==='Force Discharge') return 'bg-red-500/20 text-red-300 border-red-500/30'
  return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
}

const DEFAULT_RULE:SimImmersionRule={
  rule_name:'New Rule',priority:10,action:'ON',logic_operator:'AND',is_enabled:true,
  price_enabled:false,price_operator:'<',price_threshold_pence:10,
  soc_enabled:false,soc_operator:'>',soc_threshold_percent:50,
  solar_enabled:false,solar_operator:'>',solar_threshold_kw:2,
  temp_enabled:false,temp_operator:'<',temp_threshold_c:50,
  time_enabled:false,time_start:'00:00',time_end:'23:59',
}

export default function DevSim(){
  const [req,setReq]=useState<SimRequest>({...DEFAULT_SIM_REQUEST})
  const [result,setResult]=useState<SimResponse|null>(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string|null>(null)
  const [showImmersion,setShowImmersion]=useState(false)

  const set=(key:keyof SimRequest,v:any)=>setReq(r=>({...r,[key]:v}))

  const run=async()=>{
    setLoading(true);setError(null)
    try{setResult(await runSimulation(req))}
    catch(e:any){setError(e?.message??'Simulation failed')}
    finally{setLoading(false)}
  }

  // immersion helpers
  const imm=req.immersion
  const setImm=(k:string,v:any)=>req.immersion&&set('immersion',{...req.immersion,[k]:v})
  const toggleImmersion=(on:boolean)=>set('immersion',on?{battery_soc:req.battery_soc,solar_power_kw:req.solar_power_kw,current_price_pence:15,current_temp_c:45,rules:[]}:null)
  const addRule=()=>imm&&setImm('rules',[...imm.rules,{...DEFAULT_RULE}])
  const setRule=(i:number,k:keyof SimImmersionRule,v:any)=>{
    if(!imm)return
    const rules=[...imm.rules]
    rules[i]={...rules[i],[k]:v}
    setImm('rules',rules)
  }
  const removeRule=(i:number)=>imm&&setImm('rules',imm.rules.filter((_:any,j:number)=>j!==i))

  return(
    <div className="space-y-4 max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Dev Simulator</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Run LP optimizer and rules engine with custom inputs — no HA or DB required</p>
        </div>
        <button onClick={run} disabled={loading}
          className="px-5 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/80 disabled:opacity-50 transition-colors">
          {loading?'Running…':'▶ Run Simulation'}
        </button>
      </div>

      {error&&<div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{error}</div>}

      {/* Result banner */}
      {result&&(
        <div className={`rounded-lg border p-4 ${modeBadge(result.recommended_mode)}`}>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <span className="text-xs uppercase tracking-wide opacity-70">Recommendation</span>
              <div className="text-2xl font-bold mt-0.5">{result.recommended_mode}</div>
              <div className="text-sm mt-1 opacity-80">{result.decision_reason}</div>
            </div>
            <div className="text-right text-sm space-y-1 opacity-80">
              <div>Status: <span className="font-medium">{result.optimization_status}</span></div>
              <div>Objective: <span className="font-medium">{result.objective_value!=null?`${result.objective_value.toFixed(2)}p`:'—'}</span></div>
              <div>Solve time: <span className="font-medium">{result.optimization_time_ms.toFixed(0)}ms</span></div>
              <div>Max discharge: <span className="font-medium">{result.recommended_discharge_current}A</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      {result&&result.periods.length>0&&(
        <Section title="LP Schedule — SOC & Power per Half-Hour">
          <ResultChart periods={result.periods} capacityKwh={req.battery_capacity_kwh}/>
        </Section>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* System State */}
        <Section title="System State">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Battery SOC %" value={req.battery_soc} onChange={v=>set('battery_soc',v)} step="1" min={0} max={100}/>
            <Field label="Solar Peak kW (array max)" value={req.solar_power_kw} onChange={v=>set('solar_power_kw',v)} step="0.1" min={0}/>
            <Field label="Live BMS Charge Rate kW (opt)" value={req.live_charge_rate_kw??0} onChange={v=>set('live_charge_rate_kw',v||null)} step="0.1" min={0}/>
            <Field label="Live Battery Voltage V (opt)" value={req.live_battery_voltage_v??0} onChange={v=>set('live_battery_voltage_v',v||null)} step="0.1" min={0}/>
          </div>
          {/* Solar profile row */}
          <div className="mt-3 space-y-2">
            <span className="text-xs text-muted-foreground">Solar Profile</span>
            <div className="grid grid-cols-4 gap-2">
              {SOLAR_PROFILES.map(p=>(
                <button key={p.value}
                  onClick={()=>set('solar_profile',p.value as SolarProfile)}
                  title={p.desc}
                  className={`text-xs px-2 py-1.5 rounded border transition-colors ${req.solar_profile===p.value?'border-primary bg-primary/20 text-primary-foreground':'border-border bg-background text-muted-foreground hover:border-primary/50'}`}>
                  {p.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground whitespace-nowrap">Scale (season)</span>
              <input type="range" min={0} max={1} step={0.01}
                value={req.solar_scale}
                onChange={e=>set('solar_scale',parseFloat(e.target.value))}
                className="flex-1 accent-primary"/>
              <span className="text-xs font-mono w-10 text-right text-foreground">{Math.round(req.solar_scale*100)}%</span>
              <span className="text-xs text-muted-foreground">≈{(req.solar_power_kw*req.solar_scale).toFixed(1)}kW pk</span>
            </div>
          </div>
        </Section>

        {/* Battery Settings */}
        <Section title="Battery Settings">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Capacity kWh" value={req.battery_capacity_kwh} onChange={v=>set('battery_capacity_kwh',v)} step="0.1" min={1}/>
            <Field label="Max Charge kW" value={req.battery_max_charge_kw} onChange={v=>set('battery_max_charge_kw',v)} step="0.1" min={0}/>
            <Field label="Max Discharge kW" value={req.battery_max_discharge_kw} onChange={v=>set('battery_max_discharge_kw',v)} step="0.1" min={0}/>
            <Field label="Efficiency (0-1)" value={req.battery_efficiency} onChange={v=>set('battery_efficiency',v)} step="0.01" min={0.5} max={1}/>
            <Field label="Min SOC %" value={req.battery_min_soc} onChange={v=>set('battery_min_soc',v)} step="1" min={0} max={100}/>
            <Field label="Max SOC %" value={req.battery_max_soc} onChange={v=>set('battery_max_soc',v)} step="1" min={0} max={100}/>
            <Field label="Battery Voltage V" value={req.battery_voltage_v} onChange={v=>set('battery_voltage_v',v)} step="1" min={12}/>
          </div>
        </Section>

        {/* Grid & Pricing */}
        <Section title="Grid & Pricing">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Grid Import Limit kW" value={req.grid_import_limit_kw} onChange={v=>set('grid_import_limit_kw',v)} step="0.5" min={0}/>
            <Field label="Grid Export Limit kW" value={req.grid_export_limit_kw} onChange={v=>set('grid_export_limit_kw',v)} step="0.5" min={0}/>
            <Field label="Export Price p/kWh" value={req.export_price_pence} onChange={v=>set('export_price_pence',v)} step="0.1" min={0}/>
            <Field label="Assumed Load kW" value={req.assumed_load_kw} onChange={v=>set('assumed_load_kw',v)} step="0.1" min={0}/>
            <Field label="Force Charge Threshold kW" value={req.force_charge_threshold_kw} onChange={v=>set('force_charge_threshold_kw',v)} step="0.1" min={0}/>
            <Field label="Force Discharge Threshold kW" value={req.force_discharge_threshold_kw} onChange={v=>set('force_discharge_threshold_kw',v)} step="0.1" min={0}/>
            <Field label="Force Discharge Export Min kW" value={req.force_discharge_export_min_kw} onChange={v=>set('force_discharge_export_min_kw',v)} step="0.01" min={0}/>
            <Field label="Opt Horizon Hours" value={req.optimization_horizon_hours} onChange={v=>set('optimization_horizon_hours',v)} step="1" min={1} max={48}/>
          </div>
        </Section>

        {/* Immersion Simulator */}
        <Section title="Immersion Simulator">
          <div className="flex items-center gap-3 mb-2">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={showImmersion}
                onChange={e=>{setShowImmersion(e.target.checked);toggleImmersion(e.target.checked)}}
                className="rounded"/>
              Enable immersion simulation
            </label>
          </div>
          {imm&&(
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Battery SOC %" value={imm.battery_soc} onChange={v=>setImm('battery_soc',v)} step="1" min={0} max={100}/>
                <Field label="Solar kW" value={imm.solar_power_kw} onChange={v=>setImm('solar_power_kw',v)} step="0.1" min={0}/>
                <Field label="Current Price p" value={imm.current_price_pence} onChange={v=>setImm('current_price_pence',v)} step="0.1"/>
                <Field label="Water Temp °C" value={imm.current_temp_c??45} onChange={v=>setImm('current_temp_c',v)} step="0.5"/>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Rules</span>
                  <button onClick={addRule} className="text-xs px-2 py-0.5 rounded bg-accent hover:bg-accent/80">+ Add Rule</button>
                </div>
                {imm.rules.map((r:SimImmersionRule,i:number)=>(
                  <div key={i} className="rounded border border-border p-2 space-y-2 text-xs bg-background/50">
                    <div className="flex items-center gap-2">
                      <input value={r.rule_name} onChange={e=>setRule(i,'rule_name',e.target.value)}
                        className="flex-1 px-1.5 py-0.5 rounded border border-border bg-background text-xs"/>
                      <select value={r.action} onChange={e=>setRule(i,'action',e.target.value)}
                        className="px-1.5 py-0.5 rounded border border-border bg-background">
                        <option>ON</option><option>OFF</option>
                      </select>
                      <select value={r.logic_operator} onChange={e=>setRule(i,'logic_operator',e.target.value)}
                        className="px-1.5 py-0.5 rounded border border-border bg-background">
                        <option>AND</option><option>OR</option>
                      </select>
                      <button onClick={()=>removeRule(i)} className="text-red-400 hover:text-red-300 px-1">✕</button>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {/* Price condition */}
                      <label className="flex items-center gap-1.5">
                        <input type="checkbox" checked={r.price_enabled} onChange={e=>setRule(i,'price_enabled',e.target.checked)}/>
                        <span>Price</span>
                        <select value={r.price_operator} onChange={e=>setRule(i,'price_operator',e.target.value)}
                          className="px-1 py-0.5 rounded border border-border bg-background">
                          {OPERATORS.map(o=><option key={o}>{o}</option>)}
                        </select>
                        <input type="number" step="0.1" value={r.price_threshold_pence}
                          onChange={e=>setRule(i,'price_threshold_pence',parseFloat(e.target.value))}
                          className="w-14 px-1 py-0.5 rounded border border-border bg-background"/>
                        <span>p</span>
                      </label>
                      {/* SOC condition */}
                      <label className="flex items-center gap-1.5">
                        <input type="checkbox" checked={r.soc_enabled} onChange={e=>setRule(i,'soc_enabled',e.target.checked)}/>
                        <span>SOC</span>
                        <select value={r.soc_operator} onChange={e=>setRule(i,'soc_operator',e.target.value)}
                          className="px-1 py-0.5 rounded border border-border bg-background">
                          {OPERATORS.map(o=><option key={o}>{o}</option>)}
                        </select>
                        <input type="number" step="1" value={r.soc_threshold_percent}
                          onChange={e=>setRule(i,'soc_threshold_percent',parseFloat(e.target.value))}
                          className="w-14 px-1 py-0.5 rounded border border-border bg-background"/>
                        <span>%</span>
                      </label>
                      {/* Solar condition */}
                      <label className="flex items-center gap-1.5">
                        <input type="checkbox" checked={r.solar_enabled} onChange={e=>setRule(i,'solar_enabled',e.target.checked)}/>
                        <span>Solar</span>
                        <select value={r.solar_operator} onChange={e=>setRule(i,'solar_operator',e.target.value)}
                          className="px-1 py-0.5 rounded border border-border bg-background">
                          {OPERATORS.map(o=><option key={o}>{o}</option>)}
                        </select>
                        <input type="number" step="0.1" value={r.solar_threshold_kw}
                          onChange={e=>setRule(i,'solar_threshold_kw',parseFloat(e.target.value))}
                          className="w-14 px-1 py-0.5 rounded border border-border bg-background"/>
                        <span>kW</span>
                      </label>
                      {/* Temp condition */}
                      <label className="flex items-center gap-1.5">
                        <input type="checkbox" checked={r.temp_enabled} onChange={e=>setRule(i,'temp_enabled',e.target.checked)}/>
                        <span>Temp</span>
                        <select value={r.temp_operator} onChange={e=>setRule(i,'temp_operator',e.target.value)}
                          className="px-1 py-0.5 rounded border border-border bg-background">
                          {OPERATORS.map(o=><option key={o}>{o}</option>)}
                        </select>
                        <input type="number" step="0.5" value={r.temp_threshold_c}
                          onChange={e=>setRule(i,'temp_threshold_c',parseFloat(e.target.value))}
                          className="w-14 px-1 py-0.5 rounded border border-border bg-background"/>
                        <span>°C</span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
              {result?.immersion&&(
                <div className={`rounded p-2 text-xs border ${result.immersion.action?'border-green-500/30 bg-green-500/10 text-green-300':'border-red-500/30 bg-red-500/10 text-red-300'}`}>
                  <span className="font-semibold">Immersion: {result.immersion.action?'ON':'OFF'}</span>
                  <span className="opacity-70 ml-2">({result.immersion.source})</span>
                  <span className="ml-2 opacity-80">{result.immersion.reason}</span>
                </div>
              )}
            </div>
          )}
        </Section>
      </div>

      {/* Price Editor */}
      <Section title="Price Array (half-hourly, up to 48 slots)">
        <PriceGrid prices={req.prices} onChange={p=>set('prices',p)}/>
      </Section>
    </div>
  )
}
