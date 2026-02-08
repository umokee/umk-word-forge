import React from 'react';
import { cn } from '@/lib/utils';

interface LevelDistributionProps {
  distribution: Record<number, number>;
  className?: string;
}

const levelNames: Record<number, string> = {
  1: 'Seen',
  2: 'Familiar',
  3: 'Recognized',
  4: 'Learned',
  5: 'Practiced',
  6: 'Mastered',
  7: 'Perfected',
};

const levelColors: Record<number, string> = {
  1: 'bg-[#0a3d2a]',
  2: 'bg-[#0d5c3d]',
  3: 'bg-[#108050]',
  4: 'bg-[#15a060]',
  5: 'bg-[#00aa55]',
  6: 'bg-[#00cc6a]',
  7: 'bg-[#00ff88]',
};

export function LevelDistribution({ distribution, className }: LevelDistributionProps) {
  const maxCount = Math.max(1, ...Object.values(distribution));

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {[1, 2, 3, 4, 5, 6, 7].map((level) => {
        const count = distribution[level] ?? 0;
        const widthPercent = (count / maxCount) * 100;

        return (
          <div key={level} className="flex items-center gap-3">
            <span className="w-20 text-xs text-[#888888] text-right shrink-0 font-mono">
              {levelNames[level]}
            </span>
            <div className="flex-1 bg-[#1e1e1e] rounded-sm h-5 relative overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-sm transition-all duration-500',
                  levelColors[level]
                )}
                style={{ width: `${widthPercent}%` }}
              />
            </div>
            <span className="w-10 text-xs text-[#e0e0e0] text-right shrink-0 font-mono">
              {count}
            </span>
          </div>
        );
      })}
    </div>
  );
}
