import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Harpoon - Polymarket Wallet Analyzer',
  description: 'Analyze Polymarket wallet trading patterns and performance',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-beige text-ink antialiased">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 md:py-12">
          <header className="mb-6 sm:mb-8 md:mb-12">
            <h1 className="text-2xl sm:text-3xl font-serif tracking-tight">Harpoon</h1>
            <p className="text-ink-muted text-xs sm:text-sm mt-1 font-mono">Polymarket Wallet Analyzer</p>
          </header>
          <main>{children}</main>
          <footer className="mt-8 sm:mt-12 md:mt-16 pt-6 sm:pt-8 border-t border-beige-border">
            <p className="text-[10px] sm:text-xs text-ink-muted font-mono">
              Data sourced from Polygon blockchain via TheGraph
            </p>
          </footer>
        </div>
      </body>
    </html>
  )
}
