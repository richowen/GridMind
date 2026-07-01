/** Root app component — sets up React Router with a top pill-nav shell (no sidebar). */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from '@/components/layout/Header'
import Dashboard from '@/pages/Dashboard'
import Prices from '@/pages/Prices'
import Immersions from '@/pages/Immersions'
import History from '@/pages/History'
import Controls from '@/pages/Controls'
import Settings from '@/pages/Settings'
import DevSim from '@/pages/DevSim'
import Why from '@/pages/Why'
import { useLiveState } from '@/hooks/useLiveState'

/** The main app shell — top pill nav + centered max-width content column. */
function AppShell() {
  const { connected } = useLiveState()

  return (
    <div className="min-h-screen bg-background">
      <Header connected={connected} />
      <main className="mx-auto w-full max-w-[1200px] px-4 pb-16 pt-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/prices" element={<Prices />} />
          <Route path="/immersions" element={<Immersions />} />
          <Route path="/history" element={<History />} />
          <Route path="/controls" element={<Controls />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/dev" element={<DevSim />} />
          <Route path="/why" element={<Why />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
