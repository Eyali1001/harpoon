export interface Trade {
  tx_hash: string
  timestamp: string
  market_id: string | null
  market_title: string | null
  outcome: string | null
  side: string | null
  amount: string | null
  price: string | null
  token_id: string | null
  polygonscan_url: string
}

export interface ProfileInfo {
  name: string | null
  pseudonym: string | null
  profile_image: string | null
  bio: string | null
  profile_url: string | null
}

export interface TimezoneAnalysis {
  hourly_distribution: number[]
  inferred_timezone: string | null
  inferred_utc_offset: number | null
  activity_center_utc: number | null
}

export interface CategoryStat {
  name: string
  count: number
  percentage: number
  pnl: number | null
}

export interface InsiderMetrics {
  win_rate: number | null
  expected_win_rate: number | null
  win_rate_edge: number | null
  contrarian_trades: number
  contrarian_wins: number
  contrarian_win_rate: number | null
  avg_hours_before_close: number | null
  trades_within_24h: number
  trades_within_1h: number
  resolved_trades: number
  total_trades: number
}

export interface TradesResponse {
  address: string
  profile: ProfileInfo | null
  trades: Trade[]
  total_count: number
  page: number
  limit: number
  total_earnings: string | null
  timezone_analysis: TimezoneAnalysis | null
  top_categories: CategoryStat[]
  insider_metrics: InsiderMetrics | null
}
