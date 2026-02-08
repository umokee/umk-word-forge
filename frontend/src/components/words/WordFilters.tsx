import React from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

interface WordFiltersProps {
  onSearch: (query: string) => void;
  onLevelChange: (level: number | null) => void;
  onCefrChange: (cefr: string | null) => void;
  currentLevel: number | null;
  currentCefr: string | null;
  className?: string;
}

const levels = [0, 1, 2, 3, 4, 5, 6, 7];
const cefrLevels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export function WordFilters({
  onSearch,
  onLevelChange,
  onCefrChange,
  currentLevel,
  currentCefr,
  className,
}: WordFiltersProps) {
  const hasActiveFilters = currentLevel !== null || currentCefr !== null;

  return (
    <div className={cn('flex flex-col gap-4', className)}>
      {/* Search */}
      <Input
        placeholder="Search words..."
        onChange={(e) => onSearch(e.target.value)}
      />

      {/* Level filter */}
      <div className="flex flex-col gap-1.5">
        <span className="text-xs uppercase tracking-wider text-[#5C5C66] font-medium">
          Level
        </span>
        <div className="flex flex-wrap gap-1.5">
          {levels.map((level) => (
            <button
              key={level}
              onClick={() => onLevelChange(currentLevel === level ? null : level)}
              className={cn(
                'rounded-sm px-2.5 py-1 text-xs font-mono transition-colors',
                currentLevel === level
                  ? 'bg-indigo-600 text-white'
                  : 'bg-[#1C1C20] text-[#8B8B96] hover:bg-[#2A2A30]'
              )}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* CEFR filter */}
      <div className="flex flex-col gap-1.5">
        <span className="text-xs uppercase tracking-wider text-[#5C5C66] font-medium">
          CEFR
        </span>
        <div className="flex flex-wrap gap-1.5">
          {cefrLevels.map((cefr) => (
            <button
              key={cefr}
              onClick={() => onCefrChange(currentCefr === cefr ? null : cefr)}
              className={cn(
                'rounded-sm px-2.5 py-1 text-xs font-mono transition-colors',
                currentCefr === cefr
                  ? 'bg-indigo-600 text-white'
                  : 'bg-[#1C1C20] text-[#8B8B96] hover:bg-[#2A2A30]'
              )}
            >
              {cefr}
            </button>
          ))}
        </div>
      </div>

      {/* Clear filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            onLevelChange(null);
            onCefrChange(null);
          }}
        >
          Clear filters
        </Button>
      )}
    </div>
  );
}
