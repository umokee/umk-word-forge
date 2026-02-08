import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Volume2 } from 'lucide-react';

import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { getWord } from '@/api/words';
import { getLearningWord } from '@/api/learning';
import { cn, formatDate } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Mastery level visualization
// ---------------------------------------------------------------------------

const MASTERY_LABELS: Record<number, string> = {
  0: 'Not started',
  1: 'Introduction',
  2: 'Recognition',
  3: 'Recall',
  4: 'Context',
  5: 'Sentence',
  6: 'Production',
  7: 'Mastered',
};

const MASTERY_COLORS: Record<number, string> = {
  0: 'bg-[#2a2a2a]',
  1: 'bg-red-500',
  2: 'bg-orange-500',
  3: 'bg-amber-500',
  4: 'bg-yellow-400',
  5: 'bg-lime-500',
  6: 'bg-[#00ff88]',
  7: 'bg-[#00ff88]',
};

function MasteryDots({ level }: { level: number }) {
  return (
    <div className="flex items-center gap-2">
      {[1, 2, 3, 4, 5, 6, 7].map((l) => (
        <div
          key={l}
          className={cn(
            'h-3 w-3 rounded-full transition-colors',
            l <= level ? MASTERY_COLORS[l] : 'bg-[#2a2a2a]',
          )}
          title={MASTERY_LABELS[l]}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-10 w-48 rounded bg-[#1e1e1e]" />
      <div className="h-5 w-32 rounded bg-[#1e1e1e]" />
      <div className="h-4 w-64 rounded bg-[#1e1e1e]" />
      <div className="mt-6 h-48 rounded bg-[#1e1e1e]" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// WordDetail page
// ---------------------------------------------------------------------------

export default function WordDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const wordId = Number(id);

  // Fetch word data
  const {
    data: word,
    isLoading: wordLoading,
    error: wordError,
  } = useQuery({
    queryKey: ['word', wordId],
    queryFn: () => getWord(wordId),
    enabled: !isNaN(wordId),
  });

  // Fetch learning progress for this word
  const { data: learning } = useQuery({
    queryKey: ['learningWord', wordId],
    queryFn: () => getLearningWord(wordId),
    enabled: !isNaN(wordId),
    retry: false,
  });

  // -- Loading state -------------------------------------------------------
  if (wordLoading) {
    return (
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/words')}
          className="mb-4 gap-2"
        >
          <ArrowLeft size={16} />
          Back to Words
        </Button>
        <DetailSkeleton />
      </div>
    );
  }

  // -- Error state ---------------------------------------------------------
  if (wordError || !word) {
    return (
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/words')}
          className="mb-4 gap-2"
        >
          <ArrowLeft size={16} />
          Back to Words
        </Button>
        <Card className="text-center">
          <p className="text-red-400">Word not found.</p>
        </Card>
      </div>
    );
  }

  const masteryLevel = learning?.mastery_level ?? 0;

  return (
    <div>
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate('/words')}
        className="mb-4 gap-2"
      >
        <ArrowLeft size={16} />
        Back to Words
      </Button>

      {/* Word header */}
      <div className="mb-6">
        <div className="flex items-center gap-4">
          <h1 className="font-mono text-4xl font-bold text-[#e0e0e0]">
            {word.english}
          </h1>
          {word.cefr_level && (
            <Badge variant="accent">{word.cefr_level}</Badge>
          )}
        </div>

        {word.transcription && (
          <p className="mt-2 flex items-center gap-2 font-mono text-lg text-[#666666]">
            {word.transcription}
            <button
              className="rounded-sm p-1 text-[#666666] transition-colors hover:text-[#00ff88]"
              title="Listen to pronunciation"
            >
              <Volume2 size={16} />
            </button>
          </p>
        )}

        {word.part_of_speech && (
          <Badge variant="default" className="mt-2">
            {word.part_of_speech}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Left column */}
        <div className="space-y-4">
          {/* Translations */}
          <Card>
            <h2 className="mb-3 text-sm font-medium text-[#888888]">
              Translations
            </h2>
            <div className="space-y-1.5">
              {word.translations.map((t, i) => (
                <p key={i} className="text-base text-[#e0e0e0]">
                  {t}
                </p>
              ))}
              {word.translations.length === 0 && (
                <p className="text-sm text-[#666666]">No translations yet.</p>
              )}
            </div>
          </Card>

          {/* Mastery level */}
          <Card>
            <h2 className="mb-3 text-sm font-medium text-[#888888]">
              Mastery Level
            </h2>
            <div className="flex items-center gap-4">
              <MasteryDots level={masteryLevel} />
              <span className="text-sm text-[#e0e0e0]">
                {MASTERY_LABELS[masteryLevel]}
              </span>
            </div>
            {learning && (
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2">
                  <p className="text-xs text-[#666666]">Stability</p>
                  <p className="font-mono text-sm text-[#e0e0e0]">
                    {learning.fsrs_stability.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2">
                  <p className="text-xs text-[#666666]">Difficulty</p>
                  <p className="font-mono text-sm text-[#e0e0e0]">
                    {learning.fsrs_difficulty.toFixed(2)}
                  </p>
                </div>
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2">
                  <p className="text-xs text-[#666666]">Reviews</p>
                  <p className="font-mono text-sm text-[#e0e0e0]">
                    {learning.fsrs_reps}
                  </p>
                </div>
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2">
                  <p className="text-xs text-[#666666]">Lapses</p>
                  <p className="font-mono text-sm text-[#e0e0e0]">
                    {learning.fsrs_lapses}
                  </p>
                </div>
              </div>
            )}
            {learning?.next_review_at && (
              <p className="mt-3 text-xs text-[#666666]">
                Next review: {formatDate(learning.next_review_at)}
              </p>
            )}
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Context sentences */}
          <Card>
            <h2 className="mb-3 text-sm font-medium text-[#888888]">
              Context Sentences
            </h2>
            {word.contexts.length > 0 ? (
              <div className="space-y-3">
                {word.contexts.map((ctx) => (
                  <div
                    key={ctx.id}
                    className="rounded-sm border border-[#1e1e1e] bg-[#0a0a0a] px-4 py-3"
                  >
                    <p className="text-sm text-[#e0e0e0]">
                      {ctx.sentence_en.split(new RegExp(`(${word.english})`, 'gi')).map(
                        (part, i) =>
                          part.toLowerCase() === word.english.toLowerCase() ? (
                            <span key={i} className="font-bold text-[#00ff88]">
                              {part}
                            </span>
                          ) : (
                            <span key={i}>{part}</span>
                          ),
                      )}
                    </p>
                    {ctx.sentence_ru && (
                      <p className="mt-1 text-xs text-[#666666]">
                        {ctx.sentence_ru}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-[#666666]">
                No context sentences available.
              </p>
            )}
          </Card>

          {/* Word metadata */}
          <Card>
            <h2 className="mb-3 text-sm font-medium text-[#888888]">
              Details
            </h2>
            <div className="space-y-2">
              {word.frequency_rank && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#666666]">Frequency Rank</span>
                  <span className="font-mono text-sm text-[#e0e0e0]">
                    #{word.frequency_rank}
                  </span>
                </div>
              )}
              {word.cefr_level && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#666666]">CEFR Level</span>
                  <Badge variant="accent">{word.cefr_level}</Badge>
                </div>
              )}
              {word.part_of_speech && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#666666]">Part of Speech</span>
                  <span className="text-sm text-[#e0e0e0]">
                    {word.part_of_speech}
                  </span>
                </div>
              )}
              {learning?.created_at && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#666666]">Added</span>
                  <span className="text-sm text-[#e0e0e0]">
                    {formatDate(learning.created_at)}
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Review history */}
          {learning && (
            <Card>
              <h2 className="mb-3 text-sm font-medium text-[#888888]">
                Review Summary
              </h2>
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2 text-center">
                  <p className="text-xs text-[#666666]">Correct Streak</p>
                  <p className="font-mono text-lg font-bold text-[#00ff88]">
                    {learning.consecutive_correct}
                  </p>
                </div>
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2 text-center">
                  <p className="text-xs text-[#666666]">Wrong Streak</p>
                  <p className="font-mono text-lg font-bold text-red-400">
                    {learning.consecutive_wrong}
                  </p>
                </div>
                <div className="rounded-sm bg-[#1e1e1e] px-3 py-2 text-center">
                  <p className="text-xs text-[#666666]">Total Reviews</p>
                  <p className="font-mono text-lg font-bold text-[#e0e0e0]">
                    {learning.fsrs_reps}
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
