import { useCallback } from 'react';

interface UseTTSReturn {
  speak: (text: string, rate?: number) => void;
  stop: () => void;
}

export function useTTS(): UseTTSReturn {
  const speak = useCallback((text: string, rate?: number) => {
    if (typeof speechSynthesis === 'undefined') return;

    // Cancel any ongoing speech before starting new
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = rate || 1.0;
    speechSynthesis.speak(utterance);
  }, []);

  const stop = useCallback(() => {
    if (typeof speechSynthesis === 'undefined') return;
    speechSynthesis.cancel();
  }, []);

  return { speak, stop };
}
