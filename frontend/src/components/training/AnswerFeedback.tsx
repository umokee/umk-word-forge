import React, { useEffect, useState } from 'react';
import { Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnswerFeedbackProps {
  correct: boolean;
  correctAnswer?: string;
  onDismiss: () => void;
  dismissDelay?: number;
}

export function AnswerFeedback({
  correct,
  correctAnswer,
  onDismiss,
  dismissDelay,
}: AnswerFeedbackProps) {
  const [visible, setVisible] = useState(true);

  const delay = dismissDelay ?? (correct ? 800 : 2000);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  useEffect(() => {
    if (!visible) {
      const exitTimer = setTimeout(onDismiss, 200);
      return () => clearTimeout(exitTimer);
    }
  }, [visible, onDismiss]);

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm transition-opacity duration-200',
        visible ? 'opacity-100' : 'opacity-0'
      )}
    >
      <div
        className={cn(
          'flex flex-col items-center gap-3 rounded-sm border px-10 py-8 bg-[#141414]',
          correct
            ? 'border-[#00ff88]/60 animate-fade-in'
            : 'border-red-500/60 animate-shake'
        )}
      >
        <div
          className={cn(
            'flex h-14 w-14 items-center justify-center rounded-full',
            correct ? 'bg-[#00ff88]/10' : 'bg-red-500/10'
          )}
        >
          {correct ? (
            <Check className="h-7 w-7 text-[#00ff88]" strokeWidth={3} />
          ) : (
            <X className="h-7 w-7 text-red-400" strokeWidth={3} />
          )}
        </div>

        <span
          className={cn(
            'text-lg font-bold',
            correct ? 'text-[#00ff88]' : 'text-red-400'
          )}
        >
          {correct ? 'Correct!' : 'Wrong'}
        </span>

        {!correct && correctAnswer && (
          <div className="flex flex-col items-center gap-1 mt-1">
            <span className="text-xs text-[#666666]">Correct answer:</span>
            <span className="text-sm font-mono font-medium text-[#00ff88]">
              {correctAnswer}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
