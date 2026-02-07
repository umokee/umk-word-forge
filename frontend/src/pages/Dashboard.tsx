import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Flame,
  BookOpen,
  GraduationCap,
  Target,
  Zap,
  Clock,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { getDashboard } from '@/api/stats';
import { cn, formatPercent } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Skeleton loader for cards
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
// Level color mapping (mastery 1-7)
// ---------------------------------------------------------------------------

const LEVEL_COLORS: Record<number, string> = {
  1: 'bg-red-500',
  2: 'bg-orange-500',
  3: 'bg-amber-500',
  4: 'bg-yellow-400',
  5: 'bg-lime-500',
  6: 'bg-emerald-500',
  7: 'bg-indigo-500',
};

const LEVEL_LABELS: Record<number, string> = {
  1: 'Introduction',
  2: 'Recognition',
  3: 'Recall',
  4: 'Context',
  5: 'Sentence',
  6: 'Production',
  7: 'Mastered',
};

// ---------------------------------------------------------------------------
// Custom chart tooltip
// ---------------------------------------------------------------------------

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-sm border border-[#2A2A30] bg-[#141416] px-3 py-2 text-xs text-[#E8E8EC]">
      <p className="font-medium">{label}</p>
      <p className="text-[#8B8B96]">{payload[0].value} words</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  });

  // -- Loading state -------------------------------------------------------
  if (isLoading) {
    return (
      <div>
        <Header title="Dashboard" subtitle="Welcome back" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <SkeletonCard className="h-64" />
          <SkeletonCard className="h-64" />
        </div>
      </div>
    );
  }

  // -- Error state ---------------------------------------------------------
  if (error || !data) {
    return (
      <div>
        <Header title="Dashboard" />
        <Card className="text-center">
          <p className="text-red-400">
            Failed to load dashboard data. Please try again later.
          </p>
        </Card>
      </div>
    );
  }

  // -- Format weekly chart data --------------------------------------------
  const weeklyChartData = (data.weekly_data ?? []).map((d) => ({
    day: new Date(d.date).toLocaleDateString('en-US', { weekday: 'short' }),
    words: d.words_reviewed,
  }));

  // -- Level distribution max for bar sizing --------------------------------
  const levelEntries = Object.entries(data.level_distribution).map(
    ([level, count]) => ({
      level: Number(level),
      count: count as number,
    }),
  );
  const maxLevelCount = Math.max(1, ...levelEntries.map((e) => e.count));

  return (
    <div>
      {/* Greeting + streak */}
      <div className="mb-6 flex items-center justify-between">
        <Header title="Dashboard" subtitle="Welcome back" className="mb-0" />
        <div className="flex items-center gap-2 text-amber-400">
          <Flame size={22} />
          <span className="text-lg font-bold">{data.streak}</span>
          <span className="text-sm text-[#8B8B96]">day streak</span>
        </div>
      </div>

      {/* Today's stats cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-indigo-500/10">
              <BookOpen size={20} className="text-indigo-400" />
            </div>
            <div>
              <p className="text-xs text-[#8B8B96]">Words Reviewed</p>
              <p className="text-2xl font-bold text-[#E8E8EC]">
                {data.today_reviewed}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-emerald-500/10">
              <GraduationCap size={20} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-[#8B8B96]">New Words Learned</p>
              <p className="text-2xl font-bold text-[#E8E8EC]">
                {data.today_learned}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-sm bg-amber-500/10">
              <Target size={20} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-[#8B8B96]">Accuracy</p>
              <p className="text-2xl font-bold text-[#E8E8EC]">
                {formatPercent(data.today_accuracy)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Action buttons */}
      <div className="mt-6 flex gap-3">
        <Button
          size="lg"
          onClick={() => navigate('/train?duration=5')}
          className="gap-2"
        >
          <Zap size={18} />
          Quick Training (5 min)
        </Button>
        <Button
          variant="secondary"
          size="lg"
          onClick={() => navigate('/train?duration=15')}
          className="gap-2"
        >
          <Clock size={18} />
          Full Training (15 min)
        </Button>
      </div>

      {/* Charts row */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Weekly chart */}
        <Card>
          <h2 className="mb-4 text-sm font-medium text-[#8B8B96]">
            Words This Week
          </h2>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyChartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#2A2A30"
                  vertical={false}
                />
                <XAxis
                  dataKey="day"
                  tick={{ fill: '#8B8B96', fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#8B8B96', fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  content={<ChartTooltip />}
                  cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }}
                />
                <Bar
                  dataKey="words"
                  fill="#6366F1"
                  radius={[2, 2, 0, 0]}
                  maxBarSize={40}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Level distribution */}
        <Card>
          <h2 className="mb-4 text-sm font-medium text-[#8B8B96]">
            Level Distribution
          </h2>
          <div className="space-y-2.5">
            {[1, 2, 3, 4, 5, 6, 7].map((level) => {
              const count =
                levelEntries.find((e) => e.level === level)?.count ?? 0;
              const pct = (count / maxLevelCount) * 100;
              return (
                <div key={level} className="flex items-center gap-3">
                  <span className="w-20 text-xs text-[#8B8B96]">
                    {LEVEL_LABELS[level]}
                  </span>
                  <div className="flex-1">
                    <div className="h-4 w-full overflow-hidden rounded-sm bg-[#1C1C20]">
                      <div
                        className={cn('h-full transition-all', LEVEL_COLORS[level])}
                        style={{ width: `${Math.max(pct, count > 0 ? 2 : 0)}%` }}
                      />
                    </div>
                  </div>
                  <span className="w-8 text-right font-mono text-xs text-[#E8E8EC]">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Speech coverage */}
      <Card className="mt-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-[#8B8B96]">
              Speech Coverage
            </h2>
            <p className="mt-1 text-[#E8E8EC]">
              You know{' '}
              <span className="font-mono font-bold text-indigo-400">
                {data.total_words_known}
              </span>{' '}
              words — covering{' '}
              <span className="font-mono font-bold text-indigo-400">
                {formatPercent(data.coverage_percent)}
              </span>{' '}
              of speech
            </p>
          </div>
        </div>
        <div className="mt-3 h-3 w-full overflow-hidden rounded-sm bg-[#1C1C20]">
          <div
            className="h-full rounded-sm bg-indigo-600 transition-all"
            style={{ width: `${Math.min(data.coverage_percent * 100, 100)}%` }}
          />
        </div>
      </Card>
    </div>
  );
}
