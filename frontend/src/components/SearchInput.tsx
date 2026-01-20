'use client'

import { useState, useEffect } from 'react'

interface SearchInputProps {
  onSearch: (input: string) => void
  loading: boolean
  initialValue?: string
}

export default function SearchInput({ onSearch, loading, initialValue = '' }: SearchInputProps) {
  const [input, setInput] = useState(initialValue)

  // Update input when initialValue changes (from URL routing)
  useEffect(() => {
    if (initialValue) {
      setInput(initialValue)
    }
  }, [initialValue])

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
          placeholder="Wallet address, username, or profile URL"
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
