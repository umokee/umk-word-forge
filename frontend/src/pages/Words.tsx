import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';

import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { getWords } from '@/api/words';
import { getLearningWords } from '@/api/learning';
import { cn, formatDate } from '@/lib/utils';
import type { UserWord } from '@/types';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;
const MASTERY_LEVELS = [0, 1, 2, 3, 4, 5, 6, 7] as const;
const PER_PAGE = 20;

const CEFR_BADGE_VARIANT: Record<string, 'default' | 'success' | 'warning' | 'error' | 'accent'> = {
  A1: 'success',
  A2: 'success',
  B1: 'warning',
  B2: 'warning',
  C1: 'accent',
  C2: 'accent',
};

// ---------------------------------------------------------------------------
// Skeleton row
// ---------------------------------------------------------------------------

function SkeletonRow() {
  return (
    <tr className="animate-pulse border-b border-[#1e1e1e]">
      <td className="px-4 py-3"><div className="h-4 w-24 rounded bg-[#1e1e1e]" /></td>
      <td className="px-4 py-3"><div className="h-4 w-32 rounded bg-[#1e1e1e]" /></td>
      <td className="px-4 py-3"><div className="h-4 w-10 rounded bg-[#1e1e1e]" /></td>
      <td className="px-4 py-3"><div className="h-4 w-12 rounded bg-[#1e1e1e]" /></td>
      <td className="px-4 py-3"><div className="h-4 w-20 rounded bg-[#1e1e1e]" /></td>
      <td className="px-4 py-3"><div className="h-4 w-20 rounded bg-[#1e1e1e]" /></td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Words page
// ---------------------------------------------------------------------------

export default function Words() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [cefrFilter, setCefrFilter] = useState<string | null>(null);
  const [masteryFilter, setMasteryFilter] = useState<number | null>(null);

  // Fetch words
  const { data: wordsData, isLoading: wordsLoading } = useQuery({
    queryKey: ['words', page, search, cefrFilter],
    queryFn: () =>
      getWords({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        cefr_level: cefrFilter ?? undefined,
      }),
  });

  // Fetch learning data to get mastery levels
  const { data: learningData } = useQuery({
    queryKey: ['learningWords', page, masteryFilter],
    queryFn: () =>
      getLearningWords({
        page,
        per_page: 100,
        level: masteryFilter ?? undefined,
      }),
  });

  // Build a lookup map of word_id -> learning data
  const learningMap = useMemo(() => {
    const map = new Map<number, UserWord>();
    if (learningData?.items) {
      for (const uw of learningData.items) {
        map.set(uw.word_id, uw);
      }
    }
    return map;
  }, [learningData]);

  const totalPages = wordsData ? Math.ceil(wordsData.total / PER_PAGE) : 0;

  // Debounced search
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  return (
    <div>
      <Header title="СЛОВА" subtitle="Ваш словарный запас" />

      {/* Search bar */}
      <div className="relative mb-4">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]"
        />
        <input
          type="text"
          value={search}
          onChange={handleSearch}
          placeholder="Search words..."
          className="w-full rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] py-2.5 pl-10 pr-4 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
      </div>

      {/* Filter buttons */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-xs text-[#666666]">CEFR:</span>
        {CEFR_LEVELS.map((level) => (
          <button
            key={level}
            onClick={() => {
              setCefrFilter(cefrFilter === level ? null : level);
              setPage(1);
            }}
            className={cn(
              'rounded-sm px-2.5 py-1 text-xs font-mono transition-colors',
              cefrFilter === level
                ? 'bg-[#00ff88] text-white'
                : 'bg-[#1e1e1e] text-[#888888] hover:bg-[#242428]',
            )}
          >
            {level}
          </button>
        ))}

        <span className="ml-3 text-xs text-[#666666]">Mastery:</span>
        {MASTERY_LEVELS.map((level) => (
          <button
            key={level}
            onClick={() => {
              setMasteryFilter(masteryFilter === level ? null : level);
              setPage(1);
            }}
            className={cn(
              'rounded-sm px-2.5 py-1 text-xs font-mono transition-colors',
              masteryFilter === level
                ? 'bg-[#00ff88] text-white'
                : 'bg-[#1e1e1e] text-[#888888] hover:bg-[#242428]',
            )}
          >
            {level}
          </button>
        ))}
      </div>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#2a2a2a] text-left text-xs text-[#666666]">
                <th className="px-4 py-3 font-medium">Word</th>
                <th className="px-4 py-3 font-medium">Translation</th>
                <th className="px-4 py-3 font-medium">Level</th>
                <th className="px-4 py-3 font-medium">Stability</th>
                <th className="px-4 py-3 font-medium">Next Review</th>
                <th className="px-4 py-3 font-medium">Added</th>
              </tr>
            </thead>
            <tbody>
              {wordsLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <SkeletonRow key={i} />
                  ))
                : (wordsData?.items ?? []).map((word) => {
                    const learning = learningMap.get(word.id);
                    return (
                      <tr
                        key={word.id}
                        onClick={() => navigate(`/words/${word.id}`)}
                        className="cursor-pointer border-b border-[#1e1e1e] transition-colors hover:bg-[#1e1e1e]"
                      >
                        <td className="px-4 py-3">
                          <span className="font-mono font-medium text-[#e0e0e0]">
                            {word.english}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-[#888888]">
                          {word.translations.join(', ')}
                        </td>
                        <td className="px-4 py-3">
                          {word.cefr_level && (
                            <Badge variant={CEFR_BADGE_VARIANT[word.cefr_level] ?? 'default'}>
                              {word.cefr_level}
                            </Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-[#888888]">
                          {learning
                            ? learning.fsrs_stability.toFixed(1)
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-[#888888]">
                          {learning?.next_review_at
                            ? formatDate(learning.next_review_at)
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs text-[#666666]">
                          {learning?.created_at
                            ? formatDate(learning.created_at)
                            : '—'}
                        </td>
                      </tr>
                    );
                  })}
            </tbody>
          </table>
        </div>

        {/* Empty state */}
        {!wordsLoading && (wordsData?.items ?? []).length === 0 && (
          <div className="px-4 py-12 text-center text-sm text-[#666666]">
            No words found.
          </div>
        )}
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-[#666666]">
            Showing {(page - 1) * PER_PAGE + 1}-
            {Math.min(page * PER_PAGE, wordsData?.total ?? 0)} of{' '}
            {wordsData?.total ?? 0}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={16} />
            </Button>
            <span className="font-mono text-sm text-[#888888]">
              {page} / {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
