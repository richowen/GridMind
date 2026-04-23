/**LP schedule chart: SOC line + charge/discharge/import/export bars per period.*/
import {
  ComposedChart,Bar,Line,XAxis,YAxis,Tooltip,Legend,
  ResponsiveContainer,CartesianGrid,
} from 'recharts'
import type {SimPeriodResult} from '@/api/dev'

interface Props {periods:SimPeriodResult[];capacityKwh:number}

function slot(iso:string){
  try{const d=new Date(iso);return `${String(d.getUTCHours()).padStart(2,'0')}:${String(d.getUTCMinutes()).padStart(2,'0')}`}
  catch{return ''}
}

export default function ResultChart({periods,capacityKwh}:Props){
  if(!periods.length) return <div className="h-40 flex items-center justify-center text-xs text-muted-foreground">No data</div>

  const data=periods.map(p=>({
    t:slot(p.valid_from),
    charge:p.charge_kw,
    discharge:-p.discharge_kw,
    import:p.grid_import_kw,
    export:-p.grid_export_kw,
    soc:p.soc_pct,
    price:p.price_pence,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{top:4,right:8,bottom:0,left:0}}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b"/>
        <XAxis dataKey="t" tick={{fontSize:9,fill:'#6b7280'}} interval={5}/>
        <YAxis yAxisId="kw" tick={{fontSize:9,fill:'#6b7280'}} label={{value:'kW',angle:-90,position:'insideLeft',style:{fontSize:9,fill:'#6b7280'}}}/>
        <YAxis yAxisId="soc" orientation="right" domain={[0,100]} tick={{fontSize:9,fill:'#94a3b8'}} label={{value:'SOC %',angle:90,position:'insideRight',style:{fontSize:9,fill:'#94a3b8'}}}/>
        <Tooltip
          contentStyle={{background:'#0f172a',border:'1px solid #334155',borderRadius:4,fontSize:11}}
          labelStyle={{color:'#94a3b8'}}
          formatter={(v:number,name:string)=>[`${Math.abs(v).toFixed(2)} ${name==='soc'?'%':'kW'}`,name]}
        />
        <Legend wrapperStyle={{fontSize:10}}/>
        <Bar yAxisId="kw" dataKey="charge" stackId="a" fill="#22c55e" name="charge"/>
        <Bar yAxisId="kw" dataKey="import" stackId="a" fill="#f59e0b" name="import"/>
        <Bar yAxisId="kw" dataKey="discharge" stackId="b" fill="#ef4444" name="discharge"/>
        <Bar yAxisId="kw" dataKey="export" stackId="b" fill="#3b82f6" name="export"/>
        <Line yAxisId="soc" type="monotone" dataKey="soc" stroke="#a78bfa" dot={false} strokeWidth={2} name="soc"/>
      </ComposedChart>
    </ResponsiveContainer>
  )
}
