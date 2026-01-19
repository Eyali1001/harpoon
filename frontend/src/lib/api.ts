import type { TradesResponse } from '@/types/trade'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchTrades(
  addressOrUrl: string,
  page: number = 1,
  limit: number = 50
): Promise<TradesResponse> {
  const encodedAddress = encodeURIComponent(addressOrUrl)
  const url = `${API_URL}/api/trades/${encodedAddress}?page=${page}&limit=${limit}`

  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail?.message || error.detail || 'Failed to fetch trades')
  }

  return response.json()
}
