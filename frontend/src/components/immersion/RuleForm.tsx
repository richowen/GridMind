/** Smart rule create/edit form. */

import { useState } from 'react'
import { Check, X } from 'lucide-react'
import type { SmartRuleOut } from '@/types/api'
import { ConditionRow, TimeConditionRow } from './ConditionRow'

const BLANK_RULE: Partial<SmartRuleOut> = {
  rule_name: '',
  priority: 10,
  action: 'ON',
  logic_operator: 'AND',
  is_enabled: true,
  price_enabled: false,
  price_operator: '<',
  price_threshold_pence: 10,
  soc_enabled: false,
  soc_operator: '>',
  soc_threshold_percent: 20,
  solar_enabled: false,
  solar_operator: '>',
  solar_threshold_kw: 1.0,
  temp_enabled: false,
  temp_operator: '<',
  temp_threshold_c: 50,
  time_enabled: false,
  time_start: '00:00',
  time_end: '06:00',
}

export { BLANK_RULE }

export function RuleForm({
  initial,
  onSave,
  onCancel,
}: {
  initial: Partial<SmartRuleOut>
  onSave: (data: Partial<SmartRuleOut>) => void
  onCancel: () => void
}) {
  const [form, setForm] = useState<Partial<SmartRuleOut>>(initial)
  const set = (key: keyof SmartRuleOut, value: unknown) =>
    setForm(prev => ({ ...prev, [key]: value }))

  return (
    <div className="rounded border border-border bg-secondary/40 p-4 space-y-4">
      {/* Name / Priority / Action / Logic */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Rule Name</label>
          <input
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.rule_name ?? ''}
            onChange={e => set('rule_name', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Priority (lower = higher)</label>
          <input
            type="number"
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.priority ?? 10}
            onChange={e => set('priority', Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Action</label>
          <select
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.action ?? 'ON'}
            onChange={e => set('action', e.target.value)}
          >
            <option value="ON">ON</option>
            <option value="OFF">OFF</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Logic (how conditions combine)</label>
          <select
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.logic_operator ?? 'AND'}
            onChange={e => set('logic_operator', e.target.value)}
          >
            <option value="AND">AND (all must match)</option>
            <option value="OR">OR (any must match)</option>
          </select>
        </div>
      </div>

      {/* Conditions */}
      <div className="space-y-3">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Conditions</p>

        <ConditionRow
          label="Price"
          enabled={form.price_enabled ?? false}
          onToggle={v => set('price_enabled', v)}
          operator={form.price_operator ?? '<'}
          onOperator={v => set('price_operator', v)}
          value={form.price_threshold_pence ?? 10}
          onValue={v => set('price_threshold_pence', v)}
          unit="p/kWh"
        />

        <ConditionRow
          label="Battery"
          enabled={form.soc_enabled ?? false}
          onToggle={v => set('soc_enabled', v)}
          operator={form.soc_operator ?? '>'}
          onOperator={v => set('soc_operator', v)}
          value={form.soc_threshold_percent ?? 20}
          onValue={v => set('soc_threshold_percent', v)}
          unit="% SoC"
        />

        <ConditionRow
          label="Solar"
          enabled={form.solar_enabled ?? false}
          onToggle={v => set('solar_enabled', v)}
          operator={form.solar_operator ?? '>'}
          onOperator={v => set('solar_operator', v)}
          value={form.solar_threshold_kw ?? 1.0}
          onValue={v => set('solar_threshold_kw', v)}
          step={0.1}
          unit="kW"
        />

        <ConditionRow
          label="Temp"
          enabled={form.temp_enabled ?? false}
          onToggle={v => set('temp_enabled', v)}
          operator={form.temp_operator ?? '<'}
          onOperator={v => set('temp_operator', v)}
          value={form.temp_threshold_c ?? 50}
          onValue={v => set('temp_threshold_c', v)}
          unit="°C"
        />

        <TimeConditionRow
          enabled={form.time_enabled ?? false}
          onToggle={v => set('time_enabled', v)}
          timeStart={form.time_start ?? '00:00'}
          onTimeStart={v => set('time_start', v)}
          timeEnd={form.time_end ?? '06:00'}
          onTimeEnd={v => set('time_end', v)}
        />
      </div>

      {/* Enabled toggle */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={form.is_enabled ?? true}
          onChange={e => set('is_enabled', e.target.checked)}
          className="accent-primary"
        />
        <span className="text-sm">Rule enabled</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={() => onSave(form)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:opacity-90"
        >
          <Check className="h-3.5 w-3.5" /> Save Rule
        </button>
        <button
          onClick={onCancel}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-secondary rounded hover:bg-accent"
        >
          <X className="h-3.5 w-3.5" /> Cancel
        </button>
      </div>
    </div>
  )
}
