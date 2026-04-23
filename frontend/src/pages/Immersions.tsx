/** Immersion Manager page — device list, smart rules, and temperature targets with full CRUD. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Flame, Pencil, Trash2 } from 'lucide-react'
import { immersionApi } from '@/api/immersion'
import type { ImmersionDeviceOut, SmartRuleOut, TempTargetOut } from '@/types/api'
import { RuleForm, BLANK_RULE } from '@/components/immersion/RuleForm'
import { TargetForm, BLANK_TARGET } from '@/components/immersion/TargetForm'

export default function Immersions() {
  const qc = useQueryClient()
  const [selectedDevice, setSelectedDevice] = useState<ImmersionDeviceOut | null>(null)
  const [activeTab, setActiveTab] = useState<'rules' | 'targets' | 'device'>('rules')
  const [deviceEdit, setDeviceEdit] = useState<Partial<ImmersionDeviceOut>>({})
  const [deviceSaved, setDeviceSaved] = useState<string | null>(null)

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

  // ── Device update mutation ──────────────────────────────────────────────────

  const updateDeviceMutation = useMutation({
    mutationFn: (body: Partial<ImmersionDeviceOut>) =>
      immersionApi.updateDevice(selectedDevice!.id, body),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ['devices'] })
      setSelectedDevice(updated)
      setDeviceSaved('✅ Saved')
      setTimeout(() => setDeviceSaved(null), 2500)
    },
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
            {([['rules','Smart Rules'],['targets','Temperature Targets'],['device','Device Settings']] as const).map(([tab,label]) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab)
                  setRuleFormMode(null)
                  setTargetFormMode(null)
                  if(tab==='device') setDeviceEdit({
                    display_name: selectedDevice.display_name,
                    switch_entity_id: selectedDevice.switch_entity_id,
                    temp_sensor_entity_id: selectedDevice.temp_sensor_entity_id ?? '',
                    is_enabled: selectedDevice.is_enabled,
                    sort_order: selectedDevice.sort_order,
                  })
                }}
                className={`px-3 py-1.5 text-sm rounded ${
                  activeTab === tab ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
                }`}
              >
                {label}
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

          {/* ── Device Settings tab ── */}
          {activeTab === 'device' && (
            <div className="space-y-4 max-w-lg">
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Display Name</label>
                  <input
                    className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    value={deviceEdit.display_name ?? ''}
                    onChange={e => setDeviceEdit(p => ({...p, display_name: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Switch Entity ID</label>
                  <input
                    className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="switch.immersion_main"
                    value={deviceEdit.switch_entity_id ?? ''}
                    onChange={e => setDeviceEdit(p => ({...p, switch_entity_id: e.target.value}))}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">
                    Temperature Sensor Entity ID
                    <span className="ml-1 text-muted-foreground/60">(optional — enables temp rules &amp; Why? trace)</span>
                  </label>
                  <input
                    className="w-full rounded border border-border bg-background px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="sensor.immersion_main_temperature"
                    value={deviceEdit.temp_sensor_entity_id ?? ''}
                    onChange={e => setDeviceEdit(p => ({...p, temp_sensor_entity_id: e.target.value || null}))}
                  />
                  {selectedDevice.temp_sensor_entity_id
                    ? <p className="text-xs text-green-400 mt-1">✅ Sensor configured — temp will be read from HA on each evaluation</p>
                    : <p className="text-xs text-yellow-400 mt-1">⚠ No sensor — temp rules will be skipped (⏭) until one is set</p>
                  }
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <label className="text-xs text-muted-foreground block mb-1">Sort Order</label>
                    <input
                      type="number"
                      className="w-24 rounded border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      value={deviceEdit.sort_order ?? 0}
                      onChange={e => setDeviceEdit(p => ({...p, sort_order: parseInt(e.target.value) || 0}))}
                    />
                  </div>
                  <div className="flex items-center gap-2 pt-4">
                    <input
                      type="checkbox"
                      id="dev-enabled"
                      checked={deviceEdit.is_enabled ?? true}
                      onChange={e => setDeviceEdit(p => ({...p, is_enabled: e.target.checked}))}
                      className="h-4 w-4"
                    />
                    <label htmlFor="dev-enabled" className="text-sm">Enabled</label>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => updateDeviceMutation.mutate(deviceEdit)}
                  disabled={updateDeviceMutation.isPending}
                  className="px-4 py-1.5 rounded bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/80 disabled:opacity-50"
                >
                  {updateDeviceMutation.isPending ? 'Saving…' : 'Save Changes'}
                </button>
                {deviceSaved && <span className="text-xs text-green-400">{deviceSaved}</span>}
                {updateDeviceMutation.isError && <span className="text-xs text-red-400">❌ Save failed</span>}
              </div>
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
