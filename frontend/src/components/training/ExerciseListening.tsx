import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, RotateCcw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTTS } from '@/hooks/useTTS';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { ExerciseProps } from '@/types';

type FeedbackState = null | 'correct' | 'wrong';

export function ExerciseListening({ exercise, onAnswer }: ExerciseProps) {
  const { speak } = useTTS();
  const [input, setInput] = useState('');
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [hasPlayed, setHasPlayed] = useState(false);
  const startTimeRef = useRef(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  const textToSpeak = exercise.sentence_en ?? exercise.english;
  const correctAnswer = exercise.english;

  useEffect(() => {
    startTimeRef.current = Date.now();
    setInput('');
    setFeedback(null);
    setHasPlayed(false);
  }, [exercise.word_id, exercise.exercise_type]);

  const handlePlay = useCallback(() => {
    speak(textToSpeak, 0.85);
    setHasPlayed(true);
    setTimeout(() => inputRef.current?.focus(), 300);
  }, [speak, textToSpeak]);

  const handleRepeat = () => {
    speak(textToSpeak, 0.75);
  };

  const checkAnswer = useCallback(
    (value: string) => {
      if (feedback) return;

      const trimmed = value.trim().toLowerCase();
      const correct = correctAnswer.toLowerCase();
      const isCorrect = trimmed === correct;

      const elapsed = Date.now() - startTimeRef.current;
      setFeedback(isCorrect ? 'correct' : 'wrong');

      const delay = isCorrect ? 800 : 1800;
      setTimeout(() => {
        onAnswer(value.trim(), elapsed);
      }, delay);
    },
    [correctAnswer, feedback, onAnswer]
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      checkAnswer(input);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      {/* Play button area */}
      <Card className="w-full flex flex-col items-center gap-5 py-10 px-6">
        <button
          onClick={handlePlay}
          className="flex h-20 w-20 items-center justify-center rounded-full border-2 border-[#00ff88]/40 bg-[#00ff88]/10 text-[#00ff88] transition-all hover:border-[#00ff88]/60 hover:bg-[#00ff88]/20 hover:scale-105 active:scale-95"
          aria-label="Play audio"
        >
          <Play className="h-8 w-8 ml-1" />
        </button>

        <p className="text-sm text-[#888888]">
          {hasPlayed ? 'Listen and type the word you heard' : 'Press play to listen'}
        </p>

        {hasPlayed && (
          <button
            onClick={handleRepeat}
            className="flex items-center gap-1.5 text-xs text-[#666666] hover:text-[#888888] transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Repeat
          </button>
        )}
      </Card>

      {/* Input */}
      {hasPlayed && (
        <div className="w-full flex flex-col gap-3 animate-slide-up">
          <input
            ref={inputRef}
            type="text"
            placeholder="Type the word you heard..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={feedback !== null}
            autoComplete="off"
            autoCapitalize="off"
            spellCheck={false}
            className={cn(
              'w-full bg-[#1e1e1e] border rounded-sm px-4 py-3 text-sm font-mono text-[#e0e0e0] placeholder:text-[#666666] outline-none transition-all',
              !feedback && 'border-[#2a2a2a] focus:border-[#00ff88]',
              feedback === 'correct' && 'border-[#00ff88] bg-[#00ff88]/5',
              feedback === 'wrong' && 'border-red-500 bg-red-500/5'
            )}
          />

          {/* Feedback */}
          {feedback === 'correct' && (
            <p className="text-sm text-[#00ff88] text-center animate-fade-in">
              Correct!
            </p>
          )}
          {feedback === 'wrong' && (
            <div className="flex flex-col items-center gap-1 animate-fade-in">
              <p className="text-sm text-red-400">Incorrect</p>
              <p className="text-xs text-[#666666]">
                Correct answer:{' '}
                <span className="font-mono text-[#00ff88]">{correctAnswer}</span>
              </p>
            </div>
          )}

          {/* Submit button */}
          {!feedback && (
            <Button
              size="md"
              className="w-full"
              onClick={() => checkAnswer(input)}
              disabled={!input.trim()}
            >
              Submit
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
