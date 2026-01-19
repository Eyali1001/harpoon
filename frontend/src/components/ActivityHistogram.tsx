import type { TimezoneAnalysis } from '@/types/trade'

interface ActivityHistogramProps {
  analysis: TimezoneAnalysis
}

export default function ActivityHistogram({ analysis }: ActivityHistogramProps) {
  const { hourly_distribution, inferred_timezone, inferred_utc_offset, activity_center_utc } = analysis

  const maxCount = Math.max(...hourly_distribution, 1)
  const totalTrades = hourly_distribution.reduce((a, b) => a + b, 0)

  if (totalTrades === 0) {
    return null
  }

  // Calculate which hours are "daytime" (8am-11pm) in the inferred timezone
  const getDaytimeHours = (offset: number | null): Set<number> => {
    if (offset === null) return new Set()
    const daytime = new Set<number>()
    // Local 8am to 11pm is daytime
    for (let localHour = 8; localHour <= 23; localHour++) {
      let utcHour = localHour - offset
      if (utcHour < 0) utcHour += 24
      if (utcHour >= 24) utcHour -= 24
      daytime.add(Math.floor(utcHour))
    }
    return daytime
  }

  const daytimeHours = getDaytimeHours(inferred_utc_offset)

  // Format UTC offset for display
  const formatOffset = (offset: number | null): string => {
    if (offset === null) return ''
    const sign = offset >= 0 ? '+' : ''
    return `UTC${sign}${offset}`
  }

  // Get local hour from UTC hour
  const getLocalHour = (utcHour: number, offset: number | null): number => {
    if (offset === null) return utcHour
    let local = utcHour + offset
    if (local < 0) local += 24
    if (local >= 24) local -= 24
    return local
  }

  return (
    <div className="mt-4 p-4 border border-beige-border bg-beige-light">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-serif text-sm font-medium">Trading Activity Pattern</h3>
        {inferred_timezone && (
          <div className="text-right">
            <span className="text-xs font-mono text-ink-muted">Likely timezone: </span>
            <span className="font-mono text-sm font-medium">{inferred_timezone}</span>
            <span className="text-xs font-mono text-ink-muted ml-1">({formatOffset(inferred_utc_offset)})</span>
          </div>
        )}
      </div>

      {/* Histogram */}
      <div className="relative">
        {/* Hour labels - UTC */}
        <div className="flex justify-between text-[10px] font-mono text-ink-muted mb-1">
          <span>00</span>
          <span>06</span>
          <span>12</span>
          <span>18</span>
          <span>23</span>
        </div>

        {/* Bars */}
        <div className="flex items-end gap-[2px]" style={{ height: '80px' }}>
          {hourly_distribution.map((count, hour) => {
            const heightPx = maxCount > 0 ? Math.max((count / maxCount) * 72, count > 0 ? 4 : 0) : 0
            const isDaytime = daytimeHours.has(hour)
            const isActivityCenter = activity_center_utc !== null &&
              Math.abs(hour - activity_center_utc) < 0.5

            return (
              <div
                key={hour}
                className="flex-1 relative group flex items-end"
                title={`${hour.toString().padStart(2, '0')}:00 UTC: ${count} trades`}
              >
                <div
                  className={`w-full transition-all ${
                    isDaytime
                      ? 'bg-ink'
                      : 'bg-ink/30'
                  } ${isActivityCenter ? 'ring-2 ring-green-600' : ''}`}
                  style={{ height: `${heightPx}px` }}
                />
                {/* Tooltip on hover */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                  <div className="bg-ink text-beige text-[10px] font-mono px-1.5 py-0.5 rounded whitespace-nowrap">
                    {count} @ {hour.toString().padStart(2, '0')}:00
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Daytime indicator bracket */}
        {inferred_utc_offset !== null && (
          <div className="mt-2 relative h-4">
            {/* Calculate daytime range in UTC */}
            {(() => {
              const startLocal = 8 // 8am local
              const endLocal = 23 // 11pm local
              let startUTC = startLocal - inferred_utc_offset
              let endUTC = endLocal - inferred_utc_offset

              if (startUTC < 0) startUTC += 24
              if (startUTC >= 24) startUTC -= 24
              if (endUTC < 0) endUTC += 24
              if (endUTC >= 24) endUTC -= 24

              const startPercent = (startUTC / 24) * 100
              const endPercent = ((endUTC + 1) / 24) * 100

              // Handle wrap-around
              if (startUTC <= endUTC) {
                const width = endPercent - startPercent
                return (
                  <div
                    className="absolute h-1 bg-green-600/30 border-l-2 border-r-2 border-green-600"
                    style={{
                      left: `${startPercent}%`,
                      width: `${width}%`
                    }}
                  >
                    <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-green-700">
                      daytime
                    </span>
                  </div>
                )
              } else {
                // Wraps around midnight
                return (
                  <>
                    <div
                      className="absolute h-1 bg-green-600/30 border-l-2 border-green-600"
                      style={{ left: `${startPercent}%`, right: '0' }}
                    />
                    <div
                      className="absolute h-1 bg-green-600/30 border-r-2 border-green-600"
                      style={{ left: '0', width: `${endPercent}%` }}
                    />
                    <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-green-700">
                      daytime
                    </span>
                  </>
                )
              }
            })()}
          </div>
        )}

        {/* Local time labels */}
        {inferred_utc_offset !== null && (
          <div className="flex justify-between text-[9px] font-mono text-ink-muted mt-3 pt-1 border-t border-beige-border">
            <span>{getLocalHour(0, inferred_utc_offset).toString().padStart(2, '0')}:00</span>
            <span>{getLocalHour(6, inferred_utc_offset).toString().padStart(2, '0')}:00</span>
            <span>{getLocalHour(12, inferred_utc_offset).toString().padStart(2, '0')}:00</span>
            <span>{getLocalHour(18, inferred_utc_offset).toString().padStart(2, '0')}:00</span>
            <span>{getLocalHour(23, inferred_utc_offset).toString().padStart(2, '0')}:00</span>
            <span className="ml-1">local</span>
          </div>
        )}
      </div>
    </div>
  )
}
