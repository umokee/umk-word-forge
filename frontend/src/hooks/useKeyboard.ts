import { useEffect, useCallback } from 'react';

export interface KeyboardActions {
  onOption?: (index: number) => void;
  onConfirm?: () => void;
  onEscape?: () => void;
}

export function useKeyboard(
  actions: KeyboardActions,
  enabled: boolean = true,
) {
  const handler = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Ignore events when typing in an input or textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Still allow Escape and Enter from inputs
        if (event.key === 'Escape' && actions.onEscape) {
          event.preventDefault();
          actions.onEscape();
          return;
        }
        if (event.key === 'Enter' && actions.onConfirm) {
          event.preventDefault();
          actions.onConfirm();
          return;
        }
        return;
      }

      switch (event.key) {
        case '1':
        case '2':
        case '3':
        case '4': {
          const index = parseInt(event.key, 10) - 1;
          if (actions.onOption) {
            event.preventDefault();
            actions.onOption(index);
          }
          break;
        }
        case 'Enter': {
          if (actions.onConfirm) {
            event.preventDefault();
            actions.onConfirm();
          }
          break;
        }
        case 'Escape': {
          if (actions.onEscape) {
            event.preventDefault();
            actions.onEscape();
          }
          break;
        }
      }
    },
    [actions, enabled],
  );

  useEffect(() => {
    if (!enabled) return;
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handler, enabled]);
}
