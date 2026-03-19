/** Controls page — manual overrides for battery and immersions, system control. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { immersionApi } from '@/api/immersion'
import { overridesApi } from '@/api/overrides'
import { systemApi } from '@/api/settings'

const DURATIONS = [30, 60, 120, 240, 480]

export default function Controls() {
  const qc = useQueryClient()
  const [selectedDuration, setSelectedDuration] = useState(120)

  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: immersionApi.listDevices,
  })

  const { data: overrideStatus } = useQuery({
    queryKey: ['override-status'],
    queryFn: overridesApi.getStatus,
    refetchInterval: 30_000,
  })

  const setOverrideMutation = useMutation({
    mutationFn: ({ id, state }: { id: number; state: boolean }) =>
      overridesApi.setOverride(id, state, selectedDuration),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['override-status'] }),
  })

  const clearMutation = useMutation({
    mutationFn: (id: number) => overridesApi.clearOverride(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['override-status'] }),
  })

  const clearAllMutation = useMutation({
    mutationFn: overridesApi.clearAll,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['override-status'] }),
  })

  const optimizeMutation = useMutation({ mutationFn: systemApi.optimizeNow })
  const pauseMutation = useMutation({ mutationFn: systemApi.pause })
  const resumeMutation = useMutation({ mutationFn: systemApi.resume })

  const activeOverrides = (overrideStatus ?? []).filter(s => s.has_active_override)

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Manual Controls</h1>

      {/* Duration Selector */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium mb-3">Override Duration</h2>
        <div className="flex gap-2 flex-wrap">
          {DURATIONS.map(d => (
            <button
              key={d}
              onClick={() => setSelectedDuration(d)}
              className={`px-3 py-1.5 text-sm rounded ${selectedDuration === d ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'}`}
            >
              {d >= 60 ? `${d / 60}h` : `${d}min`}
            </button>
          ))}
        </div>
      </div>

      {/* Immersion Overrides */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium mb-3">Immersion Overrides</h2>
        <div className="space-y-3">
          {(devices ?? []).map(device => {
            const status = overrideStatus?.find(s => s.immersion_id === device.id)
            return (
              <div key={device.id} className="flex items-center justify-between p-3 rounded border border-border">
                <div>
                  <div className="font-medium text-sm">{device.display_name}</div>
                  {status?.has_active_override && (
                    <div className="text-xs text-yellow-400">
                      Override active — {status.time_remaining_minutes}min remaining
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setOverrideMutation.mutate({ id: device.id, state: true })}
                    className="px-3 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded"
                  >
                    ON
                  </button>
                  <button
                    onClick={() => setOverrideMutation.mutate({ id: device.id, state: false })}
                    className="px-3 py-1 text-xs bg-red-600 hover:bg-red-500 text-white rounded"
                  >
                    OFF
                  </button>
                  <button
                    onClick={() => clearMutation.mutate(device.id)}
                    className="px-3 py-1 text-xs bg-secondary hover:bg-accent text-muted-foreground rounded"
                  >
                    Auto
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* System Control */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-medium mb-3">System Control</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => optimizeMutation.mutate()}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded"
          >
            Run Optimization Now
          </button>
          <button
            onClick={() => pauseMutation.mutate()}
            className="px-4 py-2 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded"
          >
            Pause Automation
          </button>
          <button
            onClick={() => resumeMutation.mutate()}
            className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 text-white rounded"
          >
            Resume Automation
          </button>
        </div>
      </div>

      {/* Active Overrides */}
      {activeOverrides.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium">Active Overrides</h2>
            <button
              onClick={() => clearAllMutation.mutate()}
              className="text-xs text-red-400 hover:text-red-300"
            >
              Clear All
            </button>
          </div>
          <div className="space-y-2">
            {activeOverrides.map(s => (
              <div key={s.immersion_id} className="flex items-center justify-between p-2 rounded bg-secondary/50">
                <span className="text-sm">
                  {s.immersion_name}: {s.override?.desired_state ? 'ON' : 'OFF'} until{' '}
                  {s.override ? new Date(s.override.expires_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '—'}
                </span>
                <button
                  onClick={() => clearMutation.mutate(s.immersion_id)}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
