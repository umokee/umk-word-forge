import { create } from 'zustand';
import type { Exercise, AnswerResult } from '../types';

interface TrainingState {
  sessionId: number | null;
  exercises: Exercise[];
  currentIndex: number;
  answers: AnswerResult[];
  isActive: boolean;

  startSession: (sessionId: number, exercises: Exercise[]) => void;
  nextExercise: () => void;
  addAnswer: (answer: AnswerResult) => void;
  endSession: () => void;
  getCurrentExercise: () => Exercise | null;
}

export const useTrainingStore = create<TrainingState>((set, get) => ({
  sessionId: null,
  exercises: [],
  currentIndex: 0,
  answers: [],
  isActive: false,

  startSession: (sessionId: number, exercises: Exercise[]) => {
    set({
      sessionId,
      exercises,
      currentIndex: 0,
      answers: [],
      isActive: true,
    });
  },

  nextExercise: () => {
    const { currentIndex, exercises } = get();
    if (currentIndex < exercises.length - 1) {
      set({ currentIndex: currentIndex + 1 });
    }
  },

  addAnswer: (answer: AnswerResult) => {
    set((state) => ({
      answers: [...state.answers, answer],
    }));
  },

  endSession: () => {
    set({
      sessionId: null,
      exercises: [],
      currentIndex: 0,
      answers: [],
      isActive: false,
    });
  },

  getCurrentExercise: () => {
    const { exercises, currentIndex, isActive } = get();
    if (!isActive || currentIndex >= exercises.length) return null;
    return exercises[currentIndex];
  },
}));
