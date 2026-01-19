'use client'

import { useState } from 'react'
import SearchInput from '@/components/SearchInput'
import TradeTable from '@/components/TradeTable'
import { fetchTrades } from '@/lib/api'
import type { Trade, TradesResponse } from '@/types/trade'

export default function Home() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [address, setAddress] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)

  const handleSearch = async (input: string) => {
    setLoading(true)
    setError(null)
    setPage(1)

    try {
      const response = await fetchTrades(input, 1)
      setTrades(response.trades)
      setAddress(response.address)
      setTotalCount(response.total_count)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades')
      setTrades([])
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = async (newPage: number) => {
    if (!address) return

    setLoading(true)
    try {
      const response = await fetchTrades(address, newPage)
      setTrades(response.trades)
      setPage(newPage)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades')
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(totalCount / 50)

  return (
    <div className="space-y-8">
      <section>
        <SearchInput onSearch={handleSearch} loading={loading} />
      </section>

      {error && (
        <div className="p-4 border border-red-300 bg-red-50 text-red-800 font-mono text-sm">
          {error}
        </div>
      )}

      {address && !error && (
        <section>
          <div className="mb-4 pb-4 border-b border-beige-border">
            <p className="text-sm font-mono text-ink-muted">
              Showing trades for{' '}
              <span className="text-ink font-medium break-all">{address}</span>
            </p>
            <p className="text-sm font-mono text-ink-muted mt-1">
              {totalCount} total trade{totalCount !== 1 ? 's' : ''}
            </p>
          </div>

          <TradeTable trades={trades} loading={loading} />

          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-4 font-mono text-sm">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1 || loading}
                className="px-3 py-1 border border-beige-border hover:bg-beige-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-ink-muted">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages || loading}
                className="px-3 py-1 border border-beige-border hover:bg-beige-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </section>
      )}

      {!address && !loading && !error && (
        <div className="text-center py-16">
          <p className="text-ink-muted font-mono text-sm">
            Enter a Polymarket profile URL or Polygon wallet address to view trades
          </p>
        </div>
      )}
    </div>
  )
}
