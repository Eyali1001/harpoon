import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Harpoon - Polymarket Trade Viewer',
  description: 'View all Polymarket trades for any wallet address',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-beige text-ink antialiased">
        <div className="max-w-5xl mx-auto px-6 py-12">
          <header className="mb-12">
            <h1 className="text-3xl font-serif tracking-tight">Harpoon</h1>
            <p className="text-ink-muted text-sm mt-1 font-mono">Polymarket Trade Viewer</p>
          </header>
          <main>{children}</main>
          <footer className="mt-16 pt-8 border-t border-beige-border">
            <p className="text-xs text-ink-muted font-mono">
              Data sourced from Polygon blockchain via TheGraph
            </p>
          </footer>
        </div>
      </body>
    </html>
  )
}
