import type { Trade } from '@/types/trade'

interface TradeRowProps {
  trade: Trade
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

function formatAmount(amount: string | null): string {
  if (!amount) return '-'
  const num = parseFloat(amount)
  return num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatPrice(price: string | null): string {
  if (!price) return '-'
  const num = parseFloat(price)
  return num.toFixed(4)
}


export default function TradeRow({ trade }: TradeRowProps) {
  const isRedeem = trade.side === 'redeem'

  const sideClass = trade.side === 'buy'
    ? 'text-green-700'
    : trade.side === 'sell'
    ? 'text-red-700'
    : trade.side === 'redeem'
    ? 'text-blue-700'
    : ''

  const outcomeClass = trade.outcome?.toLowerCase() === 'yes'
    ? 'text-green-700'
    : trade.outcome?.toLowerCase() === 'no'
    ? 'text-red-700'
    : ''

  return (
    <tr className={`border-b border-beige-border hover:bg-beige-dark transition-colors ${isRedeem ? 'bg-green-50' : ''}`}>
      <td className="py-2 md:py-3 pr-3 md:pr-4 whitespace-nowrap text-ink-muted">
        {formatTimestamp(trade.timestamp)}
      </td>
      <td className="py-2 md:py-3 pr-3 md:pr-4 max-w-[200px] md:max-w-xs">
        <span className="block text-xs md:text-sm leading-tight">
          {trade.market_title || '-'}
        </span>
      </td>
      <td className={`py-2 md:py-3 pr-3 md:pr-4 uppercase font-medium ${sideClass}`}>
        {trade.side || '-'}
      </td>
      <td className={`py-2 md:py-3 pr-3 md:pr-4 font-medium ${outcomeClass}`}>
        {trade.outcome || '-'}
      </td>
      <td className="py-2 md:py-3 pr-3 md:pr-4 text-right tabular-nums">
        ${formatAmount(trade.amount)}
      </td>
      <td className="py-2 md:py-3 pr-3 md:pr-4 text-right tabular-nums">
        {isRedeem ? (
          <span className="text-green-700 font-medium">+${formatAmount(trade.amount)}</span>
        ) : (
          formatPrice(trade.price)
        )}
      </td>
      <td className="py-2 md:py-3 pl-3 md:pl-4 text-right">
        <a
          href={trade.polygonscan_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-ink-muted hover:text-ink underline transition-colors"
        >
          View
        </a>
      </td>
    </tr>
  )
}
