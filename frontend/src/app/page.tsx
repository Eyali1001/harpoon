'use client'

import { useState } from 'react'
import SearchInput from '@/components/SearchInput'
import TradeTable from '@/components/TradeTable'
import { fetchTrades } from '@/lib/api'
import type { Trade, ProfileInfo } from '@/types/trade'

export default function Home() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [address, setAddress] = useState<string>('')
  const [profile, setProfile] = useState<ProfileInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [totalEarnings, setTotalEarnings] = useState<string | null>(null)

  const handleSearch = async (input: string) => {
    setLoading(true)
    setError(null)
    setPage(1)
    setProfile(null)
    setTotalEarnings(null)

    try {
      const response = await fetchTrades(input, 1)
      setTrades(response.trades)
      setAddress(response.address)
      setProfile(response.profile)
      setTotalCount(response.total_count)
      setTotalEarnings(response.total_earnings)
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
  const displayName = profile?.name || profile?.pseudonym

  return (
    <div className="space-y-8">
      <section>
        <SearchInput onSearch={handleSearch} loading={loading} />
      </section>

      {loading && (
        <div className="w-full h-1 bg-beige-dark overflow-hidden">
          <div className="h-full bg-ink animate-progress-bar" />
        </div>
      )}

      {error && (
        <div className="p-4 border border-red-300 bg-red-50 text-red-800 font-mono text-sm">
          {error}
        </div>
      )}

      {address && !error && (
        <section>
          <div className="mb-6 pb-4 border-b border-beige-border">
            <div className="flex items-start gap-4">
              {profile?.profile_image && (
                <img
                  src={profile.profile_image}
                  alt={displayName || 'Profile'}
                  className="w-16 h-16 rounded-full object-cover border border-beige-border"
                />
              )}
              <div className="flex-1 min-w-0">
                {displayName && (
                  <div className="flex items-center gap-2 mb-1">
                    {profile?.profile_url ? (
                      <a
                        href={profile.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-lg font-serif hover:underline"
                      >
                        {displayName}
                      </a>
                    ) : (
                      <span className="text-lg font-serif">{displayName}</span>
                    )}
                    {profile?.profile_url && (
                      <a
                        href={profile.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-ink-muted hover:text-ink"
                      >
                        View on Polymarket
                      </a>
                    )}
                  </div>
                )}
                <p className="text-sm font-mono text-ink-muted break-all">
                  {address}
                </p>
                <p className="text-sm font-mono text-ink-muted mt-1">
                  {totalCount} trade{totalCount !== 1 ? 's' : ''}
                </p>
                {totalEarnings && (
                  <p className={`text-lg font-mono font-medium mt-2 ${
                    parseFloat(totalEarnings) >= 0 ? 'text-green-700' : 'text-red-700'
                  }`}>
                    Total Earnings: {parseFloat(totalEarnings) >= 0 ? '+' : ''}${parseFloat(totalEarnings).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                )}
              </div>
            </div>
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
            Enter a Polygon wallet address to view Polymarket trades
          </p>
        </div>
      )}
    </div>
  )
}
