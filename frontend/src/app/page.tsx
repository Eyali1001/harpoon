'use client'

import { useState, useCallback } from 'react'
import SearchInput from '@/components/SearchInput'
import TradeTable from '@/components/TradeTable'
import ActivityHistogram from '@/components/ActivityHistogram'
import TopCategories from '@/components/TopCategories'
import InsiderAnalytics from '@/components/InsiderAnalytics'
import MetricsExplainer from '@/components/MetricsExplainer'
import { fetchTrades, deleteTradesCache } from '@/lib/api'
import type { Trade, ProfileInfo, TimezoneAnalysis, CategoryStat, InsiderMetrics } from '@/types/trade'

export default function Home() {
  const [trades, setTrades] = useState<Trade[]>([])
  const [address, setAddress] = useState<string>('')
  const [profile, setProfile] = useState<ProfileInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [totalEarnings, setTotalEarnings] = useState<string | null>(null)
  const [timezoneAnalysis, setTimezoneAnalysis] = useState<TimezoneAnalysis | null>(null)
  const [topCategories, setTopCategories] = useState<CategoryStat[]>([])
  const [insiderMetrics, setInsiderMetrics] = useState<InsiderMetrics | null>(null)

  const handleSearch = useCallback(async (input: string) => {
    setLoading(true)
    setError(null)
    setPage(1)
    setProfile(null)
    setTotalEarnings(null)
    setTimezoneAnalysis(null)
    setTopCategories([])
    setInsiderMetrics(null)

    try {
      const response = await fetchTrades(input, 1)
      setTrades(response.trades)
      setAddress(response.address)
      setProfile(response.profile)
      setTotalCount(response.total_count)
      setTotalEarnings(response.total_earnings)
      setTimezoneAnalysis(response.timezone_analysis)
      setTopCategories(response.top_categories || [])
      setInsiderMetrics(response.insider_metrics || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch trades')
      setTrades([])
    } finally {
      setLoading(false)
    }
  }, [])

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

  const handleClearCache = async () => {
    if (!address) return
    if (!confirm('Clear cached data and refresh? This will re-fetch all trades from Polymarket.')) return

    setLoading(true)
    try {
      await deleteTradesCache(address)
      // Re-fetch trades
      const response = await fetchTrades(address, 1)
      setTrades(response.trades)
      setPage(1)
      setTotalCount(response.total_count)
      setTotalEarnings(response.total_earnings)
      setTimezoneAnalysis(response.timezone_analysis)
      setTopCategories(response.top_categories || [])
      setInsiderMetrics(response.insider_metrics || null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh')
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(totalCount / 50)
  const displayName = profile?.name || profile?.pseudonym

  return (
    <div className="space-y-4 sm:space-y-6 md:space-y-8">
      <section>
        <SearchInput onSearch={handleSearch} loading={loading} />
      </section>

      {loading && (
        <div className="w-full h-1 bg-beige-dark overflow-hidden">
          <div className="h-full bg-ink animate-progress-bar" />
        </div>
      )}

      {error && (
        <div className="p-3 md:p-4 border border-red-300 bg-red-50 text-red-800 font-mono text-xs md:text-sm">
          {error}
        </div>
      )}

      {address && !error && (
        <section>
          <div className="mb-4 md:mb-6 pb-4 border-b border-beige-border">
            {/* Profile Header */}
            <div className="flex items-start gap-3 md:gap-4">
              {profile?.profile_image && (
                <img
                  src={profile.profile_image}
                  alt={displayName || 'Profile'}
                  className="w-12 h-12 md:w-16 md:h-16 rounded-full object-cover border border-beige-border flex-shrink-0"
                />
              )}
              <div className="flex-1 min-w-0">
                {displayName && (
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mb-1">
                    {profile?.profile_url ? (
                      <a
                        href={profile.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-base md:text-lg font-serif hover:underline"
                      >
                        {displayName}
                      </a>
                    ) : (
                      <span className="text-base md:text-lg font-serif">{displayName}</span>
                    )}
                    {profile?.profile_url && (
                      <a
                        href={profile.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] md:text-xs text-ink-muted hover:text-ink"
                      >
                        View on Polymarket
                      </a>
                    )}
                  </div>
                )}
                <p className="text-xs md:text-sm font-mono text-ink-muted break-all">
                  {address}
                </p>
                <p className="text-xs md:text-sm font-mono text-ink-muted mt-1">
                  {totalCount} trade{totalCount !== 1 ? 's' : ''}
                </p>
                {totalEarnings && (
                  <p className={`text-base md:text-lg font-mono font-medium mt-2 ${
                    parseFloat(totalEarnings) >= 0 ? 'text-green-700' : 'text-red-700'
                  }`}>
                    Total: {parseFloat(totalEarnings) >= 0 ? '+' : ''}${parseFloat(totalEarnings).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                )}
              </div>
            </div>

            {/* Analytics Section - 2x2 Grid */}
            {(timezoneAnalysis || topCategories.length > 0 || insiderMetrics) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4 mt-4">
                <ActivityHistogram analysis={timezoneAnalysis || { hourly_distribution: Array(24).fill(0), inferred_timezone: null, inferred_utc_offset: null, activity_center_utc: null }} />
                <TopCategories categories={topCategories} />
                <InsiderAnalytics metrics={insiderMetrics || { win_rate: null, expected_win_rate: null, win_rate_edge: null, contrarian_trades: 0, contrarian_wins: 0, contrarian_win_rate: null, avg_hours_before_close: null, trades_within_24h: 0, trades_within_1h: 0, resolved_trades: 0, total_trades: 0 }} />
                <MetricsExplainer />
              </div>
            )}
          </div>

          <TradeTable trades={trades} loading={loading} />

          {totalPages > 1 && (
            <div className="mt-4 md:mt-6 flex items-center justify-center gap-2 md:gap-4 font-mono text-xs md:text-sm">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1 || loading}
                className="px-2 md:px-3 py-1 border border-beige-border hover:bg-beige-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Prev
              </button>
              <span className="text-ink-muted">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages || loading}
                className="px-2 md:px-3 py-1 border border-beige-border hover:bg-beige-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}

          <div className="mt-8 pt-4 border-t border-beige-border">
            <button
              onClick={handleClearCache}
              disabled={loading}
              className="text-xs font-mono text-ink-muted hover:text-ink disabled:opacity-50 transition-colors"
            >
              Clear cache & refresh
            </button>
          </div>
        </section>
      )}

      {!address && !loading && !error && (
        <div className="text-center py-8 md:py-16">
          <p className="text-ink-muted font-mono text-xs md:text-sm px-4">
            Enter a wallet address, username, or profile URL to analyze
          </p>
        </div>
      )}
    </div>
  )
}
