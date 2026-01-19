'use client'

import { useState } from 'react'

interface SearchInputProps {
  onSearch: (input: string) => void
  loading: boolean
}

export default function SearchInput({ onSearch, loading }: SearchInputProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSearch(input.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter wallet address or Polymarket profile URL"
          className="w-full px-0 py-3 bg-transparent border-0 border-b-2 border-ink font-mono text-base placeholder:text-ink-muted focus:outline-none focus:border-ink-light transition-colors"
          disabled={loading}
        />
      </div>
      <button
        type="submit"
        disabled={loading || !input.trim()}
        className="px-6 py-2 bg-ink text-beige font-mono text-sm tracking-wide hover:bg-ink-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Loading...' : 'View Trades'}
      </button>
    </form>
  )
}
