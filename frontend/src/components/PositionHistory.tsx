'use client'

import { useMemo, useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { Trade } from '@/types/trade'

interface PositionHistoryProps {
  address: string
}

interface PositionPoint {
  timestamp: number
  date: string
  [key: string]: number | string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://harpoon-backend-production.up.railway.app'

// Generate distinct colors for markets
const COLORS = [
  '#2563eb', // blue
  '#dc2626', // red
  '#16a34a', // green
  '#9333ea', // purple
  '#ea580c', // orange
  '#0891b2', // cyan
  '#be185d', // pink
  '#65a30d', // lime
]

function getMarketColor(index: number): string {
  return COLORS[index % COLORS.length]
}

function truncateTitle(title: string, maxLen: number = 30): string {
  if (title.length <= maxLen) return title
  return title.slice(0, maxLen - 3) + '...'
}

export default function PositionHistory({ address }: PositionHistoryProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch all trades for this address
  useEffect(() => {
    async function fetchAllTrades() {
      if (!address) return

      setLoading(true)
      setError(null)

      try {
        // Fetch multiple pages to get all trades
        const allTrades: Trade[] = []
        let page = 1
        const limit = 100

        while (page <= 50) { // Max 5000 trades
          const response = await fetch(
            `${API_URL}/api/trades/${address}?page=${page}&limit=${limit}`
          )

          if (!response.ok) break

          const data = await response.json()
          allTrades.push(...data.trades)

          if (data.trades.length < limit) break
          page++
        }

        setTrades(allTrades)
      } catch (err) {
        setError('Failed to load trade history')
      } finally {
        setLoading(false)
      }
    }

    fetchAllTrades()
  }, [address])

  const { chartData, markets } = useMemo(() => {
    if (!trades || trades.length === 0) {
      return { chartData: [], markets: [] }
    }

    // Sort trades by timestamp (oldest first)
    const sortedTrades = [...trades].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    // Track position sizes per market
    const positions: Record<string, { shares: number; outcome: string; title: string }> = {}
    const dataPoints: PositionPoint[] = []
    const marketSet = new Set<string>()

    for (const trade of sortedTrades) {
      const price = parseFloat(trade.price || '0')
      const amount = parseFloat(trade.amount || '0')
      if (price <= 0 || amount <= 0) continue

      const shares = amount / price
      const marketKey = trade.market_slug || trade.market_id || 'unknown'
      const posKey = `${marketKey}:${trade.outcome}`

      if (!positions[posKey]) {
        positions[posKey] = {
          shares: 0,
          outcome: trade.outcome || 'Unknown',
          title: trade.market_title || marketKey,
        }
      }

      if (trade.side === 'buy') {
        positions[posKey].shares += shares
      } else if (trade.side === 'sell') {
        positions[posKey].shares = Math.max(0, positions[posKey].shares - shares)
      }

      // Only track markets with meaningful positions
      if (positions[posKey].shares > 10) {
        marketSet.add(posKey)
      }

      // Create data point with current state of all positions
      const timestamp = new Date(trade.timestamp).getTime()
      const date = new Date(trade.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })

      const point: PositionPoint = { timestamp, date }

      // Add all tracked positions to this point
      for (const [key, pos] of Object.entries(positions)) {
        if (marketSet.has(key)) {
          point[key] = Math.round(pos.shares)
        }
      }

      dataPoints.push(point)
    }

    // Get unique markets with their metadata
    const marketsArray = Array.from(marketSet).map((key) => ({
      key,
      ...positions[key],
    }))

    // Sort by final position size (largest first) and take top 6
    marketsArray.sort((a, b) => b.shares - a.shares)
    const topMarkets = marketsArray.slice(0, 6)

    return { chartData: dataPoints, markets: topMarkets }
  }, [trades])

  if (loading) {
    return (
      <div className="p-4 border border-beige-border bg-beige-light">
        <h3 className="font-serif text-sm font-medium mb-3">Position History</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-xs text-ink-muted">Loading position history...</p>
        </div>
      </div>
    )
  }

  if (error || chartData.length === 0 || markets.length === 0) {
    return (
      <div className="p-4 border border-beige-border bg-beige-light">
        <h3 className="font-serif text-sm font-medium mb-3">Position History</h3>
        <p className="text-xs text-ink-muted">
          {error || 'Not enough trade data to show position history'}
        </p>
      </div>
    )
  }

  return (
    <div className="p-4 border border-beige-border bg-beige-light">
      <h3 className="font-serif text-sm font-medium mb-2">Position History</h3>
      <p className="text-[10px] text-ink-muted mb-3">
        Shares held over time (solid = Yes, dashed = No)
      </p>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
            <XAxis
              dataKey="date"
              tick={{ fontSize: 9 }}
              tickLine={false}
              axisLine={{ stroke: '#d4c8b8' }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9 }}
              tickLine={false}
              axisLine={{ stroke: '#d4c8b8' }}
              tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
              width={35}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#faf8f5',
                border: '1px solid #d4c8b8',
                fontSize: '10px',
                padding: '6px',
              }}
              itemSorter={(item) => -(item.value as number || 0)}
              formatter={(value, name) => {
                if (typeof value !== 'number') return ['-', String(name)]
                const market = markets.find((m) => m.key === name)
                return [
                  `${value.toLocaleString()} shares`,
                  market ? truncateTitle(market.title, 20) : String(name),
                ]
              }}
            />
            {markets.map((market, idx) => (
              <Line
                key={market.key}
                type="stepAfter"
                dataKey={market.key}
                name={market.key}
                stroke={getMarketColor(idx)}
                strokeWidth={1.5}
                strokeDasharray={market.outcome?.toLowerCase() === 'no' ? '4 4' : undefined}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
        {markets.map((market, idx) => (
          <div key={market.key} className="flex items-center gap-1">
            <div
              className="w-3 h-0.5"
              style={{
                backgroundColor: getMarketColor(idx),
              }}
            />
            <span className="text-[9px] text-ink-muted" title={market.title}>
              {truncateTitle(market.title, 18)} ({market.outcome})
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
