export default function MetricsExplainer() {
  return (
    <div className="p-4 border border-beige-border bg-beige-light h-full">
      <h3 className="font-serif text-sm font-medium mb-3">Understanding Metrics</h3>

      <div className="space-y-3 text-[11px] font-mono text-ink-muted">
        <div>
          <span className="text-ink font-medium">Win Rate Edge</span>
          <p>Actual win rate minus expected (entry price). Positive = beating the odds.</p>
        </div>

        <div>
          <span className="text-ink font-medium">Contrarian Success</span>
          <p>Win rate on low-probability bets (entry &lt;50%). High values may indicate informed trading.</p>
        </div>

        <div>
          <span className="text-ink font-medium">Time Before Close</span>
          <p>How early trades are placed before market resolution. Very late trading can be suspicious.</p>
        </div>

        <div>
          <span className="text-ink font-medium">Activity Pattern</span>
          <p>Hourly trade distribution used to infer the trader's likely timezone.</p>
        </div>

        <div>
          <span className="text-ink font-medium">Categories & P/L</span>
          <p>Most traded categories with profit/loss breakdown.</p>
        </div>
      </div>
    </div>
  )
}
