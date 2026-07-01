/** Controls page — manual overrides for battery and immersions, system control. */

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, X } from 'lucide-react'
import { immersionApi } from '@/api/immersion'
import { overridesApi } from '@/api/overrides'
import { systemApi } from '@/api/settings'
import { useLiveState } from '@/hooks/useLiveState'
import type { ManualOverrideDetectedData } from '@/types/domain'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

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
      <h1 className="font-display text-2xl tracking-display text-foreground">Manual Controls</h1>

      {/* Auto-detection notification banner — persists until dismissed */}
      {detectedOverride && (
        <div className="flex items-start gap-3 rounded-lg border border-signal/40 bg-signal/10 p-4">
          <AlertTriangle className="h-5 w-5 text-signal shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">External change detected</p>
            <p className="text-xs text-muted-foreground mt-0.5">{detectedOverride.message}</p>
          </div>
          <button
            onClick={() => setDetectedOverride(null)}
            className="text-muted-foreground hover:text-foreground shrink-0"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Duration Selector */}
      <Card>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">Override Duration</h2>
        <div className="flex gap-2 flex-wrap">
          {DURATIONS.map(d => (
            <Button
              key={d}
              variant={selectedDuration === d ? 'signal' : 'outline'}
              onClick={() => setSelectedDuration(d)}
              className="px-3 py-1.5 text-sm"
            >
              {d >= 60 ? `${d / 60}h` : `${d}min`}
            </Button>
          ))}
        </div>
      </Card>

      {/* Immersion Overrides */}
      <Card>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">Immersion Overrides</h2>
        <div className="space-y-3">
          {(devices ?? []).map(device => {
            const status = overrideStatus?.find(s => s.immersion_id === device.id)
            const isAutoDetected = status?.override?.source === 'ha_external'
            return (
              <div key={device.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                <div>
                  <div className="font-medium text-sm text-foreground">{device.display_name}</div>
                  {status?.has_active_override && (
                    <div className="text-xs mt-0.5 text-signal">
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
                  <Button variant="filled" className="px-3 py-1 text-xs" onClick={() => setOverrideMutation.mutate({ id: device.id, state: true })}>
                    ON
                  </Button>
                  <Button variant="outline" className="px-3 py-1 text-xs" onClick={() => setOverrideMutation.mutate({ id: device.id, state: false })}>
                    OFF
                  </Button>
                  <Button variant="ghost" className="px-3 py-1 text-xs" onClick={() => clearMutation.mutate(device.id)}>
                    Auto
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      </Card>

      {/* System Control */}
      <Card>
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">System Control</h2>
        <div className="flex gap-3 flex-wrap">
          <Button variant="signal" onClick={() => optimizeMutation.mutate()}>
            Run Optimization Now
          </Button>
          <Button variant="outline" onClick={() => pauseMutation.mutate()}>
            Pause Automation
          </Button>
          <Button variant="outline" onClick={() => resumeMutation.mutate()}>
            Resume Automation
          </Button>
        </div>
      </Card>

      {/* Active Overrides */}
      {activeOverrides.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Active Overrides</h2>
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
                  className={`flex items-center justify-between p-2 rounded-lg ${
                    isAutoDetected ? 'bg-signal/10 border border-signal/30' : 'bg-fog'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {isAutoDetected && (
                      <AlertTriangle className="h-3.5 w-3.5 text-signal shrink-0" />
                    )}
                    <div>
                      <span className="text-sm text-foreground">
                        {s.immersion_name}: {s.override?.desired_state ? 'ON' : 'OFF'} until{' '}
                        {s.override
                          ? new Date(s.override.expires_at).toLocaleTimeString('en-GB', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </span>
                      {isAutoDetected && (
                        <div className="text-xs text-muted-foreground">
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
        </Card>
      )}
    </div>
  )
}
