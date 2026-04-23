/**48-slot half-hourly price editor with bulk-fill and import-from-live button.*/
import {useState,useCallback} from 'react'
import {SimPrice,generateFlatPrices} from '@/api/dev'
import {api} from '@/api/client'

interface Props {prices:SimPrice[];onChange:(p:SimPrice[])=>void}

function slotLabel(iso:string){
  try{const d=new Date(iso);return `${String(d.getUTCHours()).padStart(2,'0')}:${String(d.getUTCMinutes()).padStart(2,'0')}`}
  catch{return '??:??'}
}

function priceColour(p:number){
  if(p<5) return 'bg-green-500/20 text-green-300'
  if(p<15) return 'bg-green-400/10 text-green-200'
  if(p<25) return 'bg-yellow-400/10 text-yellow-200'
  if(p<35) return 'bg-orange-400/10 text-orange-300'
  return 'bg-red-500/20 text-red-300'
}

export default function PriceGrid({prices,onChange}:Props){
  const [bulkVal,setBulkVal]=useState('15')
  const [loading,setLoading]=useState(false)

  const setSlot=(i:number,v:string)=>{
    const n=parseFloat(v)
    if(isNaN(n))return
    const next=[...prices]
    next[i]={...next[i],price_pence:n}
    onChange(next)
  }

  const fillFlat=()=>onChange(generateFlatPrices(parseFloat(bulkVal)||15,prices.length||48))

  const loadLive=useCallback(async()=>{
    setLoading(true)
    try{
      const data=await api.get<any[]>('/prices/current?hours=24')
      if(Array.isArray(data)&&data.length){
        onChange(data.map((p:any)=>({valid_from:p.valid_from,price_pence:p.price_pence})))
      }else{
        console.warn('No prices returned from /prices/current',data)
      }
    }catch(e){console.warn('Could not load live prices',e)}
    finally{setLoading(false)}
  },[onChange])

  const init=()=>{if(!prices.length)onChange(generateFlatPrices(15,48))}

  if(!prices.length) return (
    <div className="space-y-2">
      <p className="text-sm text-muted-foreground">No prices loaded.</p>
      <div className="flex gap-2 flex-wrap">
        <button onClick={init} className="px-3 py-1 text-xs rounded bg-accent hover:bg-accent/80">
          Generate 48 flat slots (15p)
        </button>
        <button onClick={loadLive} disabled={loading}
          className="px-3 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50">
          {loading?'Loading…':'Load live Octopus prices'}
        </button>
      </div>
    </div>
  )

  return (
    <div className="space-y-3">
      <div className="flex gap-2 items-center flex-wrap">
        <input type="number" value={bulkVal} onChange={e=>setBulkVal(e.target.value)}
          className="w-20 px-2 py-1 text-xs rounded border border-border bg-background" placeholder="p/kWh"/>
        <button onClick={fillFlat} className="px-3 py-1 text-xs rounded bg-accent hover:bg-accent/80">
          Fill all flat
        </button>
        <button onClick={loadLive} disabled={loading}
          className="px-3 py-1 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/80 disabled:opacity-50">
          {loading?'Loading…':'↻ Load live prices'}
        </button>
        <span className="text-xs text-muted-foreground ml-auto">{prices.length} slots</span>
      </div>
      <div className="grid grid-cols-8 gap-1 max-h-64 overflow-y-auto pr-1">
        {prices.map((p,i)=>(
          <div key={i} className={`rounded p-1 text-center ${priceColour(p.price_pence)}`}>
            <div className="text-[10px] opacity-70">{slotLabel(p.valid_from)}</div>
            <input
              type="number" step="0.1" value={p.price_pence}
              onChange={e=>setSlot(i,e.target.value)}
              className="w-full text-xs text-center bg-transparent outline-none"
            />
            <div className="text-[10px] opacity-50">p</div>
          </div>
        ))}
      </div>
    </div>
  )
}
