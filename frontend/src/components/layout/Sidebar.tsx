/** Navigation sidebar with links to all 6 pages. */

import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Flame, History,
  Sliders, Settings, Zap, FlaskConical,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/prices', icon: TrendingUp, label: 'Prices' },
  { to: '/immersions', icon: Flame, label: 'Immersions' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/controls', icon: Sliders, label: 'Controls' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/dev', icon: FlaskConical, label: 'Dev Simulator' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-card border-r border-border flex flex-col">
      <div className="flex items-center gap-2 px-4 py-5 border-b border-border">
        <Zap className="h-6 w-6 text-yellow-400" />
        <span className="font-bold text-lg text-foreground">GridMind</span>
      </div>
      <nav className="flex-1 py-4">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-accent text-accent-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
