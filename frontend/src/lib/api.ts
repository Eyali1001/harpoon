import type { TradesResponse } from '@/types/trade'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Log API URL at module load time
console.log('[API] NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL)
console.log('[API] Using API_URL:', API_URL)

export async function fetchTrades(
  addressOrUrl: string,
  page: number = 1,
  limit: number = 50
): Promise<TradesResponse> {
  const encodedAddress = encodeURIComponent(addressOrUrl)
  const url = `${API_URL}/api/trades/${encodedAddress}?page=${page}&limit=${limit}`

  console.log('[API] Fetching:', url)

  let response: Response
  try {
    response = await fetch(url)
  } catch (err) {
    // Network error - likely CORS, SSL, or connectivity issue
    const message = err instanceof Error ? err.message : 'Network error'
    console.error('[API] Fetch error:', err)
    throw new Error(`Failed to connect to API (${url}): ${message}`)
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail?.message || error.detail || 'Failed to fetch trades')
  }

  return response.json()
}
