import React from 'react';
import { X } from 'lucide-react';
import { ProgressBar } from '@/components/ui/ProgressBar';

interface SessionProgressProps {
  current: number;
  total: number;
  onExit: () => void;
}

export function SessionProgress({ current, total, onExit }: SessionProgressProps) {
  const percent = total > 0 ? (current / total) * 100 : 0;

  return (
    <div className="flex items-center gap-4 w-full animate-fade-in">
      <div className="flex-1 flex flex-col gap-1.5">
        <ProgressBar value={percent} />
        <span className="text-xs font-mono text-[#8B8B96]">
          {current} / {total}
        </span>
      </div>

      <button
        onClick={onExit}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-[#2A2A30] bg-transparent text-[#8B8B96] transition-colors hover:border-[#3A3A42] hover:text-[#E8E8EC]"
        aria-label="Exit session"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
