import React from 'react';
import { cn } from '@/lib/utils';

type ProgressColor = 'accent' | 'success' | 'error';

interface ProgressBarProps {
  value: number;
  className?: string;
  color?: ProgressColor;
}

const colorStyles: Record<ProgressColor, string> = {
  accent: 'bg-[#00ff88]',
  success: 'bg-[#00ff88]',
  error: 'bg-[#ff4444]',
};

export function ProgressBar({
  value,
  className,
  color = 'accent',
}: ProgressBarProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className={cn('bg-[#1e1e1e] h-1.5 w-full', className)}>
      <div
        className={cn('h-full transition-all duration-300', colorStyles[color])}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
}
