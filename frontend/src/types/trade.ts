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

export interface TradesResponse {
  address: string
  profile: ProfileInfo | null
  trades: Trade[]
  total_count: number
  page: number
  limit: number
  total_earnings: string | null
  timezone_analysis: TimezoneAnalysis | null
}
