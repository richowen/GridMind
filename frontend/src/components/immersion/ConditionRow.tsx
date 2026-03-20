/** Reusable condition row for the smart rule form (price, SoC, solar, temp conditions). */

interface ConditionRowProps {
  label: string
  enabled: boolean
  onToggle: (v: boolean) => void
  operator: string
  onOperator: (v: string) => void
  operators?: string[]
  value: number
  onValue: (v: number) => void
  step?: number
  unit: string
}

const DEFAULT_OPERATORS = ['<', '<=', '>', '>=']

export function ConditionRow({
  label,
  enabled,
  onToggle,
  operator,
  onOperator,
  operators = DEFAULT_OPERATORS,
  value,
  onValue,
  step,
  unit,
}: ConditionRowProps) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="checkbox"
        checked={enabled}
        onChange={e => onToggle(e.target.checked)}
        className="accent-primary"
      />
      <span className="text-sm w-16 shrink-0">{label}</span>
      <select
        disabled={!enabled}
        className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
        value={operator}
        onChange={e => onOperator(e.target.value)}
      >
        {operators.map(op => (
          <option key={op} value={op}>{op}</option>
        ))}
      </select>
      <input
        type="number"
        step={step}
        disabled={!enabled}
        className="w-20 bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
        value={value}
        onChange={e => onValue(Number(e.target.value))}
      />
      <span className="text-xs text-muted-foreground">{unit}</span>
    </div>
  )
}

/** Time-window condition row — two time inputs instead of operator + value. */
interface TimeConditionRowProps {
  enabled: boolean
  onToggle: (v: boolean) => void
  timeStart: string
  onTimeStart: (v: string) => void
  timeEnd: string
  onTimeEnd: (v: string) => void
}

export function TimeConditionRow({
  enabled,
  onToggle,
  timeStart,
  onTimeStart,
  timeEnd,
  onTimeEnd,
}: TimeConditionRowProps) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="checkbox"
        checked={enabled}
        onChange={e => onToggle(e.target.checked)}
        className="accent-primary"
      />
      <span className="text-sm w-16 shrink-0">Time</span>
      <input
        type="time"
        disabled={!enabled}
        className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
        value={timeStart}
        onChange={e => onTimeStart(e.target.value)}
      />
      <span className="text-xs text-muted-foreground">to</span>
      <input
        type="time"
        disabled={!enabled}
        className="bg-secondary border border-border rounded px-2 py-1 text-sm disabled:opacity-40"
        value={timeEnd}
        onChange={e => onTimeEnd(e.target.value)}
      />
    </div>
  )
}
