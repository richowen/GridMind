/** API calls for system settings and connection tests. */

import { api } from './client'
import type { SettingOut, ConnectionTestResult } from '@/types/api'

export const settingsApi = {
  getAll: () => api.get<Record<string, SettingOut[]>>('/settings'),
  updateBulk: (settings: Record<string, string>) =>
    api.put<{ updated: number }>('/settings', { settings }),
  getSetting: (key: string) => api.get<SettingOut>(`/settings/${key}`),
  updateSetting: (key: string, value: string) =>
    api.put<SettingOut>(`/settings/${key}`, { value }),
  testHA: () => api.post<ConnectionTestResult>('/settings/test/ha'),
  testOctopus: () => api.post<ConnectionTestResult>('/settings/test/octopus'),
  testInflux: () => api.post<ConnectionTestResult>('/settings/test/influx'),
  exportSettings: () => api.get<Record<string, string>>('/settings/export'),
  importSettings: (settings: Record<string, string>) =>
    api.post<{ imported: number }>('/settings/import', settings),
}

export const systemApi = {
  optimizeNow: () => api.post<{ status: string }>('/system/optimize-now'),
  pause: () => api.post<{ status: string }>('/system/pause'),
  resume: () => api.post<{ status: string }>('/system/resume'),
}
