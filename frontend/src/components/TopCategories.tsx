import type { CategoryStat } from '@/types/trade'

interface TopCategoriesProps {
  categories: CategoryStat[]
}

export default function TopCategories({ categories }: TopCategoriesProps) {
  if (!categories || categories.length === 0) {
    return (
      <div className="p-4 border border-beige-border bg-beige-light h-full">
        <h3 className="font-serif text-sm font-medium mb-3">Top Categories</h3>
        <p className="text-xs text-ink-muted">No category data available</p>
      </div>
    )
  }

  const maxCount = Math.max(...categories.map(c => c.count))

  return (
    <div className="p-4 border border-beige-border bg-beige-light h-full">
      <h3 className="font-serif text-sm font-medium mb-3">Top Categories</h3>

      <div className="space-y-2">
        {categories.slice(0, 8).map((category) => (
          <div key={category.name} className="flex items-center gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-xs truncate" title={category.name}>
                  {category.name}
                </span>
                <span className="font-mono text-[10px] text-ink-muted ml-2">
                  {category.count} trades
                </span>
              </div>
              <div className="h-1.5 bg-beige-dark rounded-sm overflow-hidden">
                <div
                  className="h-full bg-ink transition-all"
                  style={{ width: `${(category.count / maxCount) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
