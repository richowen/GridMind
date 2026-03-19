/** API calls for history, actions, and statistics. */

import { api } from './client'
import type { OptimizationResultOut, SystemStateOut, SystemAction } from '@/types/api'

export const historyApi = {
  getRecommendations: (hours = 24) =>
    api.get<OptimizationResultOut[]>(`/history/recommendations?hours=${hours}`),
  getStates: (hours = 24) =>
    api.get<SystemStateOut[]>(`/history/states?hours=${hours}`),
  getActions: (hours = 24, actionType?: string) =>
    api.get<SystemAction[]>(
      `/history/actions?hours=${hours}${actionType ? `&action_type=${actionType}` : ''}`
    ),
  getDailyStats: () => api.get<{ date: string; optimization_runs: number; ha_actions: number }>('/stats/daily'),
}
