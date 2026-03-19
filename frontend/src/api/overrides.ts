/** API calls for manual overrides. */

import { api } from './client'
import type { ManualOverrideOut, OverrideStatusOut } from '@/types/api'

export const overridesApi = {
  setOverride: (immersionId: number, desiredState: boolean, durationMinutes = 120) =>
    api.post<ManualOverrideOut>('/overrides/manual/set', {
      immersion_id: immersionId,
      desired_state: desiredState,
      duration_minutes: durationMinutes,
    }),
  getStatus: () => api.get<OverrideStatusOut[]>('/overrides/manual/status'),
  clearOverride: (deviceId: number) =>
    api.post<{ cleared: number }>(`/overrides/manual/clear/${deviceId}`),
  clearAll: () => api.post<{ cleared: number }>('/overrides/manual/clear-all'),
}
