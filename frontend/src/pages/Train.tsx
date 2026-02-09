import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { X, CheckCircle, XCircle, ArrowRight, Loader2, Volume2, BookOpen, Info } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useTrainingStore } from '@/stores/trainingStore';
import { createSession, submitAnswer, endSession } from '@/api/training';
import { useKeyboard } from '@/hooks/useKeyboard';
import { useTTS } from '@/hooks/useTTS';
import { cn, formatDuration, formatPercent } from '@/lib/utils';
import type { AnswerResult, Exercise, SessionSummary } from '@/types';

// ---------------------------------------------------------------------------
// Shared components
// ---------------------------------------------------------------------------

// Context display component - shows sentence examples when available
function ContextSentence({ exercise, showAlways = false }: { exercise: Exercise; showAlways?: boolean }) {
  if (!exercise.sentence_en && !showAlways) return null;

  return (
    <div className="mt-4 w-full max-w-lg">
      <div className="flex items-center gap-2 mb-2">
        <BookOpen size={14} className="text-[#666666]" />
        <span className="text-xs uppercase tracking-wide text-[#666666]">Пример</span>
      </div>
      {exercise.sentence_en ? (
        <div className="rounded-sm border border-[#2a2a2a] bg-[#141414] px-4 py-3">
          <p className="text-sm text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-1.5 text-xs text-[#666666]">{exercise.sentence_ru}</p>
          )}
        </div>
      ) : (
        <div className="rounded-sm border border-[#2a2a2a] bg-[#141414] px-4 py-3">
          <p className="text-xs text-[#666666] italic">Примеры будут добавлены</p>
        </div>
      )}
    </div>
  );
}

// Word header with audio button and optional transcription
function WordHeader({
  word,
  transcription,
  partOfSpeech,
  size = 'lg',
  onSpeak,
}: {
  word: string;
  transcription?: string | null;
  partOfSpeech?: string | null;
  size?: 'sm' | 'md' | 'lg';
  onSpeak: () => void;
}) {
  const sizeClasses = {
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-4xl',
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex items-center gap-3">
        <h2 className={cn('font-mono font-bold text-[#e0e0e0]', sizeClasses[size])}>
          {word}
        </h2>
        <button
          onClick={onSpeak}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#666666] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
          aria-label="Озвучить"
        >
          <Volume2 size={size === 'lg' ? 22 : 18} />
        </button>
      </div>
      {transcription && (
        <p className="font-mono text-sm text-[#666666]">{transcription}</p>
      )}
      {partOfSpeech && (
        <Badge variant="secondary" className="mt-1">{partOfSpeech}</Badge>
      )}
    </div>
  );
}

// Extra word info (collocations, phrasal verbs, usage notes)
function WordExtras({ exercise }: { exercise: Exercise }) {
  const hasCollocations = exercise.collocations && exercise.collocations.length > 0;
  const hasPhrasalVerbs = exercise.phrasal_verbs && exercise.phrasal_verbs.length > 0;
  const hasUsageNotes = exercise.usage_notes && exercise.usage_notes.length > 0;

  if (!hasCollocations && !hasPhrasalVerbs && !hasUsageNotes) return null;

  return (
    <div className="mt-4 w-full max-w-lg space-y-4">
      {/* Collocations */}
      {hasCollocations && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-[#666666]" />
            <span className="text-xs uppercase tracking-wide text-[#666666]">Словосочетания</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {exercise.collocations!.slice(0, 4).map((col, i) => (
              <span
                key={i}
                className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-2.5 py-1 text-xs"
              >
                <span className="text-[#e0e0e0]">{col.en}</span>
                <span className="mx-1 text-[#3a3a3a]">—</span>
                <span className="text-[#888888]">{col.ru}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Phrasal verbs */}
      {hasPhrasalVerbs && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-[#00ff88]" />
            <span className="text-xs uppercase tracking-wide text-[#666666]">Фразовые глаголы</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {exercise.phrasal_verbs!.slice(0, 3).map((pv, i) => (
              <span
                key={i}
                className="rounded-sm border border-[#00ff88]/20 bg-[#00ff88]/5 px-2.5 py-1 text-xs"
              >
                <span className="font-medium text-[#00ff88]">{pv.phrase}</span>
                <span className="mx-1 text-[#3a3a3a]">→</span>
                <span className="text-[#888888]">{pv.meaning_ru}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Usage notes */}
      {hasUsageNotes && (
        <div className="rounded-sm border border-[#2a2a2a]/50 bg-[#1a1a1a] px-3 py-2">
          <p className="text-xs text-[#888888]">
            {exercise.usage_notes!.slice(0, 2).join(' • ')}
          </p>
        </div>
      )}
    </div>
  );
}

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
  const { speak } = useTTS();

  // Helper to format verb forms
  const formatVerbForms = () => {
    if (!exercise.verb_forms) return null;
    const forms = exercise.verb_forms;
    const parts: string[] = [];
    if (forms.past) parts.push(forms.past);
    if (forms.past_participle) parts.push(forms.past_participle);
    if (forms.present_participle) parts.push(forms.present_participle);
    return parts.length > 0 ? parts.join(' / ') : null;
  };

  const verbFormsStr = formatVerbForms();

  // Check if this is a function word with rich contexts
  const isFunctionWord = exercise.is_function_word &&
    (exercise.usage_rules?.length || exercise.comparisons?.length || exercise.common_errors?.length);

  // Render function word introduction
  if (isFunctionWord) {
    return (
      <div className="flex flex-col items-center gap-6 text-center">
        <p className="text-sm text-[#888888]">Служебное слово</p>
        <div className="flex items-center gap-3">
          <h2 className="font-mono text-5xl font-bold text-[#e0e0e0]">
            {exercise.english}
          </h2>
          <button
            onClick={() => speak(exercise.english)}
            className="flex h-10 w-10 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
            aria-label="Озвучить"
          >
            <Volume2 size={24} />
          </button>
        </div>
        {exercise.transcription && (
          <p className="font-mono text-lg text-[#666666]">
            {exercise.transcription}
          </p>
        )}
        {exercise.part_of_speech && (
          <Badge variant="accent">{exercise.part_of_speech}</Badge>
        )}

        {/* Function word note */}
        <p className="text-sm text-[#f59e0b]">
          (нет прямого перевода на русский)
        </p>

        {/* Usage rules */}
        {exercise.usage_rules && exercise.usage_rules.length > 0 && (
          <div className="mt-2 w-full max-w-lg text-left">
            <p className="mb-3 text-sm font-medium text-[#888888]">Когда использовать:</p>
            <div className="space-y-3">
              {exercise.usage_rules.slice(0, 4).map((rule, i) => (
                <div key={i} className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3">
                  <p className="text-sm text-[#e0e0e0]">{rule.rule}</p>
                  {rule.example && (
                    <p className="mt-2 font-mono text-xs text-[#00ff88]">
                      {rule.example}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Comparisons */}
        {exercise.comparisons && exercise.comparisons.length > 0 && (
          <div className="mt-2 w-full max-w-lg text-left">
            <p className="mb-3 text-sm font-medium text-[#888888]">Сравнение:</p>
            <div className="space-y-2">
              {exercise.comparisons.slice(0, 3).map((comp, i) => (
                <div key={i} className="flex items-start gap-3 rounded-sm border border-[#00aaff]/20 bg-[#00aaff]/5 px-4 py-3">
                  <span className="shrink-0 font-mono text-sm font-medium text-[#00aaff]">
                    {exercise.english} vs {comp.vs}
                  </span>
                  <p className="text-sm text-[#e0e0e0]">{comp.difference}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Common errors */}
        {exercise.common_errors && exercise.common_errors.length > 0 && (
          <div className="mt-2 w-full max-w-lg text-left">
            <p className="mb-3 text-sm font-medium text-[#888888]">Частые ошибки:</p>
            <div className="space-y-2">
              {exercise.common_errors.slice(0, 3).map((err, i) => (
                <div key={i} className="rounded-sm border border-[#f59e0b]/20 bg-[#f59e0b]/5 px-4 py-3">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-[#f59e0b] line-through">{err.wrong}</span>
                    <span className="text-[#666666]">→</span>
                    <span className="text-[#00ff88]">{err.correct}</span>
                  </div>
                  {err.why && (
                    <p className="mt-1.5 text-xs text-[#888888]">{err.why}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Context sentence */}
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
          Понял
        </Button>
      </div>
    );
  }

  // Regular word introduction
  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Новое слово</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-5xl font-bold text-[#e0e0e0]">
          {exercise.english}
        </h2>
        <button
          onClick={() => speak(exercise.english)}
          className="flex h-10 w-10 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
          aria-label="Озвучить"
        >
          <Volume2 size={24} />
        </button>
      </div>
      {exercise.transcription && (
        <p className="font-mono text-lg text-[#666666]">
          {exercise.transcription}
        </p>
      )}
      {exercise.part_of_speech && (
        <Badge variant="accent">{exercise.part_of_speech}</Badge>
      )}

      {/* Verb forms (3 forms) */}
      {verbFormsStr && (
        <p className="font-mono text-sm text-[#00aa55]">
          {exercise.english} — {verbFormsStr}
        </p>
      )}

      <div className="space-y-1">
        {exercise.translations.map((t, i) => (
          <p key={i} className="text-lg text-[#e0e0e0]">
            {t}
          </p>
        ))}
      </div>

      {/* Context sentence */}
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

      {/* Collocations */}
      {exercise.collocations && exercise.collocations.length > 0 && (
        <div className="mt-2 w-full max-w-md">
          <p className="mb-2 text-xs text-[#666666]">Словосочетания:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {exercise.collocations.slice(0, 4).map((col, i) => (
              <span
                key={i}
                className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-2.5 py-1 text-xs"
              >
                <span className="text-[#e0e0e0]">{col.en}</span>
                <span className="mx-1 text-[#3a3a3a]">—</span>
                <span className="text-[#888888]">{col.ru}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Phrasal verbs */}
      {exercise.phrasal_verbs && exercise.phrasal_verbs.length > 0 && (
        <div className="mt-2 w-full max-w-md">
          <p className="mb-2 text-xs text-[#666666]">Фразовые глаголы:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {exercise.phrasal_verbs.slice(0, 3).map((pv, i) => (
              <span
                key={i}
                className="rounded-sm border border-[#00ff88]/20 bg-[#00ff88]/5 px-2.5 py-1 text-xs"
              >
                <span className="font-medium text-[#00ff88]">{pv.phrase}</span>
                <span className="mx-1 text-[#3a3a3a]">→</span>
                <span className="text-[#888888]">{pv.meaning_ru}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Usage notes */}
      {exercise.usage_notes && exercise.usage_notes.length > 0 && (
        <div className="mt-2 w-full max-w-md rounded-sm border border-[#2a2a2a]/50 bg-[#1a1a1a] px-3 py-2">
          <p className="text-xs text-[#666666]">
            {exercise.usage_notes.slice(0, 2).join(' • ')}
          </p>
        </div>
      )}

      <Button
        size="lg"
        onClick={() => onAnswer('seen')}
        disabled={disabled}
        className="mt-4"
      >
        Понял
      </Button>
    </div>
  );
}

// Type 2 -- Recognition (multiple choice)
function ExerciseRecognition({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();
  const prompt = exercise.reverse
    ? exercise.translations[0] ?? ''
    : exercise.english;
  const label = exercise.reverse
    ? 'Выберите английское слово'
    : 'Выберите перевод';

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
      <p className="text-xs uppercase tracking-wide text-[#666666]">{label}</p>

      {/* Word display */}
      {exercise.reverse ? (
        <h2 className="font-mono text-3xl font-bold text-[#e0e0e0]">{prompt}</h2>
      ) : (
        <WordHeader
          word={exercise.english}
          transcription={exercise.transcription}
          partOfSpeech={exercise.part_of_speech}
          size="md"
          onSpeak={() => speak(exercise.english)}
        />
      )}

      {/* Context sentence to help answer */}
      {exercise.sentence_en && !exercise.reverse && (
        <div className="max-w-md rounded-sm border border-[#2a2a2a]/50 bg-[#141414] px-4 py-2">
          <p className="text-xs text-[#888888]">{exercise.sentence_en}</p>
        </div>
      )}

      {/* Answer options */}
      <div className="mt-2 grid w-full max-w-md grid-cols-1 gap-2">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-all hover:border-[#00ff88] hover:bg-[#00ff88]/5',
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
      <p className="text-xs uppercase tracking-wide text-[#666666]">Напишите перевод</p>

      <WordHeader
        word={exercise.english}
        transcription={exercise.transcription}
        partOfSpeech={exercise.part_of_speech}
        size="md"
        onSpeak={() => speak(exercise.english)}
      />

      {/* Context sentence hint */}
      {exercise.sentence_en && (
        <div className="max-w-md rounded-sm border border-[#2a2a2a]/50 bg-[#141414] px-4 py-2">
          <p className="text-xs text-[#888888]">{exercise.sentence_en}</p>
        </div>
      )}

      {/* Answer input */}
      <div className="mt-2 flex w-full max-w-md gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={disabled}
          placeholder="Ваш ответ..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Ответ
        </Button>
      </div>
    </div>
  );
}

// Type 4 -- Context (gap fill with options)
function ExerciseContext({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-xs uppercase tracking-wide text-[#666666]">Перевод в контексте</p>

      {/* Context sentence - primary element */}
      {exercise.sentence_en ? (
        <div className="max-w-lg rounded-sm border border-[#00ff88]/20 bg-[#00ff88]/5 px-5 py-4">
          <p className="text-base text-[#e0e0e0]">{exercise.sentence_en}</p>
          {exercise.sentence_ru && (
            <p className="mt-2 text-xs text-[#888888]">{exercise.sentence_ru}</p>
          )}
        </div>
      ) : (
        <div className="max-w-lg rounded-sm border border-[#2a2a2a] bg-[#141414] px-5 py-4">
          <p className="text-xs text-[#666666] italic">Контекст недоступен</p>
        </div>
      )}

      {/* Target word */}
      <div className="flex items-center gap-2">
        <h2 className="font-mono text-2xl font-bold text-[#00ff88]">
          {exercise.english}
        </h2>
        <button
          onClick={() => speak(exercise.english)}
          className="flex h-8 w-8 items-center justify-center rounded-sm text-[#666666] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
        >
          <Volume2 size={16} />
        </button>
      </div>

      {/* Answer options */}
      <div className="grid w-full max-w-md grid-cols-1 gap-2">
        {(exercise.options ?? []).map((option, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onAnswer(option)}
            className={cn(
              'flex items-center gap-3 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-left text-sm text-[#e0e0e0] transition-all hover:border-[#00ff88] hover:bg-[#00ff88]/5',
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
      <p className="text-sm text-[#888888]">Составьте предложение из слов</p>
      {exercise.sentence_ru && (
        <p className="text-base text-[#888888]">{exercise.sentence_ru}</p>
      )}

      {/* Built sentence area */}
      <div className="flex min-h-[52px] w-full max-w-lg flex-wrap items-center gap-2 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3">
        {selected.length === 0 && (
          <span className="text-sm text-[#666666]">Нажимайте на слова ниже...</span>
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
        Проверить
      </Button>
    </div>
  );
}

// Type 6 -- Free Production
function ExerciseFreeProduction({ exercise, onAnswer, disabled }: ExerciseProps) {
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
      <p className="text-sm text-[#888888]">Напишите предложение с этим словом</p>
      <div className="flex items-center gap-3">
        <h2 className="font-mono text-4xl font-bold text-[#e0e0e0]">
          {exercise.english}
        </h2>
        <button
          onClick={() => speak(exercise.english)}
          className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
        >
          <Volume2 size={20} />
        </button>
      </div>
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
          placeholder="Ваше предложение..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Отправить
        </Button>
      </div>
    </div>
  );
}

// Type 7 -- Listening
function ExerciseListening({ exercise, onAnswer, disabled }: ExerciseProps) {
  const { speak } = useTTS();
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    // Auto-speak on mount
    speak(exercise.english);
  }, []);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onAnswer(input.trim());
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <p className="text-sm text-[#888888]">Прослушайте и напишите слово</p>
      <button
        onClick={() => speak(exercise.english)}
        className="flex h-16 w-16 items-center justify-center rounded-full bg-[#1e1e1e] text-[#00ff88] transition-colors hover:bg-[#2a2a2a]"
        aria-label="Озвучить"
      >
        <Volume2 size={32} />
      </button>
      {exercise.hint && (
        <p className="font-mono text-lg text-[#666666]">
          {exercise.hint}
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
          placeholder="Напишите слово..."
          className="flex-1 rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3 text-sm text-[#e0e0e0] outline-none placeholder:text-[#666666] focus:border-[#00ff88]"
        />
        <Button onClick={handleSubmit} disabled={disabled || !input.trim()}>
          Проверить
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

  // Neutral feedback per TRAINING-SPEC.md (no "Отлично!", "Супер!", "Молодец!")
  // Correct: green, Typo: yellow, Wrong: neutral gray (NOT red)
  const isTypo = !result.correct && result.rating >= 3;

  return (
    <div className="animate-fade-in mt-8 flex flex-col items-center gap-4">
      {/* Status indicator */}
      <div className={cn(
        'flex items-center gap-2 rounded-sm border px-4 py-2',
        result.correct
          ? 'border-[#00ff88]/20 bg-[#00ff88]/5 text-[#00ff88]'
          : isTypo
            ? 'border-[#f59e0b]/20 bg-[#f59e0b]/5 text-[#f59e0b]'
            : 'border-[#2a2a2a] bg-[#1e1e1e] text-[#888888]'
      )}>
        {result.correct || isTypo ? (
          <CheckCircle size={20} />
        ) : (
          <XCircle size={20} />
        )}
        <span className="text-sm font-medium uppercase tracking-wide">
          {result.correct ? 'Верно' : isTypo ? 'Опечатка' : 'Запомните'}
        </span>
      </div>

      {/* Correct answer display */}
      {!result.correct && (
        <div className="flex flex-col items-center gap-1">
          <p className="text-xs uppercase tracking-wide text-[#666666]">Правильный ответ</p>
          <p className="font-mono text-xl text-[#e0e0e0]">{result.correct_answer}</p>
        </div>
      )}

      {/* Level change indicator */}
      {result.level_changed && (
        <div className="rounded-sm border border-[#00ff88]/20 bg-[#00ff88]/5 px-3 py-1.5">
          <p className="text-xs text-[#00ff88]">
            Уровень владения: {result.mastery_level}
          </p>
        </div>
      )}

      {/* Continue button */}
      <Button onClick={onContinue} className="mt-2 gap-2">
        Далее <ArrowRight size={16} />
      </Button>
      <p className="text-xs text-[#666666]">или нажмите Enter</p>
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
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md animate-slide-up rounded-sm border border-[#2a2a2a] bg-[#141414]">
        {/* Header */}
        <div className="border-b border-[#2a2a2a] bg-[#1e1e1e] px-4 py-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-[#00ff88]">
            [СЕССИЯ ЗАВЕРШЕНА]
          </h2>
        </div>

        {/* Stats */}
        <div className="p-4 space-y-3">
          {/* Primary stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-3 py-3 text-center">
              <p className="text-xs uppercase tracking-wide text-[#666666]">Всего</p>
              <p className="font-mono text-2xl font-bold text-[#e0e0e0]">
                {summary.total_words}
              </p>
            </div>
            <div className="rounded-sm border border-[#00ff88]/20 bg-[#00ff88]/5 px-3 py-3 text-center">
              <p className="text-xs uppercase tracking-wide text-[#666666]">Верно</p>
              <p className="font-mono text-2xl font-bold text-[#00ff88]">
                {summary.correct}
              </p>
            </div>
            <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-3 py-3 text-center">
              <p className="text-xs uppercase tracking-wide text-[#666666]">Ошибок</p>
              <p className="font-mono text-2xl font-bold text-[#888888]">
                {summary.wrong}
              </p>
            </div>
          </div>

          {/* Accuracy bar */}
          <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] p-3">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="uppercase tracking-wide text-[#666666]">Точность</span>
              <span className="font-mono font-bold text-[#e0e0e0]">
                {formatPercent(summary.accuracy / 100)}
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-[#2a2a2a]">
              <div
                className="h-full rounded-full bg-[#00ff88] transition-all"
                style={{ width: `${Math.min(100, summary.accuracy)}%` }}
              />
            </div>
          </div>

          {/* Secondary stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wide text-[#666666]">Изучено</span>
                <span className="font-mono text-lg font-bold text-[#00ff88]">
                  {summary.new_words_learned}
                </span>
              </div>
            </div>
            <div className="rounded-sm border border-[#2a2a2a] bg-[#1e1e1e] px-3 py-2">
              <div className="flex items-center justify-between">
                <span className="text-xs uppercase tracking-wide text-[#666666]">Время</span>
                <span className="font-mono text-lg font-bold text-[#e0e0e0]">
                  {formatDuration(summary.time_spent_seconds)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Action */}
        <div className="border-t border-[#2a2a2a] p-4">
          <Button size="lg" onClick={onClose} className="w-full">
            На главную
          </Button>
        </div>
      </div>
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
    phases,
    currentIndex,
    isActive,
    startSession,
    nextExercise,
    addAnswer,
    trackError,
    startReinforcement,
    endSession: clearStore,
    getPhaseProgress,
    getCurrentExercise,
    isInReinforcement,
    errorWords,
    reinforcementIndex,
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
          startSession(result.session_id, result.exercises, result.phases || []);
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

      // Get current exercise (handles both normal and reinforcement mode)
      const exercise = getCurrentExercise();
      if (!exercise) return;

      const responseTime = Date.now() - answerStartTime.current;
      const inReinforcement = isInReinforcement();

      setSubmitting(true);
      try {
        // For reinforcement, we don't submit to backend - just show feedback locally
        if (inReinforcement) {
          // Simple check: compare answer to first translation
          const correctAnswer = exercise.translations[0] || '';
          const isCorrect = answer.toLowerCase().trim() === correctAnswer.toLowerCase().trim();

          const localResult: AnswerResult = {
            correct: isCorrect,
            rating: isCorrect ? 4 : 1,
            correct_answer: correctAnswer,
            feedback: isCorrect ? null : `Правильный ответ: ${correctAnswer}`,
            mastery_level: 1,
            level_changed: false,
          };

          setFeedbackResult(localResult);
          setSubmitting(false);
          return;
        }

        // Normal mode - submit to backend
        const result = await submitAnswer(sessionId, {
          word_id: exercise.word_id,
          answer,
          response_time_ms: responseTime,
          exercise_type: exercise.exercise_type,
        });
        addAnswer(result);

        // Track errors for reinforcement (not for Introduction)
        if (!result.correct && exercise.exercise_type !== 1) {
          trackError(exercise);
        }

        // Level 1 (Introduction) - auto-advance without feedback overlay
        if (exercise.exercise_type === 1) {
          setSubmitting(false);
          setTimeout(() => {
            if (currentIndex >= exercises.length - 1) {
              // Check for errors before ending
              if (startReinforcement()) {
                answerStartTime.current = Date.now();
              } else {
                endSession(sessionId).then(setSummary).catch(() => {
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
                });
              }
            } else {
              nextExercise();
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
    [sessionId, currentIndex, exercises, submitting, addAnswer, nextExercise, getCurrentExercise, isInReinforcement, trackError, startReinforcement],
  );

  // -- Advance to next exercise or finish -----------------------------------
  const handleContinue = useCallback(async () => {
    setFeedbackResult(null);
    const inReinforcement = isInReinforcement();

    if (inReinforcement) {
      // In reinforcement mode
      const errWords = useTrainingStore.getState().errorWords;
      const reinIdx = useTrainingStore.getState().reinforcementIndex;

      if (reinIdx >= errWords.length - 1) {
        // Reinforcement complete - end session
        if (sessionId) {
          try {
            const result = await endSession(sessionId);
            setSummary(result);
          } catch {
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
      return;
    }

    // Normal mode
    if (currentIndex >= exercises.length - 1) {
      // Main exercises done - check if we need reinforcement
      if (startReinforcement()) {
        // Start reinforcement phase
        answerStartTime.current = Date.now();
      } else {
        // No errors - end session
        if (sessionId) {
          try {
            const result = await endSession(sessionId);
            setSummary(result);
          } catch {
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
      }
    } else {
      nextExercise();
      answerStartTime.current = Date.now();
    }
  }, [currentIndex, exercises.length, sessionId, nextExercise, isInReinforcement, startReinforcement]);

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
          <p className="text-sm text-[#888888]">Загрузка упражнений...</p>
        </div>
      </div>
    );
  }

  // -- Error state (neutral gray, not red per TRAINING-SPEC.md) -------------
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Card className="max-w-sm text-center">
          <p className="text-[#888888]">{error}</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            На главную
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
          <p className="text-[#888888]">Нет доступных упражнений.</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            На главную
          </Button>
        </Card>
      </div>
    );
  }

  // -- Current exercise -----------------------------------------------------
  const currentExercise = getCurrentExercise();
  if (!currentExercise) {
    // Should not happen, but handle gracefully
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a]">
        <Card className="max-w-sm text-center">
          <p className="text-[#888888]">Нет доступных упражнений.</p>
          <Button variant="secondary" onClick={handleExit} className="mt-4">
            На главную
          </Button>
        </Card>
      </div>
    );
  }

  const ExerciseComponent = EXERCISE_COMPONENTS[currentExercise.exercise_type];
  const inReinforcement = isInReinforcement();
  const totalExercises = inReinforcement ? errorWords.length : exercises.length;
  const currentIdx = inReinforcement ? reinforcementIndex : currentIndex;
  const progress = ((currentIdx + 1) / totalExercises) * 100;
  const phaseProgress = getPhaseProgress();

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Top bar: progress + exit */}
      <div className="sticky top-0 z-10 border-b border-[#2a2a2a] bg-[#0a0a0a] px-6 py-4">
        <div className="mx-auto flex max-w-2xl flex-col gap-2">
          {/* Phase indicator */}
          {phaseProgress && (
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className={cn(
                  'rounded-sm px-2 py-0.5 font-medium',
                  phaseProgress.phaseType === 'reinforcement'
                    ? 'bg-[#f59e0b]/10 text-[#f59e0b]'
                    : phaseProgress.phaseType === 'review'
                      ? 'bg-[#00aaff]/10 text-[#00aaff]'
                      : 'bg-[#00ff88]/10 text-[#00ff88]'
                )}>
                  {phaseProgress.phaseType === 'reinforcement'
                    ? 'Закрепление'
                    : phaseProgress.phaseType === 'review'
                      ? 'Повторение'
                      : 'Новые'}
                </span>
                <span className="text-[#888888]">
                  {phaseProgress.phaseType === 'reinforcement'
                    ? phaseProgress.phaseNameRu
                    : `Фаза ${phaseProgress.phaseIndex + 1}/${phases.length}: ${phaseProgress.phaseNameRu}`}
                </span>
              </div>
              <span className="font-mono text-[#888888]">
                {phaseProgress.exerciseInPhase}/{phaseProgress.totalInPhase}
              </span>
            </div>
          )}

          {/* Progress bars */}
          <div className="flex items-center gap-4">
            {/* Phase progress bar */}
            {phaseProgress ? (
              <div className="flex-1">
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#1e1e1e]">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-300',
                      phaseProgress.phaseType === 'reinforcement'
                        ? 'bg-[#f59e0b]'
                        : phaseProgress.phaseType === 'review'
                          ? 'bg-[#00aaff]'
                          : 'bg-[#00ff88]'
                    )}
                    style={{ width: `${(phaseProgress.exerciseInPhase / phaseProgress.totalInPhase) * 100}%` }}
                  />
                </div>
              </div>
            ) : (
              <div className="flex-1">
                <div className="h-2 w-full overflow-hidden rounded-full bg-[#1e1e1e]">
                  <div
                    className="h-full rounded-full bg-[#00ff88] transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Overall counter */}
            <span className="shrink-0 font-mono text-sm text-[#666666]">
              {inReinforcement
                ? `+${reinforcementIndex + 1}/${errorWords.length}`
                : `${currentIndex + 1}/${exercises.length}`}
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
              Неизвестный тип упражнения: {currentExercise.exercise_type}
            </p>
            <Button
              onClick={() => handleAnswer('skip')}
              className="mt-4"
              variant="secondary"
            >
              Пропустить
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
