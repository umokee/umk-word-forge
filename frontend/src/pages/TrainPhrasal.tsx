import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { X, CheckCircle, XCircle, ArrowRight, Loader2, Volume2 } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { createPhrasalSession, submitPhrasalAnswer, endSession } from '@/api/training';
import { useKeyboard } from '@/hooks/useKeyboard';
import { useTTS } from '@/hooks/useTTS';
import { cn, formatDuration, formatPercent } from '@/lib/utils';
import type {
  PhrasalVerbExercise,
  PhrasalVerbAnswerResult,
  SessionSummary,
} from '@/types';

// ---------------------------------------------------------------------------
// Exercise type components for Phrasal Verbs
// ---------------------------------------------------------------------------

interface ExerciseProps {
  exercise: PhrasalVerbExercise;
  onAnswer: (answer: string) => void;
  disabled: boolean;
}

// Type 1 -- Introduction
function PhrasalIntroduction({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Новый фразовый глагол</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-5xl font-bold text-[#00aaff]">
          {exercise.phrase}
        </h2>
        <button
          onClick={() => speak(exercise.phrase)}
          className="flex h-10 w-10 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00aaff]"
        >
          <Volume2 size={24} />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <Badge variant="accent">{exercise.base_verb}</Badge>
        <span className="text-[#666666]">+</span>
        <Badge variant="secondary">{exercise.particle}</Badge>
      </div>

      <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-2">
        <p className="text-sm text-[#888888]">
          {exercise.is_separable ? 'Separable' : 'Inseparable'}:{' '}
          <span className="text-[#e0e0e0]">
            {exercise.is_separable
              ? `${exercise.base_verb} it ${exercise.particle}`
              : `${exercise.phrase} it`}
          </span>
        </p>
      </div>

      <div className="space-y-1">
        {exercise.translations.map((t, i) => (
          <p key={i} className="text-lg text-[#e0e0e0]">
            {t}
          </p>
        ))}
      </div>

      {exercise.definitions.length > 0 && (
        <div className="w-full max-w-md space-y-2">
          {exercise.definitions.slice(0, 2).map((def, i) => (
            <div
              key={i}
              className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3"
            >
              <p className="text-sm text-[#e0e0e0]">{def.en}</p>
              <p className="mt-1 text-xs text-[#666666]">{def.ru}</p>
            </div>
          ))}
        </div>
      )}

      {exercise.sentence_en && (
        <div className="max-w-md rounded-sm border border-[#00aaff]/20 bg-[#00aaff]/5 px-4 py-3">
          <p className="text-sm text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-1 text-xs text-[#666666]">{exercise.sentence_ru}</p>
          )}
        </div>
      )}

      <Button size="lg" onClick={() => onAnswer('seen')} disabled={disabled} className="mt-4">
        Понял
      </Button>
    </div>
  );
}

// Type 2 -- Meaning Match
function PhrasalMeaningMatch({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();

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
      <p className="text-sm text-[#888888]">Выберите значение</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#00aaff]">
          {exercise.phrase}
        </h2>
        <button
          onClick={() => speak(exercise.phrase)}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00aaff]"
        >
          <Volume2 size={20} />
        </button>
      </div>
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-colors hover:border-[#00aaff] hover:bg-[#00aaff]/5',
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

// Type 3 -- Particle Fill
function PhrasalParticleFill({ exercise, onAnswer, disabled }: ExerciseProps) {
  useKeyboard(
    {
      onOption: (index: number) => {
        if (!disabled && exercise.particle_options && exercise.particle_options[index]) {
          onAnswer(exercise.particle_options[index]);
        }
      },
    },
    !disabled,
  );

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Выберите правильную частицу</p>
      <h2 className="font-mono text-3xl font-bold text-[#e0e0e0]">
        {exercise.base_verb}{' '}
        <span className="rounded-sm bg-[#2a2a2a] px-3 py-1 text-[#00aaff]">___</span>
      </h2>
      {exercise.hint && (
        <p className="max-w-md text-sm text-[#888888]">{exercise.hint}</p>
      )}
      <p className="text-sm text-[#666666]">
        Значение: {exercise.translations[0]}
      </p>
      <div className="mt-2 grid w-full max-w-md grid-cols-2 gap-3">
        {(exercise.particle_options ?? []).map((particle, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(particle)}
            className={cn(
              'flex items-center justify-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] transition-colors hover:border-[#00aaff] hover:bg-[#00aaff]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="font-mono text-xs text-[#888888]">{idx + 1}</span>
            <span className="font-bold">{particle}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 4 -- Context (choose phrasal verb)
function PhrasalContext({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-sm text-[#888888]">Выберите подходящий фразовый глагол</p>
      {exercise.sentence_en && (
        <div className="max-w-lg rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-5 py-4">
          <p className="text-base text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-1 text-xs text-[#666666]">{exercise.sentence_ru}</p>
          )}
        </div>
      )}
      <p className="text-lg text-[#888888]">{exercise.translations[0]}</p>
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-colors hover:border-[#00aaff] hover:bg-[#00aaff]/5',
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

// Type 5 -- Separability
function PhrasalSeparability({ exercise, onAnswer, disabled }: ExerciseProps) {
  useKeyboard(
    {
      onOption: (index: number) => {
        if (!disabled && exercise.separability_options && exercise.separability_options[index]) {
          onAnswer(exercise.separability_options[index]);
        }
      },
    },
    !disabled,
  );

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Выберите правильный порядок слов</p>
      <h2 className="font-mono text-3xl font-bold text-[#00aaff]">
        {exercise.phrase}
      </h2>
      <p className="text-sm text-[#666666]">
        {exercise.is_separable ? 'Этот глагол — separable' : 'Этот глагол — inseparable'}
      </p>
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-3">
        {(exercise.separability_options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-4 text-center text-base font-mono text-[#e0e0e0] transition-colors hover:border-[#00aaff] hover:bg-[#00aaff]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-[#2a2a2a] font-mono text-xs text-[#888888]">
              {idx + 1}
            </span>
            <span className="flex-1">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 6 -- Production
function PhrasalProduction({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();
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
      <p className="text-sm text-[#888888]">Напишите предложение с этим фразовым глаголом</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#00aaff]">
          {exercise.phrase}
        </h2>
        <button
          onClick={() => speak(exercise.phrase)}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00aaff]"
        >
          <Volume2 size={20} />
        </button>
      </div>
      <p className="text-sm text-[#888888]">{exercise.translations.join(', ')}</p>
      <div className="mt-2 flex w-full max-w-lg gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Ваше предложение..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00aaff]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Отправить
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exercise renderer map
// ---------------------------------------------------------------------------

const EXERCISE_COMPONENTS: Record<number, React.FC<ExerciseProps>> = {
  1: PhrasalIntroduction,
  2: PhrasalMeaningMatch,
  3: PhrasalParticleFill,
  4: PhrasalContext,
  5: PhrasalSeparability,
  6: PhrasalProduction,
};

// ---------------------------------------------------------------------------
// Feedback overlay
// ---------------------------------------------------------------------------

function FeedbackOverlay({
  result,
  onContinue,
}: {
  result: PhrasalVerbAnswerResult;
  onContinue: () => void;
}) {
  useKeyboard({ onConfirm: onContinue }, true);

  const feedbackMessage = result.correct
    ? 'Отлично'
    : result.rating >= 3
      ? 'Почти!'
      : 'Не совсем';

  return (
    <div className="animate-fade-in mt-8 flex flex-col items-center gap-4">
      <div
        className={cn(
          'flex items-center gap-2 text-lg font-bold',
          result.correct ? 'text-[#00aaff]' : 'text-[#f59e0b]',
        )}
      >
        {result.correct ? <CheckCircle size={24} /> : <XCircle size={24} />}
        {feedbackMessage}
      </div>

      {!result.correct && (
        <p className="text-sm text-[#888888]">
          Правильный ответ:{' '}
          <span className="font-mono text-[#e0e0e0]">{result.correct_answer}</span>
        </p>
      )}

      {result.level_changed && (
        <Badge variant="success">Уровень +1! Mastery: {result.mastery_level}</Badge>
      )}

      <Button onClick={onContinue} className="mt-2 gap-2">
        Далее <ArrowRight size={16} />
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
        <h2 className="text-2xl font-bold text-[#e0e0e0]">Сессия завершена</h2>
        <p className="mt-1 text-sm text-[#888888]">Фразовые глаголы</p>

        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Фраз</p>
            <p className="text-xl font-bold text-[#e0e0e0]">{summary.total_words}</p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Точность</p>
            <p className="text-xl font-bold text-[#e0e0e0]">
              {formatPercent(summary.accuracy / 100)}
            </p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Правильно</p>
            <p className="text-xl font-bold text-[#00aaff]">{summary.correct}</p>
          </div>
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Ошибок</p>
            <p className="text-xl font-bold text-[#f59e0b]">{summary.wrong}</p>
          </div>
        </div>

        <Button size="lg" onClick={onClose} className="mt-6 w-full">
          На главную
        </Button>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Train Phrasal Verbs page
// ---------------------------------------------------------------------------

export default function TrainPhrasal() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [exercises, setExercises] = useState<PhrasalVerbExercise[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<PhrasalVerbAnswerResult[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackResult, setFeedbackResult] = useState<PhrasalVerbAnswerResult | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const answerStartTime = useRef(Date.now());

  // Initialize session
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        setLoading(true);
        const duration = Number(searchParams.get('duration')) || 15;
        const result = await createPhrasalSession({ duration_minutes: duration });
        if (!cancelled) {
          setSessionId(result.session_id);
          setExercises(result.exercises);
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
  }, []);

  // Handle answer submission
  const handleAnswer = useCallback(
    async (answer: string) => {
      if (!sessionId || submitting) return;

      const exercise = exercises[currentIndex];
      if (!exercise) return;

      const responseTime = Date.now() - answerStartTime.current;

      setSubmitting(true);
      try {
        const result = await submitPhrasalAnswer(sessionId, {
          phrasal_verb_id: exercise.phrasal_verb_id,
          answer,
          response_time_ms: responseTime,
          exercise_type: exercise.exercise_type,
        });
        setAnswers((prev) => [...prev, result]);

        // Auto-advance for introduction
        if (exercise.exercise_type === 1) {
          setSubmitting(false);
          setTimeout(() => {
            if (currentIndex >= exercises.length - 1) {
              endSession(sessionId).then(setSummary).catch(() => {
                const correct = answers.filter((a) => a.correct).length + (result.correct ? 1 : 0);
                setSummary({
                  total_words: exercises.length,
                  correct,
                  wrong: exercises.length - correct,
                  accuracy: exercises.length > 0 ? (correct / exercises.length) * 100 : 0,
                  new_words_learned: 0,
                  time_spent_seconds: 0,
                  level_ups: 0,
                });
              });
            } else {
              setCurrentIndex((i) => i + 1);
              answerStartTime.current = Date.now();
            }
          }, 300);
          return;
        }

        setFeedbackResult(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to submit answer');
      } finally {
        setSubmitting(false);
      }
    },
    [sessionId, currentIndex, exercises, submitting, answers],
  );

  // Advance to next exercise
  const handleContinue = useCallback(async () => {
    setFeedbackResult(null);

    if (currentIndex >= exercises.length - 1) {
      if (sessionId) {
        try {
          const result = await endSession(sessionId);
          setSummary(result);
        } catch {
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
      setCurrentIndex((i) => i + 1);
      answerStartTime.current = Date.now();
    }
  }, [currentIndex, exercises.length, sessionId, answers]);

  // Exit handler
  const handleExit = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // Keyboard shortcuts
  useKeyboard(
    {
      onEscape: () => {
        if (!feedbackResult && !summary) handleExit();
      },
    },
    true,
  );

  // Session summary screen
  if (summary) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] p-6">
        <SessionSummaryOverlay summary={summary} onClose={handleExit} />
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 size={32} className="animate-spin text-[#00aaff]" />
          <p className="text-sm text-[#888888]">Preparing phrasal verbs...</p>
        </div>
      </div>
    );
  }

  // Error state
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

  // No exercises
  if (exercises.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Card className="max-w-sm text-center">
          <p className="text-[#888888]">No phrasal verbs available right now.</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            Back to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  const currentExercise = exercises[currentIndex];
  const ExerciseComponent = EXERCISE_COMPONENTS[currentExercise.exercise_type];
  const progress = ((currentIndex + 1) / exercises.length) * 100;

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Top bar */}
      <div className="sticky top-0 z-10 border-b border-[#2a2a2a] bg-[#0a0a0a] px-6 py-4">
        <div className="mx-auto flex max-w-2xl items-center gap-4">
          <div className="flex-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#1e1e1e]">
              <div
                className="h-full rounded-full bg-[#00aaff] transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          <span className="shrink-0 font-mono text-sm text-[#888888]">
            {currentIndex + 1}/{exercises.length}
          </span>
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

        {feedbackResult && (
          <FeedbackOverlay result={feedbackResult} onContinue={handleContinue} />
        )}
      </div>
    </div>
  );
}
