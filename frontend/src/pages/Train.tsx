import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { X, CheckCircle, XCircle, ArrowRight, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useTrainingStore } from '@/stores/trainingStore';
import { createSession, submitAnswer, endSession } from '@/api/training';
import { useKeyboard } from '@/hooks/useKeyboard';
import { cn, formatDuration, formatPercent } from '@/lib/utils';
import type { AnswerResult, Exercise, SessionSummary } from '@/types';

// ---------------------------------------------------------------------------
// Exercise type components
// ---------------------------------------------------------------------------

interface ExerciseProps {
  exercise: Exercise;
  onAnswer: (answer: string) => void;
  disabled: boolean;
}

// Type 1 -- Introduction
function ExerciseIntroduction({ exercise, onAnswer, disabled }: ExerciseProps) {
  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">New word</p>
      <h2 className="font-mono text-5xl font-bold text-[#e0e0e0]">
        {exercise.english}
      </h2>
      {exercise.transcription && (
        <p className="font-mono text-lg text-[#666666]">
          {exercise.transcription}
        </p>
      )}
      {exercise.part_of_speech && (
        <Badge variant="accent">{exercise.part_of_speech}</Badge>
      )}
      <div className="space-y-1">
        {exercise.translations.map((t, i) => (
          <p key={i} className="text-lg text-[#e0e0e0]">
            {t}
          </p>
        ))}
      </div>
      {exercise.sentence_en && (
        <div className="mt-2 max-w-md rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3">
          <p className="text-sm text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-1 text-xs text-[#666666]">
              {exercise.sentence_ru}
            </p>
          )}
        </div>
      )}
      <Button
        size="lg"
        onClick={() => onAnswer('seen')}
        disabled={disabled}
        className="mt-4"
      >
        Got it
      </Button>
    </div>
  );
}

// Type 2 -- Recognition (multiple choice)
function ExerciseRecognition({ exercise, onAnswer, disabled }: ExerciseProps) {
  const prompt = exercise.reverse
    ? exercise.translations[0] ?? ''
    : exercise.english;
  const label = exercise.reverse
    ? 'Choose the correct English word'
    : 'Choose the correct translation';

  useKeyboard(
    {
      onOption: (index: number) => {
        if (!disabled && exercise.options && exercise.options[index]) {
          onAnswer(exercise.options[index]);
        }
      },
    },
    !disabled,
  );

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">{label}</p>
      <h2 className="font-mono text-4xl font-bold text-[#e0e0e0]">{prompt}</h2>
      {!exercise.reverse && exercise.transcription && (
        <p className="font-mono text-base text-[#666666]">
          {exercise.transcription}
        </p>
      )}
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-colors hover:border-[#00ff88] hover:bg-[#00ff88]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-[#2a2a2a] font-mono text-xs text-[#888888]">
              {idx + 1}
            </span>
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 3 -- Recall (type answer)
function ExerciseRecall({ exercise, onAnswer, disabled }: ExerciseProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onAnswer(input.trim());
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Type the translation</p>
      <h2 className="font-mono text-4xl font-bold text-[#e0e0e0]">
        {exercise.english}
      </h2>
      {exercise.transcription && (
        <p className="font-mono text-base text-[#666666]">
          {exercise.transcription}
        </p>
      )}
      <div className="mt-2 flex w-full max-w-md gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Your answer..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Check
        </Button>
      </div>
    </div>
  );
}

// Type 4 -- Context (gap fill with options)
function ExerciseContext({ exercise, onAnswer, disabled }: ExerciseProps) {
  useKeyboard(
    {
      onOption: (index: number) => {
        if (!disabled && exercise.options && exercise.options[index]) {
          onAnswer(exercise.options[index]);
        }
      },
    },
    !disabled,
  );

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Choose the correct translation in context</p>
      {exercise.sentence_en && (
        <div className="max-w-lg rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-5 py-4">
          <p className="text-base text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-1 text-xs text-[#666666]">
              {exercise.sentence_ru}
            </p>
          )}
        </div>
      )}
      <h2 className="font-mono text-3xl font-bold text-[#e0e0e0]">
        {exercise.english}
      </h2>
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-colors hover:border-[#00ff88] hover:bg-[#00ff88]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-[#2a2a2a] font-mono text-xs text-[#888888]">
              {idx + 1}
            </span>
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 5 -- Sentence Builder
function ExerciseSentenceBuilder({ exercise, onAnswer, disabled }: ExerciseProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const available = (exercise.scrambled_words ?? []).filter(
    (_, i) => !selected.includes(String(i)),
  );

  const addWord = (word: string, idx: number) => {
    if (disabled) return;
    setSelected((prev) => [...prev, String(idx)]);
  };

  const removeWord = (selIdx: number) => {
    if (disabled) return;
    setSelected((prev) => prev.filter((_, i) => i !== selIdx));
  };

  const builtSentence = selected
    .map((idx) => (exercise.scrambled_words ?? [])[Number(idx)])
    .join(' ');

  const handleSubmit = () => {
    if (builtSentence.trim() && !disabled) {
      onAnswer(builtSentence.trim());
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Arrange the words to form a sentence</p>
      {exercise.sentence_ru && (
        <p className="text-base text-[#888888]">{exercise.sentence_ru}</p>
      )}

      {/* Built sentence area */}
      <div className="flex min-h-[52px] w-full max-w-lg flex-wrap items-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3">
        {selected.length === 0 && (
          <span className="text-sm text-[#666666]">Click words below to build the sentence...</span>
        )}
        {selected.map((idx, selIdx) => (
          <button
            key={selIdx}
            onClick={() => removeWord(selIdx)}
            className="rounded-sm border border-[#00ff88]/30 bg-[#00ff88]/10 px-2.5 py-1 text-sm text-[#00aa55] transition-colors hover:bg-[#00ff88]/20"
          >
            {(exercise.scrambled_words ?? [])[Number(idx)]}
          </button>
        ))}
      </div>

      {/* Available words */}
      <div className="flex flex-wrap justify-center gap-2">
        {(exercise.scrambled_words ?? []).map((word, idx) => {
          const isUsed = selected.includes(String(idx));
          return (
            <button
              key={idx}
              disabled={isUsed || disabled}
              onClick={() => addWord(word, idx)}
              className={cn(
                'rounded-sm border border-[#2a2a2a] px-3 py-1.5 text-sm transition-colors',
                isUsed
                  ? 'cursor-default border-transparent bg-transparent text-[#2a2a2a]'
                  : 'bg-[#1e1e1e] text-[#e0e0e0] hover:border-[#3a3a3a]',
              )}
            >
              {word}
            </button>
          );
        })}
      </div>

      <Button
        onClick={handleSubmit}
        disabled={disabled || selected.length === 0}
      >
        Check
      </Button>
    </div>
  );
}

// Type 6 -- Free Production
function ExerciseFreeProduction({ exercise, onAnswer, disabled }: ExerciseProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onAnswer(input.trim());
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Write a sentence using this word</p>
      <h2 className="font-mono text-4xl font-bold text-[#e0e0e0]">
        {exercise.english}
      </h2>
      {exercise.transcription && (
        <p className="font-mono text-base text-[#666666]">
          {exercise.transcription}
        </p>
      )}
      <p className="text-sm text-[#888888]">
        {exercise.translations.join(', ')}
      </p>
      <div className="mt-2 flex w-full max-w-lg gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Write a sentence..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Submit
        </Button>
      </div>
    </div>
  );
}

// Type 7 -- Listening
function ExerciseListening({ exercise, onAnswer, disabled }: ExerciseProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onAnswer(input.trim());
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Listen and type the word</p>
      {exercise.sentence_en && (
        <div className="max-w-lg rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-5 py-4">
          <p className="text-base text-[#e0e0e0]">{exercise.sentence_en}</p>
        </div>
      )}
      <p className="text-sm text-[#888888]">
        {exercise.hint}
      </p>
      <div className="mt-2 flex w-full max-w-md gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Type the word..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Check
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exercise renderer map
// ---------------------------------------------------------------------------

const EXERCISE_COMPONENTS: Record<number, React.FC<ExerciseProps>> = {
  1: ExerciseIntroduction,
  2: ExerciseRecognition,
  3: ExerciseRecall,
  4: ExerciseContext,
  5: ExerciseSentenceBuilder,
  6: ExerciseFreeProduction,
  7: ExerciseListening,
};

// ---------------------------------------------------------------------------
// Feedback overlay
// ---------------------------------------------------------------------------

function FeedbackOverlay({
  result,
  onContinue,
}: {
  result: AnswerResult;
  onContinue: () => void;
}) {
  useKeyboard(
    {
      onConfirm: onContinue,
    },
    true,
  );

  return (
    <div className="animate-fade-in mt-8 flex flex-col items-center gap-4">
      <div
        className={cn(
          'flex items-center gap-2 text-lg font-bold',
          result.correct ? 'text-[#00ff88]' : 'text-red-400',
        )}
      >
        {result.correct ? (
          <CheckCircle size={24} />
        ) : (
          <XCircle size={24} />
        )}
        {result.correct ? 'Correct!' : 'Incorrect'}
      </div>

      {!result.correct && (
        <p className="text-sm text-[#888888]">
          Correct answer:{' '}
          <span className="font-mono text-[#e0e0e0]">
            {result.correct_answer}
          </span>
        </p>
      )}

      {result.feedback && (
        <p className="max-w-md text-center text-sm text-[#666666]">
          {result.feedback}
        </p>
      )}

      {result.level_changed && (
        <Badge variant="success">Level up! Mastery: {result.mastery_level}</Badge>
      )}

      <Button onClick={onContinue} className="mt-2 gap-2">
        Continue <ArrowRight size={16} />
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Session summary overlay
// ---------------------------------------------------------------------------

function SessionSummaryOverlay({
  summary,
  onClose,
}: {
  summary: SessionSummary;
  onClose: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md animate-slide-up text-center">
        <h2 className="text-2xl font-bold text-[#e0e0e0]">Session Complete</h2>
        <p className="mt-1 text-sm text-[#888888]">Great work!</p>

        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Words</p>
            <p className="text-xl font-bold text-[#e0e0e0]">
              {summary.total_words}
            </p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Accuracy</p>
            <p className="text-xl font-bold text-[#e0e0e0]">
              {formatPercent(summary.accuracy / 100)}
            </p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Correct</p>
            <p className="text-xl font-bold text-[#00ff88]">
              {summary.correct}
            </p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Wrong</p>
            <p className="text-xl font-bold text-red-400">{summary.wrong}</p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">New Learned</p>
            <p className="text-xl font-bold text-[#00ff88]">
              {summary.new_words_learned}
            </p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Time</p>
            <p className="text-xl font-bold text-[#e0e0e0]">
              {formatDuration(summary.time_spent_seconds)}
            </p>
          </div>
        </div>

        {summary.level_ups > 0 && (
          <div className="mt-4">
            <Badge variant="success">
              {summary.level_ups} level-up{summary.level_ups > 1 ? 's' : ''}!
            </Badge>
          </div>
        )}

        <Button size="lg" onClick={onClose} className="mt-6 w-full">
          Back to Dashboard
        </Button>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Train page (full-screen, no sidebar)
// ---------------------------------------------------------------------------

export default function Train() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const store = useTrainingStore();
  const {
    sessionId,
    exercises,
    currentIndex,
    isActive,
    startSession,
    nextExercise,
    addAnswer,
    endSession: clearStore,
  } = store;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackResult, setFeedbackResult] = useState<AnswerResult | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const answerStartTime = useRef(Date.now());

  // -- Initialize session on mount -----------------------------------------
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        setLoading(true);
        const duration = Number(searchParams.get('duration')) || 15;
        const result = await createSession({ duration_minutes: duration });
        if (!cancelled) {
          startSession(result.session_id, result.exercises);
          setLoading(false);
          answerStartTime.current = Date.now();
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to start session');
          setLoading(false);
        }
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // -- Handle answer submission ---------------------------------------------
  const handleAnswer = useCallback(
    async (answer: string) => {
      if (!sessionId || submitting) return;

      const exercise = exercises[currentIndex];
      if (!exercise) return;

      const responseTime = Date.now() - answerStartTime.current;

      setSubmitting(true);
      try {
        const result = await submitAnswer(sessionId, {
          word_id: exercise.word_id,
          answer,
          response_time_ms: responseTime,
          exercise_type: exercise.exercise_type,
        });
        addAnswer(result);
        setFeedbackResult(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to submit answer');
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, currentIndex, exercises, submitting, addAnswer],
  );

  // -- Advance to next exercise or finish -----------------------------------
  const handleContinue = useCallback(async () => {
    setFeedbackResult(null);

    if (currentIndex >= exercises.length - 1) {
      // Session is done
      if (sessionId) {
        try {
          const result = await endSession(sessionId);
          setSummary(result);
        } catch {
          // If end fails, still show a basic summary
          const answers = useTrainingStore.getState().answers;
          const correct = answers.filter((a) => a.correct).length;
          setSummary({
            total_words: exercises.length,
            correct,
            wrong: exercises.length - correct,
            accuracy: exercises.length > 0 ? (correct / exercises.length) * 100 : 0,
            new_words_learned: 0,
            time_spent_seconds: 0,
            level_ups: 0,
          });
        }
      }
    } else {
      nextExercise();
      answerStartTime.current = Date.now();
    }
  }, [currentIndex, exercises.length, sessionId, nextExercise]);

  // -- Exit session handler -------------------------------------------------
  const handleExit = useCallback(() => {
    clearStore();
    navigate('/');
  }, [clearStore, navigate]);

  // -- Keyboard shortcut for escape -----------------------------------------
  useKeyboard(
    {
      onEscape: () => {
        if (!feedbackResult && !summary) handleExit();
      },
    },
    true,
  );

  // -- Session summary screen -----------------------------------------------
  if (summary) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] p-6">
        <SessionSummaryOverlay summary={summary} onClose={handleExit} />
      </div>
    );
  }

  // -- Loading state --------------------------------------------------------
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 size={32} className="animate-spin text-[#00ff88]" />
          <p className="text-sm text-[#888888]">Preparing exercises...</p>
        </div>
      </div>
    );
  }

  // -- Error state ----------------------------------------------------------
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Card className="max-w-sm text-center">
          <p className="text-red-400">{error}</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  // -- No exercises ---------------------------------------------------------
  if (!isActive || exercises.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Card className="max-w-sm text-center">
          <p className="text-[#888888]">No exercises available right now.</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  // -- Current exercise -----------------------------------------------------
  const currentExercise = exercises[currentIndex];
  const ExerciseComponent = EXERCISE_COMPONENTS[currentExercise.exercise_type];
  const progress = ((currentIndex + 1) / exercises.length) * 100;

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Top bar: progress + exit */}
      <div className="sticky top-0 z-10 border-b border-[#2a2a2a] bg-[#0a0a0a] px-6 py-4">
        <div className="mx-auto flex max-w-2xl items-center gap-4">
          {/* Progress bar */}
          <div className="flex-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#1e1e1e]">
              <div
                className="h-full rounded-full bg-[#00ff88] transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          {/* Counter */}
          <span className="shrink-0 font-mono text-sm text-[#888888]">
            {currentIndex + 1}/{exercises.length}
          </span>
          {/* Exit button */}
          <button
            onClick={handleExit}
            className="shrink-0 rounded-sm p-1.5 text-[#666666] transition-colors hover:bg-[#1e1e1e] hover:text-[#e0e0e0]"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Exercise area */}
      <div className="mx-auto max-w-2xl px-6 py-12">
        {ExerciseComponent ? (
          <ExerciseComponent
            exercise={currentExercise}
            onAnswer={handleAnswer}
            disabled={submitting || !!feedbackResult}
          />
        ) : (
          <Card className="text-center">
            <p className="text-[#888888]">
              Unknown exercise type: {currentExercise.exercise_type}
            </p>
            <Button
              onClick={() => handleAnswer('skip')}
              className="mt-4"
              variant="secondary"
            >
              Skip
            </Button>
          </Card>
        )}

        {/* Feedback overlay */}
        {feedbackResult && (
          <FeedbackOverlay
            result={feedbackResult}
            onContinue={handleContinue}
          />
        )}
      </div>
    </div>
  );
}
