/**Why page — full system decision trace: what readings, what rules, why each device is ON/OFF.*/
import {useState,useCallback} from 'react'
import {fetchWhy,type WhyResponse,type ConditionTrace,type RuleTrace,type DeviceDebugResult} from '@/api/why'

function fmtVal(v:number|null,unit:string){
  if(v===null||v===undefined) return <span className="text-muted-foreground italic">no data</span>
  return <span className="font-mono font-semibold">{v}{unit}</span>
}

function fmtTime(iso:string|null){
  if(!iso) return '—'
  const d=new Date(iso)
  return d.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit'})
}

function condIcon(c:ConditionTrace){
  if(!c.enabled) return <span className="text-muted-foreground text-xs">—</span>
  if(c.skipped) return <span title="Skipped — value was None/unavailable" className="text-yellow-400">⏭</span>
  if(c.passed===true) return <span className="text-green-400">✅</span>
  if(c.passed===false) return <span className="text-red-400">❌</span>
  return <span className="text-muted-foreground">?</span>
}

function condLabel(c:ConditionTrace){
  const labels:Record<string,string>={price:'Price',soc:'SOC',solar:'Solar',temp:'Temp',time:'Time'}
  const units:Record<string,string>={price:'p',soc:'%',solar:'kW',temp:'°C',time:''}
  const u=units[c.type]??''
  if(!c.enabled) return <span className="text-muted-foreground text-xs">{labels[c.type]} (off)</span>
  if(c.skipped) return (
    <span className="text-yellow-300 text-xs">
      {labels[c.type]}: <span className="italic">no sensor reading</span>
      {c.operator&&` (need ${c.operator} ${c.threshold??''}${u})`}
    </span>
  )
  return (
    <span className="text-xs">
      {labels[c.type]}: <span className="font-mono">{c.actual_value??'—'}{u}</span>
      {c.operator&&<> {c.operator} <span className="font-mono">{c.threshold}{u}</span></>}
    </span>
  )
}

function RuleRow({rule}:{rule:RuleTrace}){
  const [open,setOpen]=useState(false)
  const enabledConds=rule.conditions.filter(c=>c.enabled)
  return(
    <div className={`rounded border ${rule.matched?'border-green-500/40 bg-green-500/5':rule.enabled?'border-border bg-background/30':'border-border/40 bg-background/10 opacity-50'}`}>
      <button onClick={()=>setOpen(o=>!o)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left">
        <span className="text-sm">{rule.matched?'✅':rule.enabled?'❌':'💤'}</span>
        <span className={`text-sm font-medium flex-1 ${!rule.enabled?'line-through text-muted-foreground':''}`}>{rule.rule_name}</span>
        <span className="text-xs text-muted-foreground">P{rule.priority}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded border ${rule.action==='ON'?'border-green-500/30 bg-green-500/10 text-green-300':'border-red-500/30 bg-red-500/10 text-red-300'}`}>{rule.action}</span>
        <span className="text-xs text-muted-foreground px-1.5 py-0.5 rounded border border-border">{rule.logic_operator}</span>
        <span className="text-muted-foreground text-xs ml-1">{open?'▲':'▼'}</span>
      </button>
      {open&&(
        <div className="px-3 pb-2 space-y-1 border-t border-border/50 pt-2">
          {enabledConds.length===0&&<p className="text-xs text-muted-foreground italic">No conditions enabled — rule will never match.</p>}
          {rule.conditions.map((c,i)=>(
            <div key={i} className="flex items-center gap-2">
              {condIcon(c)}
              {condLabel(c)}
            </div>
          ))}
          {!rule.enabled&&<p className="text-xs text-yellow-400 mt-1">⚠ Rule is disabled — not evaluated.</p>}
          {rule.enabled&&enabledConds.length>0&&!rule.matched&&(
            <p className="text-xs text-red-300 mt-1">
              {rule.logic_operator==='AND'
                ?'AND: all conditions must pass — at least one failed.'
                :'OR: at least one condition must pass — all failed or skipped.'}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function DeviceCard({d}:{d:DeviceDebugResult}){
  const [open,setOpen]=useState(true)
  const dec=d.final_decision
  return(
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <button onClick={()=>setOpen(o=>!o)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left bg-card hover:bg-accent/30 transition-colors">
        <span className={`text-lg`}>{dec.action?'🔥':'💧'}</span>
        <div className="flex-1">
          <div className="font-semibold text-sm text-foreground">{d.device_name}</div>
          <div className="text-xs text-muted-foreground">{d.switch_entity_id}</div>
        </div>
        <div className="text-right">
          <div className={`text-sm font-bold ${dec.action?'text-green-400':'text-muted-foreground'}`}>{dec.action?'ON':'OFF'}</div>
          <div className="text-xs text-muted-foreground">{dec.source}</div>
        </div>
        <span className="text-muted-foreground text-xs ml-2">{open?'▲':'▼'}</span>
      </button>
      {open&&(
        <div className="px-4 pb-4 space-y-3 border-t border-border">
          <div className="pt-2 space-y-1">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Decision:</span>
              <span className={`font-semibold ${dec.action?'text-green-400':'text-red-400'}`}>{dec.action?'ON':'OFF'}</span>
              <span className="text-muted-foreground">({dec.source})</span>
              <span className="text-foreground">— {dec.reason}</span>
            </div>
            {d.temp_c!==null&&<div className="text-xs text-muted-foreground">Water temp: {d.temp_c}°C</div>}
            {d.active_override&&(
              <div className="text-xs text-yellow-300 rounded border border-yellow-500/30 bg-yellow-500/10 px-2 py-1">
                ⚡ Override active: {d.active_override}
              </div>
            )}
          </div>
          {d.rule_traces.length===0
            ?<p className="text-xs text-muted-foreground italic">No smart rules configured.</p>
            :<div className="space-y-1.5">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Rules (priority order)</div>
              {d.rule_traces.map((r,i)=><RuleRow key={i} rule={r}/>)}
            </div>
          }
        </div>
      )}
    </div>
  )
}

export default function Why(){
  const [data,setData]=useState<WhyResponse|null>(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string|null>(null)

  const load=useCallback(async()=>{
    setLoading(true);setError(null)
    try{setData(await fetchWhy())}
    catch(e:any){setError(e?.message??'Failed to load')}
    finally{setLoading(false)}
  },[])

  const copyAI=()=>{
    if(!data) return
    const txt=JSON.stringify(data,null,2)
    navigator.clipboard.writeText(txt).catch(()=>{})
  }

  const lp=data?.lp_decision
  const r=data?.readings

  return(
    <div className="space-y-4 max-w-4xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Why is the system doing this?</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Full decision trace — what readings are visible, why each rule matched or didn't</p>
        </div>
        <div className="flex gap-2">
          {data&&(
            <button onClick={copyAI}
              className="px-3 py-2 rounded-lg border border-border bg-card text-sm hover:bg-accent transition-colors"
              title="Copy full trace as JSON for AI debugging">
              📋 Copy for AI
            </button>
          )}
          <button onClick={load} disabled={loading}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/80 disabled:opacity-50 transition-colors">
            {loading?'Loading…':'🔍 Fetch Trace'}
          </button>
        </div>
      </div>

      {error&&<div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">{error}</div>}

      {!data&&!loading&&(
        <div className="rounded-lg border border-dashed border-border bg-card/50 p-8 text-center text-muted-foreground text-sm">
          Click <strong>Fetch Trace</strong> to see the system's current decision reasoning.
        </div>
      )}

      {data&&(
        <>
          {/* Timestamp */}
          <div className="text-xs text-muted-foreground">Trace at {new Date(data.timestamp).toLocaleString('en-GB')}</div>

          {/* Live Readings */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">📡 Live Readings (from DB)</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              <div><span className="text-muted-foreground">Battery SOC: </span>{fmtVal(r?.battery_soc_pct as number,'%')}</div>
              <div><span className="text-muted-foreground">Solar: </span>{fmtVal(r?.solar_power_kw as number,' kW')}</div>
              <div><span className="text-muted-foreground">Price: </span>{fmtVal(r?.current_price_pence as number,'p')}</div>
              <div><span className="text-muted-foreground">Last opt: </span><span className="font-mono text-xs">{fmtTime(r?.last_optimization as string)}</span></div>
              <div><span className="text-muted-foreground">Last mode: </span><span className="font-mono text-xs">{r?.last_mode??'—'}</span></div>
            </div>
          </div>

          {/* LP Decision */}
          {lp&&(
            <div className={`rounded-lg border p-4 ${lp.mode==='Force Charge'?'border-green-500/30 bg-green-500/5':lp.mode==='Force Discharge'?'border-red-500/30 bg-red-500/5':'border-blue-500/30 bg-blue-500/5'}`}>
              <h3 className="text-sm font-semibold text-foreground mb-2">⚡ Battery Decision (LP Optimizer)</h3>
              <div className="space-y-1 text-sm">
                <div><span className="text-muted-foreground">Mode: </span><span className="font-bold text-lg">{lp.mode}</span></div>
                <div><span className="text-muted-foreground">Reason: </span><span>{lp.reason}</span></div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs text-muted-foreground">
                  <div>Status: <span className="text-foreground font-mono">{lp.status}</span></div>
                  <div>Price: <span className="text-foreground font-mono">{lp.current_slot_price_pence?.toFixed(1)??'—'}p</span></div>
                  <div>Objective: <span className="text-foreground font-mono">{lp.objective_value?.toFixed(2)??'—'}p</span></div>
                  <div>Solved in: <span className="text-foreground font-mono">{lp.optimization_time_ms?.toFixed(0)??'—'}ms</span></div>
                </div>
                {lp.last_run&&<div className="text-xs text-muted-foreground">Last run: {new Date(lp.last_run).toLocaleString('en-GB')}</div>}
              </div>
            </div>
          )}

          {/* Immersion Devices */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">🔥 Immersion Decisions</h3>
            {data.immersion_devices.length===0
              ?<div className="rounded-lg border border-dashed border-border bg-card/50 p-4 text-center text-sm text-muted-foreground">No enabled immersion devices found.</div>
              :data.immersion_devices.map(d=><DeviceCard key={d.device_id} d={d}/>)
            }
          </div>
        </>
      )}
    </div>
  )
}
