import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Eye, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { ExerciseProps } from '@/types';

function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () =>
    Array(n + 1).fill(0)
  );

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }

  return dp[m][n];
}

type FeedbackState =
  | null
  | { type: 'correct' }
  | { type: 'typo'; corrected: string }
  | { type: 'wrong'; answer: string };

export function ExerciseRecall({ exercise, onAnswer }: ExerciseProps) {
  const [input, setInput] = useState('');
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [hintVisible, setHintVisible] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [hintTimerReady, setHintTimerReady] = useState(false);
  const startTimeRef = useRef(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  const correctAnswer = exercise.english;

  useEffect(() => {
    startTimeRef.current = Date.now();
    setInput('');
    setFeedback(null);
    setHintVisible(false);
    setShowAnswer(false);
    setHintTimerReady(false);
    inputRef.current?.focus();

    const timer = setTimeout(() => setHintTimerReady(true), 10000);
    return () => clearTimeout(timer);
  }, [exercise.word_id, exercise.exercise_type]);

  const generateHint = useCallback((): string => {
    if (exercise.hint) return exercise.hint;
    const word = correctAnswer;
    if (word.length <= 1) return word;
    return word[0] + '_'.repeat(word.length - 1);
  }, [exercise.hint, correctAnswer]);

  const checkAnswer = useCallback(
    (value: string) => {
      const trimmed = value.trim().toLowerCase();
      const correct = correctAnswer.toLowerCase();

      if (trimmed === correct) {
        return { type: 'correct' as const };
      }

      const dist = levenshtein(trimmed, correct);
      const threshold = correct.length <= 4 ? 1 : 2;
      if (dist <= threshold && trimmed.length > 0) {
        return { type: 'typo' as const, corrected: correctAnswer };
      }

      return { type: 'wrong' as const, answer: correctAnswer };
    },
    [correctAnswer]
  );

  const handleSubmit = useCallback(() => {
    if (!input.trim() || feedback) return;
    const elapsed = Date.now() - startTimeRef.current;
    const result = checkAnswer(input);
    setFeedback(result);

    const delay = result.type === 'correct' ? 600 : result.type === 'typo' ? 1200 : 1800;
    setTimeout(() => {
      onAnswer(input.trim(), elapsed);
    }, delay);
  }, [input, feedback, checkAnswer, onAnswer]);

  const handleShowAnswer = () => {
    if (feedback) return;
    setShowAnswer(true);
    setFeedback({ type: 'wrong', answer: correctAnswer });
    const elapsed = Date.now() - startTimeRef.current;
    setTimeout(() => {
      onAnswer('', elapsed);
    }, 1800);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      <Card className="w-full flex flex-col items-center gap-4 py-8 px-6">
        {/* Translation prompt */}
        <h2 className="text-2xl font-bold text-[#E8E8EC] text-center">
          {exercise.translations.join(', ')}
        </h2>

        {exercise.part_of_speech && (
          <Badge variant="accent">{exercise.part_of_speech}</Badge>
        )}

        {/* Hint */}
        {hintVisible && (
          <span className="font-mono text-sm text-[#8B8B96] animate-fade-in">
            Hint: {generateHint()}
          </span>
        )}
      </Card>

      {/* Input area */}
      <div className="w-full flex flex-col gap-3">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            placeholder="Type in English..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={feedback !== null}
            autoComplete="off"
            autoCapitalize="off"
            spellCheck={false}
            className={cn(
              'w-full bg-[#1C1C20] border rounded-sm px-4 py-3 text-sm font-mono text-[#E8E8EC] placeholder:text-[#5C5C66] outline-none transition-all',
              !feedback && 'border-[#2A2A30] focus:border-indigo-500',
              feedback?.type === 'correct' && 'border-emerald-500 bg-emerald-500/5',
              feedback?.type === 'typo' && 'border-amber-500 bg-amber-500/5',
              feedback?.type === 'wrong' && 'border-red-500 bg-red-500/5'
            )}
          />
        </div>

        {/* Feedback messages */}
        {feedback?.type === 'correct' && (
          <p className="text-sm text-emerald-400 text-center animate-fade-in">
            Correct!
          </p>
        )}
        {feedback?.type === 'typo' && (
          <p className="text-sm text-amber-400 text-center animate-fade-in">
            Close! Correct spelling:{' '}
            <span className="font-mono font-semibold">{feedback.corrected}</span>
          </p>
        )}
        {feedback?.type === 'wrong' && (
          <p className="text-sm text-red-400 text-center animate-fade-in">
            Correct answer:{' '}
            <span className="font-mono font-semibold text-emerald-400">
              {feedback.answer}
            </span>
          </p>
        )}

        {/* Action buttons */}
        {!feedback && (
          <div className="flex gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 gap-2"
              onClick={() => setHintVisible(true)}
              disabled={hintVisible}
            >
              <HelpCircle className="h-4 w-4" />
              {hintTimerReady ? 'Show hint' : 'Hint'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 gap-2"
              onClick={handleShowAnswer}
            >
              <Eye className="h-4 w-4" />
              Show answer
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
