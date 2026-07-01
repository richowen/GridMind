/** Settings page — all configuration editable in the UI with connection test buttons. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import type { SettingOut } from '@/types/api'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

const SECTION_LABELS: Record<string, string> = {
  battery: 'Battery Configuration',
  ha: 'Home Assistant Connection',
  ha_entities: 'Battery Entity IDs',
  octopus: 'Octopus Energy',
  prices: 'Price Classification',
  optimization: 'Optimization',
  immersion: 'Immersion Control',
  influxdb: 'InfluxDB (optional)',
  system: 'System',
}

export default function Settings() {
  const qc = useQueryClient()
  const [edits, setEdits] = useState<Record<string, string>>({})
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.getAll,
  })

  const saveMutation = useMutation({
    mutationFn: () => settingsApi.updateBulk(edits),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['settings'] })
      setEdits({})
    },
  })

  const testHA = async () => {
    const r = await settingsApi.testHA()
    setTestResults(prev => ({ ...prev, ha: r }))
  }

  const testOctopus = async () => {
    const r = await settingsApi.testOctopus()
    setTestResults(prev => ({ ...prev, octopus: r }))
  }

  const testInflux = async () => {
    const r = await settingsApi.testInflux()
    setTestResults(prev => ({ ...prev, influx: r }))
  }

  const handleChange = (key: string, value: string) => {
    setEdits(prev => ({ ...prev, [key]: value }))
  }

  const getValue = (setting: SettingOut) => edits[setting.key] ?? setting.value

  const hasEdits = Object.keys(edits).length > 0

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl tracking-display text-foreground">Settings</h1>
        {hasEdits && (
          <Button variant="signal" onClick={() => saveMutation.mutate()}>
            Save Changes
          </Button>
        )}
      </div>

      {Object.entries(SECTION_LABELS).map(([category, label]) => {
        const sectionSettings = (settings as Record<string, SettingOut[]> | undefined)?.[category] ?? []
        if (!sectionSettings.length) return null

        return (
          <Card key={category}>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-4">{label}</h2>
            <div className="space-y-3">
              {sectionSettings.map((setting: SettingOut) => (
                <div key={setting.key} className="flex items-center gap-4">
                  <label className="text-sm text-muted-foreground w-48 shrink-0" title={setting.description ?? ''}>
                    {setting.description ?? setting.key}
                  </label>
                  <input
                    type={setting.value_type === 'bool' ? 'checkbox' : 'text'}
                    value={setting.value_type === 'bool' ? undefined : getValue(setting)}
                    checked={setting.value_type === 'bool' ? getValue(setting) === 'true' : undefined}
                    onChange={e => handleChange(
                      setting.key,
                      setting.value_type === 'bool' ? String(e.target.checked) : e.target.value
                    )}
                    className={setting.value_type === 'bool'
                      ? 'h-4 w-4 accent-signal'
                      : 'flex-1 bg-background border border-border rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-signal'
                    }
                  />
                </div>
              ))}
            </div>

            {/* Connection test buttons */}
            {category === 'ha' && (
              <div className="mt-3 flex items-center gap-3">
                <Button variant="outline" className="text-xs px-3 py-1.5" onClick={testHA}>
                  Test HA Connection
                </Button>
                {testResults.ha && (
                  <span className={`text-xs ${testResults.ha.success ? 'text-emerald-400' : 'text-red-400'}`}>
                    {testResults.ha.message}
                  </span>
                )}
              </div>
            )}
            {category === 'octopus' && (
              <div className="mt-3 flex items-center gap-3">
                <Button variant="outline" className="text-xs px-3 py-1.5" onClick={testOctopus}>
                  Test Octopus API
                </Button>
                {testResults.octopus && (
                  <span className={`text-xs ${testResults.octopus.success ? 'text-emerald-400' : 'text-red-400'}`}>
                    {testResults.octopus.message}
                  </span>
                )}
              </div>
            )}
            {category === 'influxdb' && (
              <div className="mt-3 flex items-center gap-3">
                <Button variant="outline" className="text-xs px-3 py-1.5" onClick={testInflux}>
                  Test InfluxDB
                </Button>
                {testResults.influx && (
                  <span className={`text-xs ${testResults.influx.success ? 'text-emerald-400' : 'text-red-400'}`}>
                    {testResults.influx.message}
                  </span>
                )}
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}
