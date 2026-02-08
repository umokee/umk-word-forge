import React from 'react';
import { cn } from '@/lib/utils';

interface CoverageBarProps {
  knownWords: number;
  coveragePercent: number;
  className?: string;
}

const milestones = [50, 72, 80, 95];

export function CoverageBar({ knownWords, coveragePercent, className }: CoverageBarProps) {
  const clampedPercent = Math.min(100, Math.max(0, coveragePercent));

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="flex items-baseline justify-between">
        <p className="text-sm text-[#e0e0e0]">
          You know <span className="font-mono font-semibold text-[#00ff88]">{knownWords.toLocaleString()}</span> words
        </p>
        <p className="text-sm text-[#888888]">
          Cover <span className="font-mono font-semibold text-[#00ff88]">{clampedPercent}%</span> of speech
        </p>
      </div>

      <div className="relative">
        {/* Track */}
        <div className="bg-[#1e1e1e] rounded-sm h-4 w-full relative overflow-hidden">
          {/* Fill */}
          <div
            className="h-full rounded-sm bg-[#00ff88] transition-all duration-500"
            style={{ width: `${clampedPercent}%` }}
          />
        </div>

        {/* Percentage label */}
        <div
          className="absolute -top-6 text-xs font-mono font-semibold text-[#00ff88] transition-all duration-500"
          style={{ left: `${clampedPercent}%`, transform: 'translateX(-50%)' }}
        >
          {clampedPercent}%
        </div>

        {/* Milestone markers */}
        {milestones.map((m) => (
          <div
            key={m}
            className="absolute top-0 flex flex-col items-center"
            style={{ left: `${m}%`, transform: 'translateX(-50%)' }}
          >
            <div
              className={cn(
                'w-0.5 h-4',
                clampedPercent >= m ? 'bg-[#00aa55]/40' : 'bg-[#666666]/40'
              )}
            />
            <span
              className={cn(
                'mt-1 text-[10px] font-mono',
                clampedPercent >= m ? 'text-[#00ff88]' : 'text-[#666666]'
              )}
            >
              {m}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
