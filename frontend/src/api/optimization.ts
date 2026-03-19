/** API calls for optimization, prices, and system state. */

import { api } from './client'
import type { OptimizationResultOut, PriceOut, PriceStats, SystemStateOut } from '@/types/api'

export const optimizationApi = {
  getRecommendation: () => api.get<OptimizationResultOut>('/recommendation/now'),
  getCurrentPrices: (hours = 48) => api.get<PriceOut[]>(`/prices/current?hours=${hours}`),
  getPriceStats: () => api.get<PriceStats>('/prices/stats'),
  refreshPrices: () => api.post<{ status: string }>('/prices/refresh'),
  getCurrentState: () => api.get<SystemStateOut>('/state/current'),
}
