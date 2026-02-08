import React, { useState, useEffect, useCallback, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/Card';
import type { ExerciseProps } from '@/types';

type FeedbackState = null | { index: number; correct: boolean };

export function ExerciseContext({ exercise, onAnswer }: ExerciseProps) {
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [correctIndex, setCorrectIndex] = useState<number | null>(null);
  const startTimeRef = useRef(Date.now());
  const answeredRef = useRef(false);

  const options = exercise.options ?? [];
  const correctAnswer = exercise.english;

  const sentenceWithBlank = exercise.sentence_en
    ? exercise.sentence_en.replace(
        new RegExp(exercise.english.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'),
        '_____'
      )
    : `Use the word "${exercise.english}" in context.`;

  useEffect(() => {
    startTimeRef.current = Date.now();
    answeredRef.current = false;
    setFeedback(null);
    setCorrectIndex(null);
  }, [exercise.word_id, exercise.exercise_type]);

  const handleSelect = useCallback(
    (option: string, index: number) => {
      if (answeredRef.current) return;
      answeredRef.current = true;

      const elapsed = Date.now() - startTimeRef.current;
      const isCorrect =
        option.toLowerCase().trim() === correctAnswer.toLowerCase().trim();

      setFeedback({ index, correct: isCorrect });

      if (!isCorrect) {
        const cIdx = options.findIndex(
          (o) => o.toLowerCase().trim() === correctAnswer.toLowerCase().trim()
        );
        setCorrectIndex(cIdx >= 0 ? cIdx : null);
      }

      const delay = isCorrect ? 500 : 1500;
      setTimeout(() => {
        onAnswer(option, elapsed);
      }, delay);
    },
    [correctAnswer, onAnswer, options]
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const num = parseInt(e.key, 10);
      if (num >= 1 && num <= 4 && num <= options.length) {
        handleSelect(options[num - 1], num - 1);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleSelect, options]);

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      <Card className="w-full flex flex-col items-center gap-4 py-8 px-6">
        <p className="text-lg text-[#e0e0e0] text-center leading-relaxed font-mono">
          {sentenceWithBlank}
        </p>
        {exercise.sentence_ru && (
          <p className="text-xs text-[#666666] text-center">
            {exercise.sentence_ru}
          </p>
        )}
      </Card>

      <div className="grid grid-cols-2 gap-3 w-full">
        {options.map((option, i) => {
          const isSelected = feedback?.index === i;
          const isCorrectOption = correctIndex === i;
          const showCorrect = isSelected && feedback?.correct;
          const showWrong = isSelected && !feedback?.correct;
          const showHighlight = isCorrectOption && feedback && !feedback.correct;

          return (
            <button
              key={i}
              onClick={() => handleSelect(option, i)}
              disabled={answeredRef.current}
              className={cn(
                'relative flex items-center gap-3 rounded-sm border bg-[#141414] px-4 py-3.5 text-left text-sm text-[#e0e0e0] transition-all duration-150',
                !feedback &&
                  'border-[#2a2a2a] hover:border-[#3a3a3a] hover:bg-[#1e1e1e] cursor-pointer',
                showCorrect && 'border-[#00ff88] bg-[#00ff88]/5',
                showWrong && 'border-red-500 bg-red-500/5 animate-shake',
                showHighlight && 'border-[#00ff88] bg-[#00ff88]/5',
                feedback && !isSelected && !isCorrectOption && 'opacity-40'
              )}
            >
              <span
                className={cn(
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-sm border text-xs font-mono',
                  showCorrect || showHighlight
                    ? 'border-[#00ff88] text-[#00ff88]'
                    : showWrong
                      ? 'border-red-500 text-red-400'
                      : 'border-[#2a2a2a] text-[#666666]'
                )}
              >
                {i + 1}
              </span>
              <span className="font-mono leading-snug">{option}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
