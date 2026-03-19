/** Settings page — all configuration editable in the UI with connection test buttons. */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import type { SettingOut } from '@/types/api'

const SECTION_LABELS: Record<string, string> = {
  battery: 'Battery Configuration',
  ha: 'Home Assistant Connection',
  ha_entities: 'Battery Entity IDs',
  octopus: 'Octopus Energy',
  prices: 'Price Classification',
  optimization: 'Optimization',
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
        <h1 className="text-xl font-semibold">Settings</h1>
        {hasEdits && (
          <button
            onClick={() => saveMutation.mutate()}
            className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded hover:opacity-90"
          >
            Save Changes
          </button>
        )}
      </div>

      {Object.entries(SECTION_LABELS).map(([category, label]) => {
        const sectionSettings = (settings as Record<string, SettingOut[]> | undefined)?.[category] ?? []
        if (!sectionSettings.length) return null

        return (
          <div key={category} className="rounded-lg border border-border bg-card p-4">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">{label}</h2>
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
                    className="flex-1 bg-secondary border border-border rounded px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              ))}
            </div>

            {/* Connection test buttons */}
            {category === 'ha' && (
              <div className="mt-3 flex items-center gap-3">
                <button onClick={testHA} className="text-xs px-3 py-1.5 bg-secondary rounded hover:bg-accent">
                  Test HA Connection
                </button>
                {testResults.ha && (
                  <span className={`text-xs ${testResults.ha.success ? 'text-green-400' : 'text-red-400'}`}>
                    {testResults.ha.message}
                  </span>
                )}
              </div>
            )}
            {category === 'octopus' && (
              <div className="mt-3 flex items-center gap-3">
                <button onClick={testOctopus} className="text-xs px-3 py-1.5 bg-secondary rounded hover:bg-accent">
                  Test Octopus API
                </button>
                {testResults.octopus && (
                  <span className={`text-xs ${testResults.octopus.success ? 'text-green-400' : 'text-red-400'}`}>
                    {testResults.octopus.message}
                  </span>
                )}
              </div>
            )}
            {category === 'influxdb' && (
              <div className="mt-3 flex items-center gap-3">
                <button onClick={testInflux} className="text-xs px-3 py-1.5 bg-secondary rounded hover:bg-accent">
                  Test InfluxDB
                </button>
                {testResults.influx && (
                  <span className={`text-xs ${testResults.influx.success ? 'text-green-400' : 'text-red-400'}`}>
                    {testResults.influx.message}
                  </span>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
