/** Controls page — manual overrides for battery and immersions, system control. */

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, X } from 'lucide-react'
import { immersionApi } from '@/api/immersion'
import { overridesApi } from '@/api/overrides'
import { systemApi } from '@/api/settings'
import { useLiveState } from '@/hooks/useLiveState'
import type { ManualOverrideDetectedData } from '@/types/domain'

const DURATIONS = [30, 60, 120, 240, 480]

export default function Controls() {
  const qc = useQueryClient()
  const [selectedDuration, setSelectedDuration] = useState(120)
  // Reuse the shared WebSocket connection from useLiveState rather than opening
  // a second independent connection via useWebSocket directly.
  const { lastMessage } = useLiveState()
  // Persist the detection banner in local state so it survives subsequent WS
  // messages (pings, state updates) that would otherwise overwrite lastMessage.
  const [detectedOverride, setDetectedOverride] = useState<ManualOverrideDetectedData | null>(null)

  const { data: devices } = useQuery({
    queryKey: ['devices'],
    queryFn: immersionApi.listDevices,
  })

  const { data: overrideStatus } = useQuery({
    queryKey: ['override-status'],
    queryFn: overridesApi.getStatus,
    refetchInterval: 30_000,
  })

  // Auto-refresh override status and capture the banner when the backend detects
  // an external HA change. The banner is stored in local state so it persists
  // until the user explicitly dismisses it.
  useEffect(() => {
    if (lastMessage?.type === 'manual_override_detected') {
      setDetectedOverride(lastMessage.data)
      qc.invalidateQueries({ queryKey: ['override-status'] })
    }
  }, [lastMessage, qc])

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

      {/* Auto-detection notification banner — persists until dismissed */}
      {detectedOverride && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-300">External change detected</p>
            <p className="text-xs text-amber-400/80 mt-0.5">{detectedOverride.message}</p>
          </div>
          <button
            onClick={() => setDetectedOverride(null)}
            className="text-amber-400/60 hover:text-amber-300 shrink-0"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

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
            const isAutoDetected = status?.override?.source === 'ha_external'
            return (
              <div key={device.id} className="flex items-center justify-between p-3 rounded border border-border">
                <div>
                  <div className="font-medium text-sm">{device.display_name}</div>
                  {status?.has_active_override && (
                    <div className={`text-xs mt-0.5 ${isAutoDetected ? 'text-amber-400' : 'text-yellow-400'}`}>
                      {isAutoDetected ? (
                        <span className="flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          Auto-detected from HA — {status.time_remaining_minutes}min remaining
                        </span>
                      ) : (
                        <>Override active — {status.time_remaining_minutes}min remaining</>
                      )}
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
            {activeOverrides.map(s => {
              const isAutoDetected = s.override?.source === 'ha_external'
              return (
                <div
                  key={s.immersion_id}
                  className={`flex items-center justify-between p-2 rounded ${
                    isAutoDetected ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-secondary/50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isAutoDetected && (
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                    )}
                    <div>
                      <span className="text-sm">
                        {s.immersion_name}: {s.override?.desired_state ? 'ON' : 'OFF'} until{' '}
                        {s.override
                          ? new Date(s.override.expires_at).toLocaleTimeString('en-GB', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </span>
                      {isAutoDetected && (
                        <div className="text-xs text-amber-400/80">
                          Auto-detected — turned {s.override?.desired_state ? 'ON' : 'OFF'} manually in Home Assistant
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => clearMutation.mutate(s.immersion_id)}
                    className="text-xs text-muted-foreground hover:text-foreground shrink-0"
                  >
                    Clear
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
