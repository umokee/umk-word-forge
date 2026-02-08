import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { X, CheckCircle, XCircle, ArrowRight, Loader2, Volume2 } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { createIrregularSession, submitIrregularAnswer, endSession } from '@/api/training';
import { useKeyboard } from '@/hooks/useKeyboard';
import { useTTS } from '@/hooks/useTTS';
import { cn, formatDuration, formatPercent } from '@/lib/utils';
import type {
  IrregularVerbExercise,
  IrregularVerbAnswerResult,
  SessionSummary,
} from '@/types';

// ---------------------------------------------------------------------------
// Exercise type components for Irregular Verbs
// ---------------------------------------------------------------------------

interface ExerciseProps {
  exercise: IrregularVerbExercise;
  onAnswer: (answer: string) => void;
  disabled: boolean;
}

// Type 1 -- Introduction
function IrregularIntroduction({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();

  const speakAll = () => {
    speak(`${exercise.base_form}, ${exercise.past_simple}, ${exercise.past_participle}`);
  };

  const patternLabels: Record<string, string> = {
    ABC: 'Все разные',
    ABB: 'Past = Participle',
    AAA: 'Все одинаковые',
    ABA: 'Base = Participle',
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Новый неправильный глагол</p>

      <div className="flex items-center gap-3">
        <button
          onClick={speakAll}
          className="flex h-12 w-12 items-center justify-center rounded-full bg-[#1e1e1e] text-[#ff6b6b] transition-colors hover:bg-[#2a2a2a]"
        >
          <Volume2 size={24} />
        </button>
      </div>

      {/* Three forms display */}
      <div className="flex items-center gap-4 font-mono text-3xl">
        <div className="flex flex-col items-center">
          <button
            onClick={() => speak(exercise.base_form)}
            className="font-bold text-[#ff6b6b] hover:text-[#ff8888]"
          >
            {exercise.base_form}
          </button>
          <span className="mt-1 text-xs text-[#666666]">Base</span>
          {exercise.transcription_base && (
            <span className="text-xs text-[#555555]">{exercise.transcription_base}</span>
          )}
        </div>
        <span className="text-[#3a3a3a]">→</span>
        <div className="flex flex-col items-center">
          <button
            onClick={() => speak(exercise.past_simple)}
            className="font-bold text-[#e0e0e0] hover:text-white"
          >
            {exercise.past_simple}
          </button>
          <span className="mt-1 text-xs text-[#666666]">Past</span>
          {exercise.transcription_past && (
            <span className="text-xs text-[#555555]">{exercise.transcription_past}</span>
          )}
        </div>
        <span className="text-[#3a3a3a]">→</span>
        <div className="flex flex-col items-center">
          <button
            onClick={() => speak(exercise.past_participle)}
            className="font-bold text-[#e0e0e0] hover:text-white"
          >
            {exercise.past_participle}
          </button>
          <span className="mt-1 text-xs text-[#666666]">Participle</span>
          {exercise.transcription_participle && (
            <span className="text-xs text-[#555555]">{exercise.transcription_participle}</span>
          )}
        </div>
      </div>

      {/* Pattern badge */}
      <Badge
        variant="secondary"
        className="border-[#ff6b6b]/30 bg-[#ff6b6b]/10 text-[#ff6b6b]"
      >
        Pattern: {exercise.verb_pattern} — {patternLabels[exercise.verb_pattern] || exercise.verb_pattern}
      </Badge>

      {/* Translations */}
      <div className="space-y-1">
        {exercise.translations.map((t, i) => (
          <p key={i} className="text-lg text-[#e0e0e0]">
            {t}
          </p>
        ))}
      </div>

      {/* Context sentence */}
      {exercise.sentence_en && (
        <div className="max-w-md rounded-sm border border-[#ff6b6b]/20 bg-[#ff6b6b]/5 px-4 py-3">
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

// Type 2 -- Form Recognition (multiple choice)
function IrregularFormRecognition({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();

  const formLabel = exercise.target_form === 'past' ? 'Past Simple' : 'Past Participle';

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
      <p className="text-sm text-[#888888]">Выберите {formLabel}</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#ff6b6b]">
          {exercise.given_form || exercise.base_form}
        </h2>
        <button
          onClick={() => speak(exercise.given_form || exercise.base_form)}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#ff6b6b]"
        >
          <Volume2 size={20} />
        </button>
      </div>
      <p className="text-sm text-[#666666]">{exercise.translations[0]}</p>
      <div className="mt-2 grid w-full max-w-md grid-cols-2 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center justify-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-4 font-mono text-base text-[#e0e0e0] transition-colors hover:border-[#ff6b6b] hover:bg-[#ff6b6b]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="text-xs text-[#888888]">{idx + 1}</span>
            <span className="font-bold">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 3 -- Type Form
function IrregularTypeForm({ exercise, onAnswer, disabled }: ExerciseProps) {
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

  const formLabel = exercise.target_form === 'past' ? 'Past Simple' : 'Past Participle';

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Напишите {formLabel}</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#ff6b6b]">
          {exercise.given_form || exercise.base_form}
        </h2>
        <button
          onClick={() => speak(exercise.given_form || exercise.base_form)}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#ff6b6b]"
        >
          <Volume2 size={20} />
        </button>
      </div>
      <p className="text-sm text-[#666666]">{exercise.translations[0]}</p>
      {exercise.hint && <p className="text-sm text-[#888888]">{exercise.hint}</p>}
      <div className="mt-2 flex w-full max-w-md gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Ваш ответ..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 font-mono text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#ff6b6b]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Проверить
        </Button>
      </div>
    </div>
  );
}

// Type 4 -- Sentence Fill
function IrregularSentenceFill({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-sm text-[#888888]">Заполните пропуск</p>
      {exercise.sentence_en && (
        <div className="max-w-lg rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-5 py-4">
          <p className="text-lg text-[#e0e0e0]">{exercise.sentence_en}</p>
        </div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-sm text-[#666666]">Base form:</span>
        <span className="font-mono font-bold text-[#ff6b6b]">
          {exercise.given_form || exercise.base_form}
        </span>
      </div>
      <div className="mt-2 flex w-full max-w-md gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Ваш ответ..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 font-mono text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#ff6b6b]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Проверить
        </Button>
      </div>
    </div>
  );
}

// Type 5 -- Reverse (given past/participle, find base)
function IrregularReverse({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-sm text-[#888888]">Какой это глагол? (Base form)</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#e0e0e0]">
          {exercise.given_form}
        </h2>
        <button
          onClick={() => speak(exercise.given_form || '')}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#ff6b6b]"
        >
          <Volume2 size={20} />
        </button>
      </div>
      <div className="mt-2 grid w-full max-w-md grid-cols-2 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center justify-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-4 font-mono text-base text-[#e0e0e0] transition-colors hover:border-[#ff6b6b] hover:bg-[#ff6b6b]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="text-xs text-[#888888]">{idx + 1}</span>
            <span className="font-bold">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// Type 6 -- Pattern Recognition
function IrregularPattern({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-sm text-[#888888]">Найдите глагол с таким же паттерном</p>
      <div className="rounded-sm border border-[#ff6b6b]/30 bg-[#ff6b6b]/10 px-6 py-3">
        <p className="font-mono text-xl font-bold text-[#ff6b6b]">
          {exercise.base_form} — {exercise.past_simple} — {exercise.past_participle}
        </p>
        <p className="mt-1 text-xs text-[#888888]">Pattern: {exercise.verb_pattern}</p>
      </div>
      {exercise.hint && <p className="text-sm text-[#888888]">{exercise.hint}</p>}
      <div className="mt-2 grid w-full max-w-md grid-cols-2 gap-3">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center justify-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-4 font-mono text-base text-[#e0e0e0] transition-colors hover:border-[#ff6b6b] hover:bg-[#ff6b6b]/5',
              disabled && 'pointer-events-none opacity-50',
            )}
          >
            <span className="text-xs text-[#888888]">{idx + 1}</span>
            <span className="font-bold">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exercise renderer map
// ---------------------------------------------------------------------------

const EXERCISE_COMPONENTS: Record<number, React.FC<ExerciseProps>> = {
  1: IrregularIntroduction,
  2: IrregularFormRecognition,
  3: IrregularTypeForm,
  4: IrregularSentenceFill,
  5: IrregularReverse,
  6: IrregularPattern,
};

// ---------------------------------------------------------------------------
// Feedback overlay
// ---------------------------------------------------------------------------

function FeedbackOverlay({
  result,
  onContinue,
}: {
  result: IrregularVerbAnswerResult;
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
          result.correct ? 'text-[#ff6b6b]' : 'text-[#f59e0b]',
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
        <p className="mt-1 text-sm text-[#888888]">Неправильные глаголы</p>

        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="rounded-sm bg-[#1e1e1e] px-3 py-3">
            <p className="text-xs text-[#888888]">Глаголов</p>
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
            <p className="text-xl font-bold text-[#ff6b6b]">{summary.correct}</p>
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
// Train Irregular Verbs page
// ---------------------------------------------------------------------------

export default function TrainIrregular() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [exercises, setExercises] = useState<IrregularVerbExercise[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<IrregularVerbAnswerResult[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackResult, setFeedbackResult] = useState<IrregularVerbAnswerResult | null>(null);
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
        const result = await createIrregularSession({ duration_minutes: duration });
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
        const result = await submitIrregularAnswer(sessionId, {
          irregular_verb_id: exercise.irregular_verb_id,
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
          <Loader2 size={32} className="animate-spin text-[#ff6b6b]" />
          <p className="text-sm text-[#888888]">Preparing irregular verbs...</p>
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
          <p className="text-[#888888]">No irregular verbs available right now.</p>
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
                className="h-full rounded-full bg-[#ff6b6b] transition-all duration-300"
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
