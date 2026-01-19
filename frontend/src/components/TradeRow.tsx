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

function truncateMarketTitle(title: string | null): string {
  if (!title) return '-'
  if (title.length <= 40) return title
  return title.substring(0, 37) + '...'
}

export default function TradeRow({ trade }: TradeRowProps) {
  const sideClass = trade.side === 'buy'
    ? 'text-green-700'
    : trade.side === 'sell'
    ? 'text-red-700'
    : ''

  return (
    <tr className="border-b border-beige-border hover:bg-beige-dark transition-colors">
      <td className="py-3 pr-4 whitespace-nowrap text-ink-muted">
        {formatTimestamp(trade.timestamp)}
      </td>
      <td className="py-3 pr-4" title={trade.market_title || undefined}>
        {truncateMarketTitle(trade.market_title)}
      </td>
      <td className={`py-3 pr-4 uppercase font-medium ${sideClass}`}>
        {trade.side || '-'}
      </td>
      <td className="py-3 pr-4">
        {trade.outcome || '-'}
      </td>
      <td className="py-3 pr-4 text-right tabular-nums">
        ${formatAmount(trade.amount)}
      </td>
      <td className="py-3 pr-4 text-right tabular-nums">
        {formatPrice(trade.price)}
      </td>
      <td className="py-3 text-right">
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
