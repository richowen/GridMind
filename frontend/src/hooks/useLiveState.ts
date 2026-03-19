/** Combines WebSocket live state with initial REST state for the dashboard. */

import { useEffect, useState } from 'react'
import { useWebSocket } from './useWebSocket'
import type { LiveState } from '@/types/domain'

const INITIAL_STATE: LiveState = {
  battery_soc: null,
  battery_mode: null,
  battery_discharge_current: null,
  solar_power_kw: null,
  solar_forecast_today_kwh: null,
  current_price_pence: null,
  price_classification: null,
  recommended_mode: null,
  decision_reason: null,
  last_updated: null,
}

export function useLiveState() {
  const { connected, lastMessage } = useWebSocket()
  const [state, setState] = useState<LiveState>(INITIAL_STATE)

  useEffect(() => {
    if (!lastMessage) return
    if (lastMessage.type === 'state' || lastMessage.type === 'optimization_result') {
      setState(prev => ({ ...prev, ...lastMessage.data }))
    }
  }, [lastMessage])

  return { state, connected }
}
