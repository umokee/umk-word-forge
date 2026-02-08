import React from 'react';
import { Volume2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTTS } from '@/hooks/useTTS';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { ExerciseProps } from '@/types';

export function ExerciseIntroduction({ exercise, onAnswer }: ExerciseProps) {
  const { speak } = useTTS();

  const handleSpeak = () => {
    speak(exercise.english);
  };

  const handleGotIt = () => {
    onAnswer('got_it', 0);
  };

  const highlightWord = (sentence: string, word: string): React.ReactNode => {
    const regex = new RegExp(`(${word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = sentence.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <span key={i} className="text-[#00ff88] font-semibold">
          {part}
        </span>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      <Card className="w-full flex flex-col items-center gap-5 py-8 px-6">
        {/* Word */}
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold font-mono text-[#e0e0e0]">
            {exercise.english}
          </h1>
          <button
            onClick={handleSpeak}
            className="flex h-9 w-9 items-center justify-center rounded-sm text-[#888888] transition-colors hover:bg-[#1e1e1e] hover:text-[#00ff88]"
            aria-label="Listen to pronunciation"
          >
            <Volume2 className="h-5 w-5" />
          </button>
        </div>

        {/* Transcription */}
        {exercise.transcription && (
          <span className="text-[#888888] font-mono text-sm">
            {exercise.transcription}
          </span>
        )}

        {/* Part of speech */}
        {exercise.part_of_speech && (
          <Badge variant="accent">{exercise.part_of_speech}</Badge>
        )}

        {/* Translations */}
        <div className="flex flex-wrap justify-center gap-2 mt-1">
          {exercise.translations.map((t, i) => (
            <span
              key={i}
              className={cn(
                'text-[#e0e0e0] text-base',
                i < exercise.translations.length - 1 && "after:content-[','] after:ml-0.5"
              )}
            >
              {t}
            </span>
          ))}
        </div>

        {/* Context sentences */}
        {exercise.sentence_en && (
          <div className="w-full border-t border-[#2a2a2a] pt-4 mt-2 flex flex-col gap-1.5">
            <p className="text-sm text-[#e0e0e0] leading-relaxed">
              {highlightWord(exercise.sentence_en, exercise.english)}
            </p>
            {exercise.sentence_ru && (
              <p className="text-xs text-[#666666] leading-relaxed">
                {exercise.sentence_ru}
              </p>
            )}
          </div>
        )}
      </Card>

      <Button size="lg" className="w-full max-w-xs" onClick={handleGotIt}>
        Got it
      </Button>
    </div>
  );
}
