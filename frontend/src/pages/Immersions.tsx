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
