import { useState, useRef, useCallback, useEffect } from 'react';

interface UseTimerReturn {
  elapsed: number;
  isRunning: boolean;
  start: () => void;
  stop: () => void;
  reset: () => void;
}

export function useTimer(autoStart: boolean = true): UseTimerReturn {
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const startTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const accumulatedRef = useRef(0);

  const tick = useCallback(() => {
    if (startTimeRef.current !== null) {
      const now = performance.now();
      setElapsed(accumulatedRef.current + (now - startTimeRef.current));
    }
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const start = useCallback(() => {
    if (startTimeRef.current !== null) return; // already running
    startTimeRef.current = performance.now();
    setIsRunning(true);
    rafRef.current = requestAnimationFrame(tick);
  }, [tick]);

  const stop = useCallback(() => {
    if (startTimeRef.current !== null) {
      accumulatedRef.current += performance.now() - startTimeRef.current;
      startTimeRef.current = null;
    }
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    setIsRunning(false);
    setElapsed(accumulatedRef.current);
  }, []);

  const reset = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    startTimeRef.current = null;
    accumulatedRef.current = 0;
    setElapsed(0);
    setIsRunning(false);
  }, []);

  useEffect(() => {
    if (autoStart) {
      start();
    }
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [autoStart, start]);

  return { elapsed, isRunning, start, stop, reset };
}
