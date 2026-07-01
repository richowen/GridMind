/** Temperature target create/edit form. */

import { useState } from 'react'
import { Check, X } from 'lucide-react'
import type { TempTargetOut } from '@/types/api'
import { DAY_NAMES } from '@/types/domain'
import Button from '@/components/ui/Button'

const BLANK_TARGET: Partial<TempTargetOut> = {
  target_name: '',
  target_temp_c: 55,
  target_time: '07:00',
  days_of_week: '0,1,2,3,4,5,6',
  heating_rate_c_per_hour: 10,
  buffer_minutes: 30,
  is_enabled: true,
}

export { BLANK_TARGET }

export function TargetForm({
  initial,
  onSave,
  onCancel,
}: {
  initial: Partial<TempTargetOut>
  onSave: (data: Partial<TempTargetOut>) => void
  onCancel: () => void
}) {
  const [form, setForm] = useState<Partial<TempTargetOut>>(initial)
  const set = (key: keyof TempTargetOut, value: unknown) =>
    setForm(prev => ({ ...prev, [key]: value }))

  const selectedDays = (form.days_of_week ?? '').split(',').filter(Boolean)
  const toggleDay = (d: number) => {
    const s = new Set(selectedDays.map(Number))
    if (s.has(d)) s.delete(d)
    else s.add(d)
    set('days_of_week', Array.from(s).sort().join(','))
  }

  return (
    <div className="rounded-lg border border-border bg-fog p-4 space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Target Name</label>
          <input
            className="w-full bg-background border border-border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-signal"
            value={form.target_name ?? ''}
            onChange={e => set('target_name', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Target Temp (°C)</label>
          <input
            type="number"
            className="w-full bg-background border border-border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-signal"
            value={form.target_temp_c ?? 55}
            onChange={e => set('target_temp_c', Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Must reach by</label>
          <input
            type="time"
            className="w-full bg-background border border-border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-signal"
            value={form.target_time ?? '07:00'}
            onChange={e => set('target_time', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Heating rate (°C/hr)</label>
          <input
            type="number"
            step="0.5"
            className="w-full bg-background border border-border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-signal"
            value={form.heating_rate_c_per_hour ?? 10}
            onChange={e => set('heating_rate_c_per_hour', Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Buffer (minutes)</label>
          <input
            type="number"
            className="w-full bg-background border border-border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-signal"
            value={form.buffer_minutes ?? 30}
            onChange={e => set('buffer_minutes', Number(e.target.value))}
          />
        </div>
      </div>

      {/* Days of week */}
      <div>
        <label className="text-xs text-muted-foreground block mb-2">Active days</label>
        <div className="flex gap-1.5">
          {(Object.entries(DAY_NAMES) as [string, string][]).map(([dayNum, label]) => (
            <button
              key={dayNum}
              onClick={() => toggleDay(Number(dayNum))}
              className={`px-2 py-1 text-xs rounded-pill ${
                selectedDays.includes(dayNum)
                  ? 'bg-signal text-signal-foreground'
                  : 'bg-secondary text-muted-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Enabled */}
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={form.is_enabled ?? true}
          onChange={e => set('is_enabled', e.target.checked)}
          className="accent-signal"
        />
        <span className="text-sm text-foreground">Target enabled</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <Button variant="signal" className="px-3 py-1.5 text-sm" onClick={() => onSave(form)}>
          <Check className="h-3.5 w-3.5" /> Save Target
        </Button>
        <Button variant="ghost" className="px-3 py-1.5 text-sm" onClick={onCancel}>
          <X className="h-3.5 w-3.5" /> Cancel
        </Button>
      </div>
    </div>
  )
}
