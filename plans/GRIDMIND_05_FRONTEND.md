# GridMind — Frontend Design

## Technology

- **React 18** + TypeScript
- **Vite** — build tool
- **Tailwind CSS** + **shadcn/ui** — UI components
- **Recharts** — charts
- **React Router v6** — routing
- **TanStack Query (React Query)** — API data fetching + caching
- **WebSocket** — real-time updates

## Scaffold Setup

### package.json dependencies
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.56.0",
    "recharts": "^2.12.0",
    "lucide-react": "^0.441.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### shadcn/ui Setup Sequence
```bash
# 1. Create Vite project
npm create vite@latest frontend -- --template react-ts

# 2. Install dependencies
cd frontend && npm install

# 3. Install Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 4. Init shadcn/ui
npx shadcn-ui@latest init
# Choose: TypeScript, Default style, Slate base color, src/lib/utils.ts

# 5. Add required shadcn components
npx shadcn-ui@latest add button card dialog input select switch table badge tabs
```

---

## Page Routes

```
/                    → Dashboard
/prices              → Price Chart
/immersions          → Immersion Manager
/history             → History & Analytics
/controls            → Manual Controls
/settings            → Settings
```

---

## Dashboard Page (`/`)

Live overview of the entire system. Updates via WebSocket.

```
┌─────────────────────────────────────────────────────────────┐
│  🔋 GridMind                    ● Live    [Wed 18 Mar 18:42]│
├──────────────┬──────────────┬──────────────┬───────────────┤
│  BATTERY     │  SOLAR       │  PRICE NOW   │  MODE         │
│              │              │              │               │
│  ████░░ 72%  │  ⚡ 4.2 kW   │  🟡 8.3p     │  Self Use     │
│              │  Today: 18kWh│  Next: 5.1p  │  50A          │
│  Charging    │  Forecast    │  In 30min    │  discharge    │
├──────────────┴──────────────┴──────────────┴───────────────┤
│  IMMERSION DEVICES                                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🔥 Main Hot Water    ON  │ 52°C │ Schedule 18-20:00 │  │
│  │ 🔥 Lucy's Tank      OFF  │ 38°C │ Smart: waiting    │  │
│  └─────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  NEXT 12 HOURS (price sparkline)                            │
│  [Colour-coded bar chart - compact]                         │
├─────────────────────────────────────────────────────────────┤
│  RECENT DECISIONS                                           │
│  18:40  Self Use (50A)   8.3p  SOC 72%  Solar 4.2kW       │
│  18:10  Self Use (50A)   9.1p  SOC 68%  Solar 3.8kW       │
│  17:40  Force Charge     2.1p  SOC 55%  Solar 0.0kW       │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- `BatteryCard` — SOC gauge + mode
- `SolarCard` — current kW + today forecast
- `PriceCard` — current price + next period
- `ModeCard` — current battery mode + discharge current
- `ImmersionStatusCard` — all devices with temp + source
- `PriceSparkline` — compact 12hr bar chart
- `RecentDecisions` — last 10 decisions table

---

## Price Chart Page (`/prices`)

Full 48-hour price forecast with planned actions overlay.

```
┌─────────────────────────────────────────────────────────────┐
│  48-Hour Price Forecast              [Refresh] [Last updated: 18:30] │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                                                     │  │
│  │  [Full-width Recharts BarChart]                     │  │
│  │                                                     │  │
│  │  Colours:                                           │  │
│  │  🟢 Negative (< 0p) — get paid to use electricity  │  │
│  │  🟡 Cheap (< 10p)                                  │  │
│  │  🔵 Normal                                          │  │
│  │  🔴 Expensive (> 25p)                               │  │
│  │                                                     │  │
│  │  Overlays:                                          │  │
│  │  ⚡ Force Charge periods (blue highlight)           │  │
│  │  ▼ Current time marker                              │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  TODAY'S STATS                                              │
│  Min: -2.1p  Max: 38.4p  Avg: 14.2p  Median: 12.1p       │
│  Negative: 3 periods  Cheap: 8 periods  Expensive: 4       │
│                                                             │
│  PRICE TABLE (scrollable)                                   │
│  Time        Price    Classification    Action              │
│  18:00-18:30  8.3p    Normal           Self Use            │
│  18:30-19:00  5.1p    Cheap            Self Use            │
│  19:00-19:30 -1.2p    Negative         Force Charge        │
└─────────────────────────────────────────────────────────────┘
```

---

## Immersion Manager Page (`/immersions`)

Full control over all immersion devices, rules, schedules, and temperature targets.

```
┌─────────────────────────────────────────────────────────────┐
│  Immersion Control Manager                  [+ Add Device]  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔥 Main Hot Water Tank              ON | 52°C        │  │
│  │    switch.immersion_switch                           │  │
│  │    sensor.sonoff_1001e116e1_temperature              │  │
│  │    Source: Schedule (18:00-20:00)        [Edit][⚙]  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 🔥 Lucy's Tank                     OFF | 38°C        │  │
│  │    switch.immersion_lucy_switch                      │  │
│  │    sensor.t_h_sensor_with_external_probe_temp...     │  │
│  │    Source: Smart rule (waiting)          [Edit][⚙]  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ─── Configuring: Main Hot Water Tank ─────────────────── │
│                                                             │
│  [Temperature Targets] [Smart Rules]                    ← tabs │
│                                                             │
│  ── TEMPERATURE TARGETS ──────────────────────────────── │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Morning Hot Water                        [Edit][🗑]  │  │
│  │ Ensure 30°C by 09:00 on Mon,Tue,Wed,Thu,Fri         │  │
│  │ Heating rate: 5°C/hr | Buffer: 30min                │  │
│  │ Status: ✅ 52°C — already at target                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  [+ Add Temperature Target]                                 │
│                                                             │
│  ── SMART RULES ──────────────────────────────────────── │
│  ┌─────┬──────────────────────┬──────────────┬─────────┐ │
│  │ Pri │ Rule Name            │ Conditions   │ Action  │ │
│  ├─────┼──────────────────────┼──────────────┼─────────┤ │
│  │  1  │ Negative Price       │ price < 0p   │ ON  ✅  │ │
│  │  2  │ Very Cheap + Full    │ price<2p AND │ ON  ✅  │ │
│  │     │                      │ soc>=95%     │         │ │
│  │  3  │ Solar Surplus        │ solar>=5kW   │ ON  ✅  │ │
│  │     │                      │ AND soc>=90% │         │ │
│  │  99 │ Overheat Protection  │ temp>=70°C   │ OFF ✅  │ │
│  └─────┴──────────────────────┴──────────────┴─────────┘ │
│  [+ Add Rule]  Drag rows to reorder priority              │
└─────────────────────────────────────────────────────────────┘
```

**Rule Editor Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│  Edit Smart Rule                                            │
│                                                             │
│  Rule Name: [Solar Surplus                              ]   │
│  Action:    [ON ▼]                                         │
│  Priority:  [3]                                            │
│  Logic:     [AND ▼]  (all conditions must match)           │
│                                                             │
│  CONDITIONS:                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ☑ Solar Power    [>=▼]  [5.0]  kW                   │  │
│  │ ☑ Battery SoC    [>=▼]  [90.0] %                    │  │
│  │ ☐ Price          [< ▼]  [    ] p/kWh                │  │
│  │ ☐ Temperature    [< ▼]  [    ] °C                   │  │
│  │ ☐ Time of day    [    ] to [    ]                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [Cancel]                              [Save Rule]         │
└─────────────────────────────────────────────────────────────┘
```

---

## History Page (`/history`)

Charts and data over configurable time ranges.

```
┌─────────────────────────────────────────────────────────────┐
│  History & Analytics        [24h ▼] [7d] [30d] [Custom]   │
│                                                             │
│  BATTERY STATE OF CHARGE                                    │
│  [Recharts LineChart — SOC % vs time]                       │
│  [Overlay: Force Charge periods highlighted]                │
│                                                             │
│  SOLAR GENERATION                                           │
│  [Recharts AreaChart — kW vs time]                          │
│                                                             │
│  ELECTRICITY PRICE                                          │
│  [Recharts BarChart — p/kWh vs time, colour coded]          │
│                                                             │
│  IMMERSION TEMPERATURES                                     │
│  [Recharts LineChart — °C vs time, one line per device]     │
│  [Overlay: ON periods highlighted per device]               │
│                                                             │
│  DECISIONS LOG                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Time  │ Mode       │ SOC │ Price │ Solar │ Reason    │  │
│  ├───────┼────────────┼─────┼───────┼───────┼───────────┤  │
│  │ 18:40 │ Self Use   │ 72% │ 8.3p  │ 4.2kW │ ...       │  │
│  │ 18:10 │ Self Use   │ 68% │ 9.1p  │ 3.8kW │ ...       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Controls Page (`/controls`)

Manual overrides and system control.

```
┌─────────────────────────────────────────────────────────────┐
│  Manual Controls                                            │
│                                                             │
│  BATTERY MODE OVERRIDE                                      │
│  [Force Charge] [Self Use] [Feed-in First]                 │
│  Duration: [30min ▼]  [Apply Override]                     │
│                                                             │
│  IMMERSION OVERRIDES                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Main Hot Water (52°C)                                │  │
│  │ [ON] [OFF] [Auto]    Duration: [2 hours ▼]           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Lucy's Tank (38°C)                                   │  │
│  │ [ON] [OFF] [Auto]    Duration: [2 hours ▼]           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  SYSTEM CONTROL                                             │
│  Automation: [● Running]  [Pause]                          │
│  [Refresh Prices Now]  [Run Optimization Now]              │
│                                                             │
│  ACTIVE OVERRIDES                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Main Hot Water: ON until 20:30 (manual)    [Clear]   │  │
│  └──────────────────────────────────────────────────────┘  │
│  [Clear All Overrides]                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Settings Page (`/settings`)

All configuration editable in the UI. See [`GRIDMIND_SETTINGS_DESIGN.md`](GRIDMIND_SETTINGS_DESIGN.md) for full detail.

**Sections:**
1. Battery Configuration
2. Home Assistant Connection + Entity IDs
3. Octopus Energy
4. Price Classification Thresholds
5. Optimization Parameters
6. Load Measurement (CT clamp entities)
7. InfluxDB
8. System

---

## Component Architecture

```
src/
├── App.tsx                    ← Router + layout wrapper
│
├── pages/
│   ├── Dashboard.tsx          ← Composes dashboard cards
│   ├── Prices.tsx             ← Price chart + table
│   ├── Immersions.tsx         ← Device list + config tabs
│   ├── History.tsx            ← Multi-chart history view
│   ├── Controls.tsx           ← Override controls
│   └── Settings.tsx           ← Settings form
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx        ← Navigation sidebar
│   │   └── Header.tsx         ← Top bar with live indicator
│   │
│   ├── dashboard/
│   │   ├── BatteryCard.tsx    ← SOC gauge + mode
│   │   ├── SolarCard.tsx      ← Solar power + forecast
│   │   ├── PriceCard.tsx      ← Current price + next
│   │   ├── ModeCard.tsx       ← Battery mode + discharge A
│   │   └── ImmersionStatusCard.tsx  ← All devices status
│   │
│   ├── charts/
│   │   ├── PriceChart.tsx     ← 48hr bar chart
│   │   ├── PriceSparkline.tsx ← Compact 12hr sparkline
│   │   ├── SocChart.tsx       ← SOC line chart
│   │   ├── SolarChart.tsx     ← Solar area chart
│   │   └── TemperatureChart.tsx  ← Immersion temp chart
│   │
│   ├── immersion/
│   │   ├── DeviceCard.tsx     ← Device summary card
│   │   ├── DeviceEditor.tsx   ← Edit device dialog
│   │   ├── RulesTable.tsx     ← Rules list with drag-reorder
│   │   ├── RuleEditor.tsx     ← Add/edit rule dialog
│   │   └── TempTargetForm.tsx ← Temperature target form
│   │
│   └── ui/                    ← shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── input.tsx
│       ├── select.tsx
│       ├── switch.tsx
│       ├── table.tsx
│       └── ...
│
├── hooks/
│   ├── useWebSocket.ts        ← WebSocket connection + reconnect
│   ├── useLiveState.ts        ← Combined live state from WS
│   └── useApi.ts              ← React Query wrappers
│
├── api/
│   ├── client.ts              ← Base fetch/axios client
│   ├── optimization.ts        ← Recommendation, prices, state
│   ├── immersion.ts           ← Devices, rules, schedules, targets
│   ├── overrides.ts           ← Manual overrides
│   ├── history.ts             ← History, actions, stats
│   └── settings.ts            ← Settings CRUD + test connections
│
└── types/
    ├── api.ts                 ← API response types (matches backend Pydantic models)
    └── domain.ts              ← Domain types (Device, Rule, Schedule, etc.)
```

---

## Real-Time Updates (WebSocket)

The frontend connects to `ws://192.168.1.2:8000/ws` on load.

**Message types received from backend:**
```typescript
type WSMessage =
  | { type: 'state'; data: SystemState }           // Every 5min or on change
  | { type: 'optimization_result'; data: OptResult } // After each optimization
  | { type: 'prices_updated'; data: PriceData[] }  // After price refresh
  | { type: 'immersion_action'; data: ImmersionAction } // When immersion changes
  | { type: 'ping'; data: null }                   // Keep-alive

// Frontend sends:
type WSCommand =
  | { type: 'refresh' }                            // Request immediate state
```

**`useWebSocket.ts` hook:**
```typescript
export function useWebSocket() {
  const [state, setState] = useState<SystemState | null>(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws`);
    
    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 5 seconds
      setTimeout(() => reconnect(), 5000);
    };
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'state' || msg.type === 'optimization_result') {
        setState(msg.data);
      }
    };
    
    return () => ws.close();
  }, []);
  
  return { state, connected };
}
```
