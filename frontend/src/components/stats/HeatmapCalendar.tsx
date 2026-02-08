import React, { useMemo, useState } from 'react';
import { cn } from '@/lib/utils';

interface HeatmapEntry {
  date: string;
  count: number;
  level: number;
}

interface HeatmapCalendarProps {
  data: HeatmapEntry[];
  className?: string;
}

const levelColors: Record<number, string> = {
  0: '#1e1e1e',
  1: '#0a3d2a',   // dark green
  2: '#0d5c3d',   // medium green
  3: '#00aa55',   // accent dim
  4: '#00ff88',   // accent bright
};

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const CELL_SIZE = 12;
const GAP = 2;

export function HeatmapCalendar({ data, className }: HeatmapCalendarProps) {
  const [tooltip, setTooltip] = useState<{ x: number; y: number; date: string; count: number } | null>(null);

  const { grid, monthPositions } = useMemo(() => {
    const lookup = new Map<string, HeatmapEntry>();
    for (const entry of data) {
      lookup.set(entry.date, entry);
    }

    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - (51 * 7 + startDate.getDay()));

    const columns: (HeatmapEntry & { dateObj: Date })[][] = [];
    const positions: { month: number; col: number }[] = [];
    let lastMonth = -1;

    const current = new Date(startDate);
    let col = 0;

    while (col < 52) {
      const week: (HeatmapEntry & { dateObj: Date })[] = [];

      for (let row = 0; row < 7; row++) {
        const dateStr = current.toISOString().slice(0, 10);
        const entry = lookup.get(dateStr) ?? { date: dateStr, count: 0, level: 0 };

        if (current.getMonth() !== lastMonth) {
          lastMonth = current.getMonth();
          positions.push({ month: lastMonth, col });
        }

        week.push({ ...entry, dateObj: new Date(current) });
        current.setDate(current.getDate() + 1);
      }

      columns.push(week);
      col++;
    }

    return { grid: columns, monthPositions: positions };
  }, [data]);

  return (
    <div className={cn('relative', className)}>
      <svg
        width={52 * (CELL_SIZE + GAP) + 2}
        height={7 * (CELL_SIZE + GAP) + 20}
        className="block"
      >
        {/* Month labels */}
        {monthPositions.map(({ month, col }, i) => (
          <text
            key={`${month}-${i}`}
            x={col * (CELL_SIZE + GAP)}
            y={10}
            fill="#888888"
            fontSize={10}
            fontFamily="monospace"
          >
            {monthLabels[month]}
          </text>
        ))}

        {/* Cells */}
        {grid.map((week, colIdx) =>
          week.map((day, rowIdx) => (
            <rect
              key={day.date}
              x={colIdx * (CELL_SIZE + GAP)}
              y={rowIdx * (CELL_SIZE + GAP) + 18}
              width={CELL_SIZE}
              height={CELL_SIZE}
              rx={2}
              fill={levelColors[day.level] ?? levelColors[0]}
              className="transition-colors"
              onMouseEnter={(e) => {
                const rect = (e.target as SVGRectElement).getBoundingClientRect();
                setTooltip({
                  x: rect.left + rect.width / 2,
                  y: rect.top,
                  date: day.date,
                  count: day.count,
                });
              }}
              onMouseLeave={() => setTooltip(null)}
            />
          ))
        )}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-[#141414] border border-[#2a2a2a] rounded-sm px-2 py-1 text-xs text-[#e0e0e0] pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y - 32,
            transform: 'translateX(-50%)',
          }}
        >
          <span className="font-mono">{tooltip.count}</span>{' '}
          {tooltip.count === 1 ? 'word' : 'words'} on{' '}
          <span className="text-[#888888]">{tooltip.date}</span>
        </div>
      )}
    </div>
  );
}
