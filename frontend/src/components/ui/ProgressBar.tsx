import React from 'react';
import { cn } from '@/lib/utils';

type ProgressColor = 'accent' | 'success' | 'error';

interface ProgressBarProps {
  value: number;
  className?: string;
  color?: ProgressColor;
}

const colorStyles: Record<ProgressColor, string> = {
  accent: 'bg-indigo-500',
  success: 'bg-emerald-500',
  error: 'bg-red-500',
};

export function ProgressBar({
  value,
  className,
  color = 'accent',
}: ProgressBarProps) {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className={cn('bg-[#1C1C20] rounded-sm h-1.5 w-full', className)}>
      <div
        className={cn('h-full rounded-sm transition-all duration-300', colorStyles[color])}
        style={{ width: `${clampedValue}%` }}
      />
    </div>
  );
}
