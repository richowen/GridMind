/** Immersion Manager page — device list, smart rules, and temperature targets with full CRUD. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Flame, Pencil, Trash2, X, Check } from 'lucide-react'
import { immersionApi } from '@/api/immersion'
import type { ImmersionDeviceOut, SmartRuleOut, TempTargetOut } from '@/types/api'

// ── Blank templates ──────────────────────────────────────────────────────────

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

const BLANK_TARGET: Partial<TempTargetOut> = {
  target_name: '',
  target_temp_c: 55,
  target_time: '07:00',
  days_of_week: '0,1,2,3,4,5,6',
  heating_rate_c_per_hour: 10,
  buffer_minutes: 30,
  is_enabled: true,
}

// ── Rule Form ────────────────────────────────────────────────────────────────

function RuleForm({
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

        {/* Price */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={form.price_enabled ?? false}
            onChange={e => set('price_enabled', e.target.checked)}
            className="accent-primary"
          />
          <span className="text-sm w-16 shrink-0">Price</span>
          <select
            disabled={!form.price_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.price_operator ?? '<'}
            onChange={e => set('price_operator', e.target.value)}
          >
            <option value="<">{'<'}</option>
            <option value="<=">{'<='}</option>
            <option value=">">{'>'}</option>
            <option value=">=">{'>='}</option>
          </select>
          <input
            type="number"
            disabled={!form.price_enabled}
            className="w-20 bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.price_threshold_pence ?? 10}
            onChange={e => set('price_threshold_pence', Number(e.target.value))}
          />
          <span className="text-xs text-muted-foreground">p/kWh</span>
        </div>

        {/* SoC */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={form.soc_enabled ?? false}
            onChange={e => set('soc_enabled', e.target.checked)}
            className="accent-primary"
          />
          <span className="text-sm w-16 shrink-0">Battery</span>
          <select
            disabled={!form.soc_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.soc_operator ?? '>'}
            onChange={e => set('soc_operator', e.target.value)}
          >
            <option value="<">{'<'}</option>
            <option value="<=">{'<='}</option>
            <option value=">">{'>'}</option>
            <option value=">=">{'>='}</option>
          </select>
          <input
            type="number"
            disabled={!form.soc_enabled}
            className="w-20 bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.soc_threshold_percent ?? 20}
            onChange={e => set('soc_threshold_percent', Number(e.target.value))}
          />
          <span className="text-xs text-muted-foreground">% SoC</span>
        </div>

        {/* Solar */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={form.solar_enabled ?? false}
            onChange={e => set('solar_enabled', e.target.checked)}
            className="accent-primary"
          />
          <span className="text-sm w-16 shrink-0">Solar</span>
          <select
            disabled={!form.solar_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.solar_operator ?? '>'}
            onChange={e => set('solar_operator', e.target.value)}
          >
            <option value="<">{'<'}</option>
            <option value="<=">{'<='}</option>
            <option value=">">{'>'}</option>
            <option value=">=">{'>='}</option>
          </select>
          <input
            type="number"
            step="0.1"
            disabled={!form.solar_enabled}
            className="w-20 bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.solar_threshold_kw ?? 1.0}
            onChange={e => set('solar_threshold_kw', Number(e.target.value))}
          />
          <span className="text-xs text-muted-foreground">kW</span>
        </div>

        {/* Temperature */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={form.temp_enabled ?? false}
            onChange={e => set('temp_enabled', e.target.checked)}
            className="accent-primary"
          />
          <span className="text-sm w-16 shrink-0">Temp</span>
          <select
            disabled={!form.temp_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.temp_operator ?? '<'}
            onChange={e => set('temp_operator', e.target.value)}
          >
            <option value="<">{'<'}</option>
            <option value="<=">{'<='}</option>
            <option value=">">{'>'}</option>
            <option value=">=">{'>='}</option>
          </select>
          <input
            type="number"
            disabled={!form.temp_enabled}
            className="w-20 bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.temp_threshold_c ?? 50}
            onChange={e => set('temp_threshold_c', Number(e.target.value))}
          />
          <span className="text-xs text-muted-foreground">°C</span>
        </div>

        {/* Time window */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={form.time_enabled ?? false}
            onChange={e => set('time_enabled', e.target.checked)}
            className="accent-primary"
          />
          <span className="text-sm w-16 shrink-0">Time</span>
          <input
            type="time"
            disabled={!form.time_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.time_start ?? '00:00'}
            onChange={e => set('time_start', e.target.value)}
          />
          <span className="text-xs text-muted-foreground">to</span>
          <input
            type="time"
            disabled={!form.time_enabled}
            className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
            value={form.time_end ?? '06:00'}
            onChange={e => set('time_end', e.target.value)}
          />
        </div>
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

// ── Target Form ──────────────────────────────────────────────────────────────

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function TargetForm({
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
    <div className="rounded border border-border bg-secondary/40 p-4 space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Target Name</label>
          <input
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.target_name ?? ''}
            onChange={e => set('target_name', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Target Temp (°C)</label>
          <input
            type="number"
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.target_temp_c ?? 55}
            onChange={e => set('target_temp_c', Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Must reach by</label>
          <input
            type="time"
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.target_time ?? '07:00'}
            onChange={e => set('target_time', e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Heating rate (°C/hr)</label>
          <input
            type="number"
            step="0.5"
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.heating_rate_c_per_hour ?? 10}
            onChange={e => set('heating_rate_c_per_hour', Number(e.target.value))}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground block mb-1">Buffer (minutes)</label>
          <input
            type="number"
            className="w-full bg-secondary border border-border rounded px-2 py-1.5 text-sm"
            value={form.buffer_minutes ?? 30}
            onChange={e => set('buffer_minutes', Number(e.target.value))}
          />
        </div>
      </div>

      {/* Days of week */}
      <div>
        <label className="text-xs text-muted-foreground block mb-2">Active days</label>
        <div className="flex gap-1.5">
          {DAY_LABELS.map((label, i) => (
            <button
              key={i}
              onClick={() => toggleDay(i)}
              className={`px-2 py-1 text-xs rounded ${
                selectedDays.includes(String(i))
                  ? 'bg-primary text-primary-foreground'
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
          className="accent-primary"
        />
        <span className="text-sm">Target enabled</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={() => onSave(form)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:opacity-90"
        >
          <Check className="h-3.5 w-3.5" /> Save Target
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

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Immersions() {
  const qc = useQueryClient()
  const [selectedDevice, setSelectedDevice] = useState<ImmersionDeviceOut | null>(null)
  const [activeTab, setActiveTab] = useState<'rules' | 'targets'>('rules')

  // Rule form state: null = hidden, 'new' = adding, number = editing rule id
  const [ruleFormMode, setRuleFormMode] = useState<null | 'new' | number>(null)
  const [ruleFormInitial, setRuleFormInitial] = useState<Partial<SmartRuleOut>>(BLANK_RULE)

  // Target form state: null = hidden, 'new' = adding, number = editing target id
  const [targetFormMode, setTargetFormMode] = useState<null | 'new' | number>(null)
  const [targetFormInitial, setTargetFormInitial] = useState<Partial<TempTargetOut>>(BLANK_TARGET)

  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: immersionApi.listDevices,
  })

  const { data: rules } = useQuery({
    queryKey: ['rules', selectedDevice?.id],
    queryFn: () => immersionApi.listRules(selectedDevice!.id),
    enabled: !!selectedDevice,
  })

  const { data: targets } = useQuery({
    queryKey: ['targets', selectedDevice?.id],
    queryFn: () => immersionApi.listTargets(selectedDevice!.id),
    enabled: !!selectedDevice,
  })

  // ── Rule mutations ──────────────────────────────────────────────────────────

  const createRuleMutation = useMutation({
    mutationFn: (body: Partial<SmartRuleOut>) =>
      immersionApi.createRule(selectedDevice!.id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rules'] })
      setRuleFormMode(null)
    },
  })

  const updateRuleMutation = useMutation({
    mutationFn: ({ ruleId, body }: { ruleId: number; body: Partial<SmartRuleOut> }) =>
      immersionApi.updateRule(selectedDevice!.id, ruleId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rules'] })
      setRuleFormMode(null)
    },
  })

  const deleteRuleMutation = useMutation({
    mutationFn: (ruleId: number) =>
      immersionApi.deleteRule(selectedDevice!.id, ruleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  })

  // ── Target mutations ────────────────────────────────────────────────────────

  const createTargetMutation = useMutation({
    mutationFn: (body: Partial<TempTargetOut>) =>
      immersionApi.createTarget(selectedDevice!.id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['targets'] })
      setTargetFormMode(null)
    },
  })

  const updateTargetMutation = useMutation({
    mutationFn: ({ targetId, body }: { targetId: number; body: Partial<TempTargetOut> }) =>
      immersionApi.updateTarget(selectedDevice!.id, targetId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['targets'] })
      setTargetFormMode(null)
    },
  })

  const deleteTargetMutation = useMutation({
    mutationFn: (targetId: number) =>
      immersionApi.deleteTarget(selectedDevice!.id, targetId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['targets'] }),
  })

  // ── Handlers ────────────────────────────────────────────────────────────────

  const handleSaveRule = (data: Partial<SmartRuleOut>) => {
    if (ruleFormMode === 'new') {
      createRuleMutation.mutate(data)
    } else if (typeof ruleFormMode === 'number') {
      updateRuleMutation.mutate({ ruleId: ruleFormMode, body: data })
    }
  }

  const handleEditRule = (rule: SmartRuleOut) => {
    setRuleFormInitial(rule)
    setRuleFormMode(rule.id)
  }

  const handleSaveTarget = (data: Partial<TempTargetOut>) => {
    if (targetFormMode === 'new') {
      createTargetMutation.mutate(data)
    } else if (typeof targetFormMode === 'number') {
      updateTargetMutation.mutate({ targetId: targetFormMode, body: data })
    }
  }

  const handleEditTarget = (target: TempTargetOut) => {
    setTargetFormInitial(target)
    setTargetFormMode(target.id)
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Immersion Control Manager</h1>
      </div>

      {/* Device List */}
      <div className="space-y-3">
        {(devices ?? []).map(device => (
          <div
            key={device.id}
            className={`rounded-lg border p-4 cursor-pointer transition-colors ${
              selectedDevice?.id === device.id
                ? 'border-primary bg-accent'
                : 'border-border bg-card hover:bg-accent/50'
            }`}
            onClick={() => {
              setSelectedDevice(device)
              setRuleFormMode(null)
              setTargetFormMode(null)
            }}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Flame className={`h-5 w-5 ${device.is_enabled ? 'text-orange-400' : 'text-muted-foreground'}`} />
                <div>
                  <div className="font-medium">{device.display_name}</div>
                  <div className="text-xs text-muted-foreground">{device.switch_entity_id}</div>
                </div>
              </div>
              <div className={`text-xs px-2 py-1 rounded ${device.is_enabled ? 'bg-green-500/20 text-green-400' : 'bg-secondary text-muted-foreground'}`}>
                {device.is_enabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Device Config */}
      {selectedDevice && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h2 className="font-medium mb-4">Configuring: {selectedDevice.display_name}</h2>

          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            {(['rules', 'targets'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab)
                  setRuleFormMode(null)
                  setTargetFormMode(null)
                }}
                className={`px-3 py-1.5 text-sm rounded ${
                  activeTab === tab ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
                }`}
              >
                {tab === 'rules' ? 'Smart Rules' : 'Temperature Targets'}
              </button>
            ))}
          </div>

          {/* ── Smart Rules tab ── */}
          {activeTab === 'rules' && (
            <div className="space-y-3">
              {(rules ?? []).map(rule => (
                <div key={rule.id}>
                  {ruleFormMode === rule.id ? (
                    <RuleForm
                      key={ruleFormMode}
                      initial={ruleFormInitial}
                      onSave={handleSaveRule}
                      onCancel={() => setRuleFormMode(null)}
                    />
                  ) : (
                    <div className="rounded border border-border p-3 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-xs text-muted-foreground w-6 shrink-0">#{rule.priority}</span>
                        <span className="font-medium text-sm truncate">{rule.rule_name}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${rule.action === 'ON' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                          {rule.action}
                        </span>
                        <span className="text-xs text-muted-foreground shrink-0">{rule.logic_operator}</span>
                        {!rule.is_enabled && (
                          <span className="text-xs text-muted-foreground shrink-0">(disabled)</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleEditRule(rule)}
                          className="text-muted-foreground hover:text-foreground"
                          title="Edit rule"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete rule "${rule.rule_name}"?`)) {
                              deleteRuleMutation.mutate(rule.id)
                            }
                          }}
                          className="text-red-400 hover:text-red-300"
                          title="Delete rule"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Add Rule form or button */}
              {ruleFormMode === 'new' ? (
                <RuleForm
                  key="new-rule"
                  initial={ruleFormInitial}
                  onSave={handleSaveRule}
                  onCancel={() => setRuleFormMode(null)}
                />
              ) : (
                <button
                  onClick={() => {
                    setRuleFormInitial(BLANK_RULE)
                    setRuleFormMode('new')
                  }}
                  className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mt-1"
                >
                  <Plus className="h-4 w-4" /> Add Rule
                </button>
              )}
            </div>
          )}

          {/* ── Temperature Targets tab ── */}
          {activeTab === 'targets' && (
            <div className="space-y-3">
              {(targets ?? []).map(target => (
                <div key={target.id}>
                  {targetFormMode === target.id ? (
                    <TargetForm
                      key={targetFormMode}
                      initial={targetFormInitial}
                      onSave={handleSaveTarget}
                      onCancel={() => setTargetFormMode(null)}
                    />
                  ) : (
                    <div className="rounded border border-border p-3 flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-medium text-sm">{target.target_name}</div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {target.target_temp_c}°C by {target.target_time} · days {target.days_of_week} · {target.heating_rate_c_per_hour}°C/hr · {target.buffer_minutes}min buffer
                          {!target.is_enabled && ' · (disabled)'}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          onClick={() => handleEditTarget(target)}
                          className="text-muted-foreground hover:text-foreground"
                          title="Edit target"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete target "${target.target_name}"?`)) {
                              deleteTargetMutation.mutate(target.id)
                            }
                          }}
                          className="text-red-400 hover:text-red-300"
                          title="Delete target"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Add Target form or button */}
              {targetFormMode === 'new' ? (
                <TargetForm
                  key="new-target"
                  initial={targetFormInitial}
                  onSave={handleSaveTarget}
                  onCancel={() => setTargetFormMode(null)}
                />
              ) : (
                <button
                  onClick={() => {
                    setTargetFormInitial(BLANK_TARGET)
                    setTargetFormMode('new')
                  }}
                  className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mt-1"
                >
                  <Plus className="h-4 w-4" /> Add Temperature Target
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
