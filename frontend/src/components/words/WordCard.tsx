import React from 'react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import type { Word } from '@/types';

interface WordCardProps {
  word: Word;
  className?: string;
}

export function WordCard({ word, className }: WordCardProps) {
  return (
    <Card className={cn('flex flex-col gap-5', className)}>
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-mono font-bold text-[#E8E8EC]">
          {word.english}
        </h2>
        <div className="flex items-center gap-3">
          {word.transcription && (
            <span className="text-sm font-mono text-[#8B8B96]">
              {word.transcription}
            </span>
          )}
          {word.part_of_speech && (
            <Badge variant="accent">{word.part_of_speech}</Badge>
          )}
        </div>
      </div>

      {/* Translations */}
      <div className="flex flex-col gap-1.5">
        <h3 className="text-xs uppercase tracking-wider text-[#5C5C66] font-medium">
          Translations
        </h3>
        <div className="flex flex-wrap gap-2">
          {word.translations.map((t, i) => (
            <span
              key={i}
              className="bg-[#1C1C20] rounded-sm px-3 py-1.5 text-sm text-[#E8E8EC]"
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Contexts */}
      {word.contexts.length > 0 && (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs uppercase tracking-wider text-[#5C5C66] font-medium">
            Contexts
          </h3>
          <div className="flex flex-col gap-3">
            {word.contexts.map((ctx) => (
              <div
                key={ctx.id}
                className="bg-[#1C1C20] rounded-sm p-3 flex flex-col gap-1 border-l-2 border-indigo-500/40"
              >
                <p className="text-sm text-[#E8E8EC]">{ctx.sentence_en}</p>
                {ctx.sentence_ru && (
                  <p className="text-sm text-[#8B8B96]">{ctx.sentence_ru}</p>
                )}
                {ctx.source && (
                  <p className="text-xs text-[#5C5C66] mt-1">{ctx.source}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
