import type { InsiderMetrics } from '@/types/trade'

interface InsiderAnalyticsProps {
  metrics: InsiderMetrics
}

function formatHours(hours: number | null): string {
  if (hours === null) return '-'
  if (hours < 1) return `${Math.round(hours * 60)}m`
  if (hours < 24) return `${hours.toFixed(1)}h`
  const days = hours / 24
  return `${days.toFixed(1)}d`
}

export default function InsiderAnalytics({ metrics }: InsiderAnalyticsProps) {
  const {
    win_rate,
    expected_win_rate,
    win_rate_edge,
    contrarian_trades,
    contrarian_wins,
    contrarian_win_rate,
    avg_hours_before_close,
    trades_within_24h,
    trades_within_1h,
    resolved_trades,
  } = metrics

  // Determine edge status for coloring
  const edgeClass = win_rate_edge !== null
    ? win_rate_edge > 10 ? 'text-green-700 font-medium'
      : win_rate_edge > 0 ? 'text-green-600'
        : win_rate_edge < -10 ? 'text-red-700'
          : 'text-ink-muted'
    : 'text-ink-muted'

  // Contrarian win rate coloring (beating 50% is good)
  const contrarianClass = contrarian_win_rate !== null
    ? contrarian_win_rate > 60 ? 'text-green-700 font-medium'
      : contrarian_win_rate > 50 ? 'text-green-600'
        : 'text-ink-muted'
    : 'text-ink-muted'

  // Timing coloring (faster = more suspicious)
  const timingClass = avg_hours_before_close !== null
    ? avg_hours_before_close < 24 ? 'text-amber-700 font-medium'
      : avg_hours_before_close < 168 ? 'text-amber-600'
        : 'text-ink-muted'
    : 'text-ink-muted'

  if (resolved_trades === 0) {
    return (
      <div className="p-4 border border-beige-border bg-beige-light h-full">
        <h3 className="font-serif text-sm font-medium mb-2">Performance Metrics</h3>
        <p className="text-xs text-ink-muted">No resolved trades to analyze</p>
      </div>
    )
  }

  return (
    <div className="p-4 border border-beige-border bg-beige-light h-full">
      <h3 className="font-serif text-sm font-medium mb-3">Performance Metrics</h3>

      <div className="space-y-3">
        {/* Win Rate vs Expected */}
        <div>
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-ink-muted">Win Rate vs Expected</span>
            <span className={`font-mono text-xs ${edgeClass}`}>
              {win_rate_edge !== null ? (win_rate_edge > 0 ? '+' : '') + win_rate_edge.toFixed(1) + '%' : '-'}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 h-1.5 bg-beige-dark rounded-sm overflow-hidden">
              <div
                className="h-full bg-ink transition-all"
                style={{ width: `${Math.min(win_rate || 0, 100)}%` }}
              />
            </div>
            <span className="font-mono text-[10px] text-ink-muted w-16 text-right">
              {win_rate?.toFixed(0)}% / {expected_win_rate?.toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Contrarian Success */}
        <div>
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-ink-muted">Contrarian Success</span>
            <span className={`font-mono text-xs ${contrarianClass}`}>
              {contrarian_win_rate !== null ? contrarian_win_rate.toFixed(0) + '%' : '-'}
            </span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 h-1.5 bg-beige-dark rounded-sm overflow-hidden">
              <div
                className="h-full bg-ink transition-all"
                style={{ width: `${Math.min(contrarian_win_rate || 0, 100)}%` }}
              />
            </div>
            <span className="font-mono text-[10px] text-ink-muted w-16 text-right">
              {contrarian_wins}/{contrarian_trades}
            </span>
          </div>
        </div>

        {/* Timing */}
        <div>
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-ink-muted">Avg Time Before Close</span>
            <span className={`font-mono text-xs ${timingClass}`}>
              {formatHours(avg_hours_before_close)}
            </span>
          </div>
          <div className="flex gap-3 mt-1 text-[10px] font-mono text-ink-muted">
            <span>&lt;24h: {trades_within_24h}</span>
            <span>&lt;1h: {trades_within_1h}</span>
          </div>
        </div>

        {/* Summary */}
        <div className="pt-2 border-t border-beige-border text-[10px] font-mono text-ink-muted">
          Based on {resolved_trades} resolved trade{resolved_trades !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  )
}
