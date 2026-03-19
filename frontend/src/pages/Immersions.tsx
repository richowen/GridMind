/** Immersion Manager page — device list, smart rules, and temperature targets. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Flame } from 'lucide-react'
import { immersionApi } from '@/api/immersion'
import type { ImmersionDeviceOut, SmartRuleOut, TempTargetOut } from '@/types/api'

export default function Immersions() {
  const qc = useQueryClient()
  const [selectedDevice, setSelectedDevice] = useState<ImmersionDeviceOut | null>(null)
  const [activeTab, setActiveTab] = useState<'rules' | 'targets'>('rules')

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

  const deleteRuleMutation = useMutation({
    mutationFn: ({ deviceId, ruleId }: { deviceId: number; ruleId: number }) =>
      immersionApi.deleteRule(deviceId, ruleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }),
  })

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
            onClick={() => setSelectedDevice(device)}
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
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 text-sm rounded ${
                  activeTab === tab ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
                }`}
              >
                {tab === 'rules' ? 'Smart Rules' : 'Temperature Targets'}
              </button>
            ))}
          </div>

          {activeTab === 'rules' && (
            <div>
              <table className="w-full text-sm mb-3">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground border-b border-border">
                    <th className="pb-2 pr-4">Priority</th>
                    <th className="pb-2 pr-4">Rule Name</th>
                    <th className="pb-2 pr-4">Action</th>
                    <th className="pb-2 pr-4">Logic</th>
                    <th className="pb-2">Enabled</th>
                    <th className="pb-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {(rules ?? []).map(rule => (
                    <tr key={rule.id} className="border-b border-border/50">
                      <td className="py-2 pr-4">{rule.priority}</td>
                      <td className="py-2 pr-4 font-medium">{rule.rule_name}</td>
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs ${rule.action === 'ON' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                          {rule.action}
                        </span>
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{rule.logic_operator}</td>
                      <td className="py-2 pr-4">
                        <span className={`text-xs ${rule.is_enabled ? 'text-green-400' : 'text-muted-foreground'}`}>
                          {rule.is_enabled ? '✓' : '✗'}
                        </span>
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => deleteRuleMutation.mutate({ deviceId: selectedDevice.id, ruleId: rule.id })}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'targets' && (
            <div className="space-y-3">
              {(targets ?? []).map(target => (
                <div key={target.id} className="rounded border border-border p-3">
                  <div className="font-medium text-sm">{target.target_name}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Ensure {target.target_temp_c}°C by {target.target_time} on days {target.days_of_week}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Rate: {target.heating_rate_c_per_hour}°C/hr | Buffer: {target.buffer_minutes}min
                  </div>
                </div>
              ))}
              {(!targets || targets.length === 0) && (
                <p className="text-sm text-muted-foreground">No temperature targets configured.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
