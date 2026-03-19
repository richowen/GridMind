/** API calls for immersion devices, smart rules, and temperature targets. */

import { api } from './client'
import type {
  ImmersionDeviceOut, SmartRuleOut, TempTargetOut,
  ManualOverrideOut, OverrideStatusOut,
} from '@/types/api'

export const immersionApi = {
  // Devices
  listDevices: () => api.get<ImmersionDeviceOut[]>('/immersions/devices'),
  createDevice: (body: Partial<ImmersionDeviceOut>) =>
    api.post<ImmersionDeviceOut>('/immersions/devices', body),
  updateDevice: (id: number, body: Partial<ImmersionDeviceOut>) =>
    api.put<ImmersionDeviceOut>(`/immersions/devices/${id}`, body),
  deleteDevice: (id: number) => api.delete<void>(`/immersions/devices/${id}`),

  // Smart Rules
  listRules: (deviceId: number) =>
    api.get<SmartRuleOut[]>(`/immersions/${deviceId}/rules`),
  createRule: (deviceId: number, body: Partial<SmartRuleOut>) =>
    api.post<SmartRuleOut>(`/immersions/${deviceId}/rules`, body),
  updateRule: (deviceId: number, ruleId: number, body: Partial<SmartRuleOut>) =>
    api.put<SmartRuleOut>(`/immersions/${deviceId}/rules/${ruleId}`, body),
  deleteRule: (deviceId: number, ruleId: number) =>
    api.delete<void>(`/immersions/${deviceId}/rules/${ruleId}`),

  // Temperature Targets
  listTargets: (deviceId: number) =>
    api.get<TempTargetOut[]>(`/immersions/${deviceId}/targets`),
  createTarget: (deviceId: number, body: Partial<TempTargetOut>) =>
    api.post<TempTargetOut>(`/immersions/${deviceId}/targets`, body),
  updateTarget: (deviceId: number, targetId: number, body: Partial<TempTargetOut>) =>
    api.put<TempTargetOut>(`/immersions/${deviceId}/targets/${targetId}`, body),
  deleteTarget: (deviceId: number, targetId: number) =>
    api.delete<void>(`/immersions/${deviceId}/targets/${targetId}`),
}
