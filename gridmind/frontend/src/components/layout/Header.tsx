/** Top header bar with live connection indicator and current time. */

import { Wifi, WifiOff } from 'lucide-react'

interface HeaderProps {
  connected: boolean
}

export default function Header({ connected }: HeaderProps) {
  const now = new Date().toLocaleString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short',
    hour: '2-digit', minute: '2-digit',
  })

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6">
      <h1 className="text-sm font-medium text-muted-foreground">
        Solar Battery Intelligence
      </h1>
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{now}</span>
        <div className={`flex items-center gap-1.5 text-xs font-medium ${
          connected ? 'text-green-400' : 'text-red-400'
        }`}>
          {connected
            ? <><Wifi className="h-3.5 w-3.5" /> Live</>
            : <><WifiOff className="h-3.5 w-3.5" /> Offline</>
          }
        </div>
      </div>
    </header>
  )
}
