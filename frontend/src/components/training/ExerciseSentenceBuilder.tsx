import React, { useState, useEffect, useRef } from 'react';
import { RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { ExerciseProps } from '@/types';

export function ExerciseSentenceBuilder({ exercise, onAnswer }: ExerciseProps) {
  const [available, setAvailable] = useState<string[]>([]);
  const [placed, setPlaced] = useState<string[]>([]);
  const [feedback, setFeedback] = useState<'correct' | 'wrong' | null>(null);
  const startTimeRef = useRef(Date.now());

  const scrambled = exercise.scrambled_words ?? [];
  const correctSentence = exercise.sentence_en ?? '';

  useEffect(() => {
    startTimeRef.current = Date.now();
    setAvailable([...scrambled]);
    setPlaced([]);
    setFeedback(null);
  }, [exercise.word_id, exercise.exercise_type]);

  const handleAddWord = (word: string, index: number) => {
    if (feedback) return;
    setPlaced((prev) => [...prev, word]);
    setAvailable((prev) => {
      const next = [...prev];
      next.splice(index, 1);
      return next;
    });
  };

  const handleRemoveWord = (word: string, index: number) => {
    if (feedback) return;
    setAvailable((prev) => [...prev, word]);
    setPlaced((prev) => {
      const next = [...prev];
      next.splice(index, 1);
      return next;
    });
  };

  const handleReset = () => {
    if (feedback) return;
    setAvailable([...scrambled]);
    setPlaced([]);
  };

  const handleCheck = () => {
    if (feedback || placed.length === 0) return;

    const elapsed = Date.now() - startTimeRef.current;
    const builtSentence = placed.join(' ');

    const normalize = (s: string) =>
      s
        .toLowerCase()
        .replace(/[.,!?;:'"]/g, '')
        .replace(/\s+/g, ' ')
        .trim();

    const isCorrect = normalize(builtSentence) === normalize(correctSentence);
    setFeedback(isCorrect ? 'correct' : 'wrong');

    const delay = isCorrect ? 800 : 1500;
    setTimeout(() => {
      onAnswer(builtSentence, elapsed);
    }, delay);
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      {/* Russian translation prompt */}
      {exercise.sentence_ru && (
        <Card className="w-full py-6 px-6">
          <p className="text-base text-[#E8E8EC] text-center leading-relaxed">
            {exercise.sentence_ru}
          </p>
        </Card>
      )}

      {/* Drop zone */}
      <div
        className={cn(
          'w-full min-h-[72px] rounded-sm border-2 border-dashed p-3 flex flex-wrap gap-2 transition-all duration-200',
          !feedback && 'border-[#2A2A30] bg-[#141416]',
          feedback === 'correct' && 'border-emerald-500/60 bg-emerald-500/5',
          feedback === 'wrong' && 'border-red-500/60 bg-red-500/5 animate-shake'
        )}
      >
        {placed.length === 0 && (
          <span className="text-sm text-[#5C5C66] m-auto">
            Click words below to build the sentence
          </span>
        )}
        {placed.map((word, i) => (
          <button
            key={`placed-${i}`}
            onClick={() => handleRemoveWord(word, i)}
            disabled={feedback !== null}
            className={cn(
              'rounded-sm border px-3 py-1.5 text-sm font-mono transition-all',
              feedback === 'correct'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                : feedback === 'wrong'
                  ? 'border-red-500/40 bg-red-500/10 text-red-300'
                  : 'border-indigo-500/40 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 cursor-pointer'
            )}
          >
            {word}
          </button>
        ))}
      </div>

      {/* Available word tiles */}
      <div className="w-full flex flex-wrap justify-center gap-2">
        {available.map((word, i) => (
          <button
            key={`avail-${i}`}
            onClick={() => handleAddWord(word, i)}
            disabled={feedback !== null}
            className="rounded-sm border border-[#2A2A30] bg-[#141416] px-3 py-1.5 text-sm font-mono text-[#E8E8EC] transition-all hover:border-[#3A3A42] hover:bg-[#1C1C20] cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {word}
          </button>
        ))}
      </div>

      {/* Feedback text */}
      {feedback === 'correct' && (
        <p className="text-sm text-emerald-400 animate-fade-in">Correct!</p>
      )}
      {feedback === 'wrong' && (
        <div className="flex flex-col items-center gap-1 animate-fade-in">
          <p className="text-sm text-red-400">Incorrect order</p>
          <p className="text-xs text-[#5C5C66]">
            Correct:{' '}
            <span className="font-mono text-emerald-400">{correctSentence}</span>
          </p>
        </div>
      )}

      {/* Action buttons */}
      {!feedback && (
        <div className="flex gap-3 w-full">
          <Button
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={handleReset}
            disabled={placed.length === 0}
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </Button>
          <Button
            size="md"
            className="flex-1"
            onClick={handleCheck}
            disabled={placed.length === 0}
          >
            Check
          </Button>
        </div>
      )}
    </div>
  );
}
