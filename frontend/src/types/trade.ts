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

export interface TradesResponse {
  address: string
  trades: Trade[]
  total_count: number
  page: number
  limit: number
}
