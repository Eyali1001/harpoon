import type { Trade } from '@/types/trade'
import TradeRow from './TradeRow'

interface TradeTableProps {
  trades: Trade[]
  loading: boolean
}

export default function TradeTable({ trades, loading }: TradeTableProps) {
  if (loading) {
    return (
      <div className="py-8 md:py-12 text-center">
        <p className="text-ink-muted font-mono text-xs md:text-sm">Loading trades...</p>
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="py-8 md:py-12 text-center">
        <p className="text-ink-muted font-mono text-xs md:text-sm">No trades found</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full font-mono text-xs md:text-sm min-w-[640px]">
        <thead>
          <tr className="border-b-2 border-ink">
            <th className="text-left py-2 md:py-3 pr-3 md:pr-4 font-medium">Time</th>
            <th className="text-left py-2 md:py-3 pr-3 md:pr-4 font-medium">Market</th>
            <th className="text-left py-2 md:py-3 pr-3 md:pr-4 font-medium">Side</th>
            <th className="text-left py-2 md:py-3 pr-3 md:pr-4 font-medium">Outcome</th>
            <th className="text-right py-2 md:py-3 pr-3 md:pr-4 font-medium">Amount</th>
            <th className="text-right py-2 md:py-3 pr-3 md:pr-4 font-medium">Price</th>
            <th className="text-right py-2 md:py-3 pl-3 md:pl-4 font-medium">Tx</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <TradeRow key={trade.tx_hash} trade={trade} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
