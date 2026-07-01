/** Floating pill navigation capsule + brand mark + live status — replaces the old boxy sidebar. */

import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, TrendingUp, Flame, History,
  Sliders, Settings, Zap, FlaskConical, HelpCircle,
  Wifi, WifiOff,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/prices', icon: TrendingUp, label: 'Prices' },
  { to: '/immersions', icon: Flame, label: 'Immersions' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/controls', icon: Sliders, label: 'Controls' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/dev', icon: FlaskConical, label: 'Dev' },
  { to: '/why', icon: HelpCircle, label: 'Why?' },
]

interface HeaderProps {
  connected: boolean
}

export default function Header({ connected }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 flex flex-col items-center gap-3 px-4 pt-4 pb-3 bg-background/95 backdrop-blur">
      <div className="flex w-full max-w-[1200px] items-center justify-between gap-4">
        {/* Brand mark */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="flex h-8 w-8 items-center justify-center rounded-pill bg-signal text-signal-foreground">
            <Zap className="h-4 w-4" fill="currentColor" />
          </span>
          <span className="font-display text-lg tracking-display text-foreground">GridMind</span>
        </div>

        {/* Floating nav capsule */}
        <nav className="hidden md:flex items-center gap-0.5 rounded-nav border border-border bg-card px-1.5 py-1.5 shadow-soft">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-pill px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-signal text-signal-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`
              }
            >
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Live status pill */}
        <div
          className={`flex items-center gap-1.5 rounded-pill border px-3 py-1.5 text-xs font-medium shrink-0 ${
            connected
              ? 'border-signal/30 bg-signal/10 text-signal'
              : 'border-border bg-card text-muted-foreground'
          }`}
        >
          {connected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          <span className="hidden sm:inline">{connected ? 'Live' : 'Offline'}</span>
        </div>
      </div>

      {/* Mobile nav — horizontal scroll pill row */}
      <nav className="flex md:hidden w-full max-w-[1200px] items-center gap-1 overflow-x-auto rounded-nav border border-border bg-card px-1.5 py-1.5 shadow-soft">
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-1.5 shrink-0 rounded-pill px-3 py-1.5 text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-signal text-signal-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent'
              }`
            }
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
