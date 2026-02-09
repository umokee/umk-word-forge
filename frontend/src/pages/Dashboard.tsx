import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Flame,
  BookOpen,
  GraduationCap,
  Target,
  Zap,
  Clock,
  Layers,
  ArrowLeftRight,
  CheckCircle,
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

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { getDashboard } from '@/api/stats';
import { getDailyStatus } from '@/api/training';
import { cn, formatPercent } from '@/lib/utils';
import type { DailyStatus, TrainingMode } from '@/types';

// ---------------------------------------------------------------------------
// Skeleton loader for cards
// ---------------------------------------------------------------------------

function SkeletonCard({ className }: { className?: string }) {
  return (
    <Card className={cn('animate-pulse', className)}>
      <div className="h-4 w-24 rounded bg-[#1e1e1e]" />
      <div className="mt-3 h-8 w-16 rounded bg-[#1e1e1e]" />
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
  6: 'bg-[#00ff88]',
  7: 'bg-[#00ff88]',
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
    <div className="rounded-sm border border-[#2a2a2a] bg-[#141414] px-3 py-2 text-xs text-[#e0e0e0]">
      <p className="font-medium">{label}</p>
      <p className="text-[#888888]">{payload[0].value} words</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const navigate = useNavigate();
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    mode: TrainingMode | null;
  }>({ open: false, mode: null });

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  });

  const { data: dailyStatus } = useQuery({
    queryKey: ['dailyStatus'],
    queryFn: getDailyStatus,
  });

  const handleTrainingClick = (mode: TrainingMode) => {
    const isCompleted =
      mode === 'words'
        ? dailyStatus?.words?.exceeded
        : mode === 'phrasal'
          ? dailyStatus?.phrasal?.exceeded
          : dailyStatus?.irregular?.exceeded;

    if (isCompleted) {
      setConfirmDialog({ open: true, mode });
    } else {
      navigate(`/train/${mode}`);
    }
  };

  const handleConfirmContinue = () => {
    if (confirmDialog.mode) {
      navigate(`/train/${confirmDialog.mode}`);
    }
    setConfirmDialog({ open: false, mode: null });
  };

  // -- Loading state -------------------------------------------------------
  if (isLoading) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-lg font-bold uppercase tracking-wider text-[#00ff88]">[DASHBOARD]</h1>
          <p className="mt-1 text-xs text-[#666666]">Загрузка данных...</p>
        </div>
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
        <div className="mb-6">
          <h1 className="text-lg font-bold uppercase tracking-wider text-[#00ff88]">[DASHBOARD]</h1>
        </div>
        <div className="rounded-sm border border-[#2a2a2a] bg-[#141414] p-6 text-center">
          <p className="text-[#888888]">
            Не удалось загрузить данные. Попробуйте обновить страницу.
          </p>
        </div>
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
      {/* Header with streak */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold uppercase tracking-wider text-[#00ff88]">[DASHBOARD]</h1>
          <p className="mt-1 text-xs text-[#666666]">Ваш прогресс обучения</p>
        </div>
        <div className="flex items-center gap-3 rounded-sm border border-[#f59e0b]/20 bg-[#f59e0b]/5 px-4 py-2">
          <Flame size={20} className="text-[#f59e0b]" />
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-xl font-bold text-[#f59e0b]">{data.streak}</span>
            <span className="text-xs text-[#888888]">дней подряд</span>
          </div>
        </div>
      </div>

      {/* Today's stats - terminal widget style */}
      <div className="rounded-sm border border-[#2a2a2a] bg-[#141414]">
        <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#888888]">[СЕГОДНЯ]</h2>
        </div>
        <div className="grid grid-cols-3 divide-x divide-[#2a2a2a]">
          <div className="px-4 py-4 text-center">
            <p className="text-xs uppercase tracking-wide text-[#666666]">Повторено</p>
            <p className="mt-1 font-mono text-3xl font-bold text-[#e0e0e0]">{data.today_reviewed}</p>
          </div>
          <div className="px-4 py-4 text-center">
            <p className="text-xs uppercase tracking-wide text-[#666666]">Изучено</p>
            <p className="mt-1 font-mono text-3xl font-bold text-[#00ff88]">{data.today_learned}</p>
          </div>
          <div className="px-4 py-4 text-center">
            <p className="text-xs uppercase tracking-wide text-[#666666]">Точность</p>
            <p className="mt-1 font-mono text-3xl font-bold text-[#e0e0e0]">{formatPercent(data.today_accuracy)}</p>
          </div>
        </div>
      </div>

      {/* Training mode buttons */}
      <div className="mt-6 rounded-sm border border-[#2a2a2a] bg-[#141414]">
        <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#888888]">[ТРЕНИРОВКА]</h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <button
              onClick={() => handleTrainingClick('words')}
              className={cn(
                'group relative flex items-center gap-4 rounded-sm border p-4 text-left transition-all',
                dailyStatus?.words?.exceeded
                  ? 'border-[#00ff88]/30 bg-[#00ff88]/5 hover:border-[#00ff88]/50'
                  : 'border-[#2a2a2a] bg-[#1e1e1e] hover:border-[#00ff88]/50'
              )}
            >
              {dailyStatus?.words?.exceeded && (
                <div className="absolute right-3 top-3">
                  <CheckCircle size={18} className="text-[#00ff88]" />
                </div>
              )}
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-sm bg-[#00ff88]/10 text-[#00ff88]">
                <BookOpen size={24} />
              </div>
              <div>
                <p className="font-medium text-[#e0e0e0]">Слова</p>
                <p className="text-xs text-[#666666]">10,000+ слов</p>
              </div>
            </button>

            <button
              onClick={() => handleTrainingClick('phrasal')}
              className={cn(
                'group relative flex items-center gap-4 rounded-sm border p-4 text-left transition-all',
                dailyStatus?.phrasal?.exceeded
                  ? 'border-[#00aaff]/30 bg-[#00aaff]/5 hover:border-[#00aaff]/50'
                  : 'border-[#2a2a2a] bg-[#1e1e1e] hover:border-[#00aaff]/50'
              )}
            >
              {dailyStatus?.phrasal?.exceeded && (
                <div className="absolute right-3 top-3">
                  <CheckCircle size={18} className="text-[#00aaff]" />
                </div>
              )}
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-sm bg-[#00aaff]/10 text-[#00aaff]">
                <Layers size={24} />
              </div>
              <div>
                <p className="font-medium text-[#e0e0e0]">Фразовые глаголы</p>
                <p className="text-xs text-[#666666]">300+ выражений</p>
              </div>
            </button>

            <button
              onClick={() => handleTrainingClick('irregular')}
              className={cn(
                'group relative flex items-center gap-4 rounded-sm border p-4 text-left transition-all',
                dailyStatus?.irregular?.exceeded
                  ? 'border-[#ff6b6b]/30 bg-[#ff6b6b]/5 hover:border-[#ff6b6b]/50'
                  : 'border-[#2a2a2a] bg-[#1e1e1e] hover:border-[#ff6b6b]/50'
              )}
            >
              {dailyStatus?.irregular?.exceeded && (
                <div className="absolute right-3 top-3">
                  <CheckCircle size={18} className="text-[#ff6b6b]" />
                </div>
              )}
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-sm bg-[#ff6b6b]/10 text-[#ff6b6b]">
                <ArrowLeftRight size={24} />
              </div>
              <div>
                <p className="font-medium text-[#e0e0e0]">Неправильные глаголы</p>
                <p className="text-xs text-[#666666]">200+ глаголов</p>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Confirm dialog for exceeded daily limit */}
      {confirmDialog.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="mx-4 w-full max-w-sm rounded-sm border border-[#2a2a2a] bg-[#141414]">
            <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#f59e0b]">[ВНИМАНИЕ]</h3>
            </div>
            <div className="p-4">
              <p className="mb-4 text-sm text-[#e0e0e0]">
                Вы уже завершили тренировку по этой категории сегодня.
              </p>
              <p className="mb-6 text-xs text-[#888888]">
                Продолжить тренировку?
              </p>
              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  onClick={() => setConfirmDialog({ open: false, mode: null })}
                  className="flex-1"
                >
                  Отмена
                </Button>
                <Button onClick={handleConfirmContinue} className="flex-1">
                  Продолжить
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts row */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Weekly chart */}
        <div className="rounded-sm border border-[#2a2a2a] bg-[#141414]">
          <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#888888]">[НЕДЕЛЯ]</h2>
          </div>
          <div className="p-4">
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyChartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#2a2a2a"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="day"
                    tick={{ fill: '#888888', fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#888888', fontSize: 12 }}
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
                    fill="#00ff88"
                    radius={[2, 2, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Level distribution */}
        <div className="rounded-sm border border-[#2a2a2a] bg-[#141414]">
          <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#888888]">[УРОВНИ]</h2>
          </div>
          <div className="p-4">
            <div className="space-y-2.5">
              {[1, 2, 3, 4, 5, 6, 7].map((level) => {
                const count =
                  levelEntries.find((e) => e.level === level)?.count ?? 0;
                const pct = (count / maxLevelCount) * 100;
                return (
                  <div key={level} className="flex items-center gap-3">
                    <span className="w-24 text-xs text-[#888888]">
                      {LEVEL_LABELS[level]}
                    </span>
                    <div className="flex-1">
                      <div className="h-3 w-full overflow-hidden rounded-sm bg-[#1e1e1e]">
                        <div
                          className={cn('h-full transition-all', LEVEL_COLORS[level])}
                          style={{ width: `${Math.max(pct, count > 0 ? 2 : 0)}%` }}
                        />
                      </div>
                    </div>
                    <span className="w-8 text-right font-mono text-xs text-[#e0e0e0]">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Speech coverage */}
      <div className="mt-4 rounded-sm border border-[#2a2a2a] bg-[#141414]">
        <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#888888]">[ОХВАТ РЕЧИ]</h2>
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[#e0e0e0]">
              Вы знаете{' '}
              <span className="font-mono font-bold text-[#00ff88]">
                {data.total_words_known}
              </span>{' '}
              слов — это{' '}
              <span className="font-mono font-bold text-[#00ff88]">
                {formatPercent(data.coverage_percent)}
              </span>{' '}
              разговорной речи
            </p>
          </div>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-sm bg-[#1e1e1e]">
            <div
              className="h-full rounded-sm bg-[#00ff88] transition-all"
              style={{ width: `${Math.min(data.coverage_percent * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
