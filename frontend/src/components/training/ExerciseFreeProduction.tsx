import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiFetch } from '@/api/client';
import type { ExerciseProps, FreeProductionFeedback } from '@/types';

export function ExerciseFreeProduction({ exercise, onAnswer }: ExerciseProps) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [aiFeedback, setAiFeedback] = useState<FreeProductionFeedback | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const startTimeRef = useRef(Date.now());
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    startTimeRef.current = Date.now();
    setInput('');
    setLoading(false);
    setAiFeedback(null);
    setError(null);
    textareaRef.current?.focus();
  }, [exercise.word_id, exercise.exercise_type]);

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading || aiFeedback) return;

    const elapsed = Date.now() - startTimeRef.current;
    setLoading(true);
    setError(null);

    try {
      const result = await apiFetch<FreeProductionFeedback>(
        '/training/check-sentence',
        {
          method: 'POST',
          body: JSON.stringify({
            word: exercise.english,
            sentence: trimmed,
          }),
        }
      );
      setAiFeedback(result);

      setTimeout(() => {
        onAnswer(trimmed, elapsed);
      }, 3000);
    } catch {
      setError('Could not check your sentence. Submitting as-is.');
      setTimeout(() => {
        onAnswer(trimmed, elapsed);
      }, 1500);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full max-w-lg mx-auto animate-fade-in">
      {/* Word + translations */}
      <Card className="w-full flex flex-col items-center gap-3 py-6 px-6">
        <h2 className="text-2xl font-bold font-mono text-[#e0e0e0]">
          {exercise.english}
        </h2>
        <p className="text-sm text-[#888888]">
          {exercise.translations.join(', ')}
        </p>
      </Card>

      <p className="text-sm text-[#888888] text-center">
        Write your own sentence using this word:
      </p>

      {/* Textarea input */}
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={loading || aiFeedback !== null}
        placeholder="Type your sentence here..."
        rows={3}
        className={cn(
          'w-full bg-[#1e1e1e] border border-[#2a2a2a] rounded-sm px-4 py-3 text-sm font-mono text-[#e0e0e0] placeholder:text-[#666666] outline-none transition-all resize-none',
          'focus:border-[#00ff88]',
          loading && 'opacity-60',
          aiFeedback && 'border-[#2a2a2a]'
        )}
      />

      {/* Submit button / loading */}
      {!aiFeedback && !error && (
        <Button
          size="md"
          className="w-full gap-2"
          onClick={handleSubmit}
          disabled={!input.trim() || loading}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            'Check'
          )}
        </Button>
      )}

      {/* Error fallback */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-amber-400 animate-fade-in">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AI Feedback */}
      {aiFeedback && (
        <Card className="w-full flex flex-col gap-4 py-5 px-5 animate-slide-up">
          {/* Indicators */}
          <div className="flex flex-wrap gap-3">
            <FeedbackIndicator
              ok={aiFeedback.grammar_ok}
              label="Grammar"
            />
            <FeedbackIndicator
              ok={aiFeedback.word_usage_ok}
              label="Word usage"
            />
            <FeedbackIndicator
              ok={aiFeedback.natural}
              label="Natural"
            />
          </div>

          {/* Feedback text */}
          {aiFeedback.feedback_ru && (
            <p className="text-sm text-[#888888] leading-relaxed">
              {aiFeedback.feedback_ru}
            </p>
          )}

          {/* Corrected sentence */}
          {aiFeedback.corrected && (
            <div className="border-t border-[#2a2a2a] pt-3 flex flex-col gap-1">
              <span className="text-xs text-[#666666]">Suggested correction:</span>
              <p className="text-sm font-mono text-[#00ff88]">
                {aiFeedback.corrected}
              </p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function FeedbackIndicator({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge variant={ok ? 'success' : 'error'} className="gap-1.5">
      {ok ? (
        <CheckCircle className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      {label}
    </Badge>
  );
}
