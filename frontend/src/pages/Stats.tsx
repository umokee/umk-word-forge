import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { BookOpen, TrendingUp, BarChart3, Target } from 'lucide-react';

import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { getDailyStats, getHeatmap, getCoverage } from '@/api/stats';
import { getLearningStats } from '@/api/learning';
import { cn, formatPercent } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Custom chart tooltip
// ---------------------------------------------------------------------------

function ChartTooltip({
  active,
  payload,
  label,
  unit,
}: {
  active?: boolean;
  payload?: Array<{ value: number; name: string }>;
  label?: string;
  unit?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-sm border border-[#2A2A30] bg-[#141416] px-3 py-2 text-xs text-[#E8E8EC]">
      <p className="font-medium">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-[#8B8B96]">
          {entry.value}
          {unit ? ` ${unit}` : ''}
        </p>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Heatmap calendar (simplified grid)
// ---------------------------------------------------------------------------

const HEATMAP_COLORS = [
  'bg-[#1C1C20]', // level 0
  'bg-indigo-900/50', // level 1
  'bg-indigo-700/60', // level 2
  'bg-indigo-600/70', // level 3
  'bg-indigo-500', // level 4
];

function HeatmapCalendar({
  data,
}: {
  data: Array<{ date: string; count: number; level: number }>;
}) {
  // Build a lookup from date -> level
  const lookup = useMemo(() => {
    const map = new Map<string, number>();
    for (const entry of data) {
      map.set(entry.date, entry.level);
    }
    return map;
  }, [data]);

  // Generate 52 weeks x 7 days grid
  const today = new Date();
  const grid = useMemo(() => {
    const weeks: Array<Array<{ date: string; level: number }>> = [];

    // Start from 52 weeks ago, aligned to Sunday
    const start = new Date(today);
    start.setDate(start.getDate() - (52 * 7) - start.getDay());

    let currentWeek: Array<{ date: string; level: number }> = [];

    for (let i = 0; i <= 52 * 7 + today.getDay(); i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const level = lookup.get(dateStr) ?? 0;

      currentWeek.push({ date: dateStr, level: Math.min(level, 4) });

      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    }

    if (currentWeek.length > 0) {
      weeks.push(currentWeek);
    }

    return weeks;
  }, [lookup, today]);

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-[3px]">
        {grid.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {week.map((day, di) => (
              <div
                key={di}
                className={cn(
                  'h-[11px] w-[11px] rounded-[2px]',
                  HEATMAP_COLORS[day.level],
                )}
                title={`${day.date}: level ${day.level}`}
              />
            ))}
          </div>
        ))}
      </div>
      {/* Legend */}
      <div className="mt-3 flex items-center gap-1 text-xs text-[#5C5C66]">
        <span>Less</span>
        {HEATMAP_COLORS.map((color, i) => (
          <div
            key={i}
            className={cn('h-[11px] w-[11px] rounded-[2px]', color)}
          />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function SkeletonCard({ className }: { className?: string }) {
  return (
    <Card className={cn('animate-pulse', className)}>
      <div className="h-4 w-24 rounded bg-[#1C1C20]" />
      <div className="mt-3 h-8 w-16 rounded bg-[#1C1C20]" />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Stats page
// ---------------------------------------------------------------------------

export default function Stats() {
  // Daily stats (last 30 days)
  const { data: dailyStats, isLoading: dailyLoading } = useQuery({
    queryKey: ['dailyStats'],
    queryFn: () => getDailyStats(),
  });

  // Heatmap data
  const { data: heatmapData, isLoading: heatmapLoading } = useQuery({
    queryKey: ['heatmap'],
    queryFn: () => getHeatmap(),
  });

  // Coverage
  const { data: coverage, isLoading: coverageLoading } = useQuery({
    queryKey: ['coverage'],
    queryFn: () => getCoverage(),
  });

  // Learning stats
  const { data: learningStats, isLoading: learningLoading } = useQuery({
    queryKey: ['learningStats'],
    queryFn: () => getLearningStats(),
  });

  const isLoading = dailyLoading || heatmapLoading || coverageLoading || learningLoading;

  // -- Area chart data (last 30 days words reviewed) -----------------------
  const areaChartData = useMemo(
    () =>
      (dailyStats ?? []).map((d) => ({
        date: new Date(d.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        words: d.words_reviewed,
        accuracy: d.accuracy,
      })),
    [dailyStats],
  );

  // -- Accuracy by level bar chart data ------------------------------------
  const accuracyByLevel = useMemo(() => {
    if (!learningStats?.by_level) return [];
    return Object.entries(learningStats.by_level).map(([level, count]) => ({
      level: `Level ${level}`,
      count,
    }));
  }, [learningStats]);

  // -- Summary calculations ------------------------------------------------
  const totalWords = learningStats?.total_words ?? 0;
  const wordsLearned = learningStats?.by_state?.['review'] ?? 0;
  const wordsInProgress = learningStats?.by_state?.['learning'] ?? 0;

  // Average accuracy over last 30 days
  const avgAccuracy = useMemo(() => {
    if (!dailyStats?.length) return 0;
    const withData = dailyStats.filter((d) => d.words_reviewed > 0);
    if (withData.length === 0) return 0;
    const sum = withData.reduce((acc, d) => acc + d.accuracy, 0);
    return sum / withData.length;
  }, [dailyStats]);

  return (
    <div>
      <Header title="Statistics" subtitle="Track your learning progress" />

      {/* Summary cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            <Card>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-indigo-500/10">
                  <BookOpen size={20} className="text-indigo-400" />
                </div>
                <div>
                  <p className="text-xs text-[#8B8B96]">Total Words</p>
                  <p className="text-2xl font-bold text-[#E8E8EC]">
                    {totalWords}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-emerald-500/10">
                  <TrendingUp size={20} className="text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs text-[#8B8B96]">Words Learned</p>
                  <p className="text-2xl font-bold text-[#E8E8EC]">
                    {wordsLearned}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-amber-500/10">
                  <BarChart3 size={20} className="text-amber-400" />
                </div>
                <div>
                  <p className="text-xs text-[#8B8B96]">In Progress</p>
                  <p className="text-2xl font-bold text-[#E8E8EC]">
                    {wordsInProgress}
                  </p>
                </div>
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-500/10">
                  <Target size={20} className="text-rose-400" />
                </div>
                <div>
                  <p className="text-xs text-[#8B8B96]">Avg. Accuracy</p>
                  <p className="text-2xl font-bold text-[#E8E8EC]">
                    {formatPercent(avgAccuracy / 100)}
                  </p>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Area chart: words reviewed per day */}
        <Card>
          <h2 className="mb-4 text-sm font-medium text-[#8B8B96]">
            Words Reviewed (Last 30 Days)
          </h2>
          {dailyLoading ? (
            <div className="h-52 animate-pulse rounded bg-[#1C1C20]" />
          ) : (
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={areaChartData}>
                  <defs>
                    <linearGradient id="colorWords" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#2A2A30"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#8B8B96', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: '#8B8B96', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<ChartTooltip unit="words" />} />
                  <Area
                    type="monotone"
                    dataKey="words"
                    stroke="#6366F1"
                    strokeWidth={2}
                    fill="url(#colorWords)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Accuracy by level */}
        <Card>
          <h2 className="mb-4 text-sm font-medium text-[#8B8B96]">
            Words by Level
          </h2>
          {learningLoading ? (
            <div className="h-52 animate-pulse rounded bg-[#1C1C20]" />
          ) : (
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={accuracyByLevel}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#2A2A30"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="level"
                    tick={{ fill: '#8B8B96', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#8B8B96', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<ChartTooltip unit="words" />} />
                  <Bar
                    dataKey="count"
                    fill="#6366F1"
                    radius={[2, 2, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      {/* Heatmap */}
      <Card className="mt-4">
        <h2 className="mb-4 text-sm font-medium text-[#8B8B96]">
          Activity Calendar
        </h2>
        {heatmapLoading ? (
          <div className="h-24 animate-pulse rounded bg-[#1C1C20]" />
        ) : (
          <HeatmapCalendar data={heatmapData ?? []} />
        )}
      </Card>

      {/* Coverage */}
      <Card className="mt-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-[#8B8B96]">
              Speech Coverage
            </h2>
            {coverage && (
              <p className="mt-1 text-[#E8E8EC]">
                <span className="font-mono font-bold text-indigo-400">
                  {coverage.known_words}
                </span>{' '}
                words known —{' '}
                <span className="font-mono font-bold text-indigo-400">
                  {formatPercent(coverage.coverage_percent / 100)}
                </span>{' '}
                of everyday speech
              </p>
            )}
          </div>
          {coverage?.next_milestone && (
            <div className="text-right">
              <p className="text-xs text-[#5C5C66]">Next milestone</p>
              <p className="font-mono text-sm text-[#8B8B96]">
                {coverage.next_milestone.words_remaining} words to{' '}
                {coverage.next_milestone.coverage_at_milestone}%
              </p>
            </div>
          )}
        </div>
        {coverage && (
          <div className="mt-3 h-3 w-full overflow-hidden rounded-sm bg-[#1C1C20]">
            <div
              className="h-full rounded-sm bg-indigo-600 transition-all"
              style={{
                width: `${Math.min(coverage.coverage_percent, 100)}%`,
              }}
            />
          </div>
        )}
      </Card>
    </div>
  );
}
