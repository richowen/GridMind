/** Root app component — sets up React Router with sidebar layout. */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from '@/components/layout/Sidebar'
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

/** The main app shell (sidebar + header + content). */
function AppShell() {
  const { connected } = useLiveState()

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header connected={connected} />
        <main className="flex-1 overflow-y-auto p-6">
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
