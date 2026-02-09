import { create } from 'zustand';
import type { Exercise, AnswerResult, ExercisePhase } from '../types';

interface PhaseProgress {
  phaseIndex: number;
  exerciseInPhase: number;
  totalInPhase: number;
  phaseName: string;
  phaseNameRu: string;
  phaseType: 'review' | 'new' | 'reinforcement';
}

interface ErrorTracker {
  wordId: number;
  exercise: Exercise;
}

interface TrainingState {
  sessionId: number | null;
  exercises: Exercise[];
  phases: ExercisePhase[];
  currentIndex: number;
  answers: AnswerResult[];
  isActive: boolean;

  // Error reinforcement
  errorWords: ErrorTracker[];
  reinforcementStarted: boolean;
  reinforcementIndex: number;

  startSession: (sessionId: number, exercises: Exercise[], phases?: ExercisePhase[]) => void;
  nextExercise: () => void;
  addAnswer: (answer: AnswerResult) => void;
  trackError: (exercise: Exercise) => void;
  startReinforcement: () => boolean; // returns true if there are errors to reinforce
  endSession: () => void;
  getCurrentExercise: () => Exercise | null;
  getPhaseProgress: () => PhaseProgress | null;
  isInReinforcement: () => boolean;
}

export const useTrainingStore = create<TrainingState>((set, get) => ({
  sessionId: null,
  exercises: [],
  phases: [],
  currentIndex: 0,
  answers: [],
  isActive: false,
  errorWords: [],
  reinforcementStarted: false,
  reinforcementIndex: 0,

  startSession: (sessionId: number, exercises: Exercise[], phases: ExercisePhase[] = []) => {
    set({
      sessionId,
      exercises,
      phases,
      currentIndex: 0,
      answers: [],
      isActive: true,
      errorWords: [],
      reinforcementStarted: false,
      reinforcementIndex: 0,
    });
  },

  nextExercise: () => {
    const { currentIndex, exercises, reinforcementStarted, reinforcementIndex, errorWords } = get();

    if (reinforcementStarted) {
      // In reinforcement mode
      if (reinforcementIndex < errorWords.length - 1) {
        set({ reinforcementIndex: reinforcementIndex + 1 });
      }
    } else {
      // Normal mode
      if (currentIndex < exercises.length - 1) {
        set({ currentIndex: currentIndex + 1 });
      }
    }
  },

  addAnswer: (answer: AnswerResult) => {
    set((state) => ({
      answers: [...state.answers, answer],
    }));
  },

  trackError: (exercise: Exercise) => {
    set((state) => {
      // Don't add duplicates (same word)
      if (state.errorWords.some(e => e.wordId === exercise.word_id)) {
        return state;
      }
      return {
        errorWords: [...state.errorWords, { wordId: exercise.word_id, exercise }],
      };
    });
  },

  startReinforcement: () => {
    const { errorWords } = get();
    if (errorWords.length === 0) {
      return false;
    }
    set({
      reinforcementStarted: true,
      reinforcementIndex: 0,
    });
    return true;
  },

  endSession: () => {
    set({
      sessionId: null,
      exercises: [],
      phases: [],
      currentIndex: 0,
      answers: [],
      isActive: false,
      errorWords: [],
      reinforcementStarted: false,
      reinforcementIndex: 0,
    });
  },

  getCurrentExercise: () => {
    const { exercises, currentIndex, isActive, reinforcementStarted, reinforcementIndex, errorWords } = get();
    if (!isActive) return null;

    if (reinforcementStarted) {
      // In reinforcement mode - return error word exercise
      if (reinforcementIndex >= errorWords.length) return null;
      const errorExercise = errorWords[reinforcementIndex].exercise;
      // Force exercise type to Recognition (2) for reinforcement
      return {
        ...errorExercise,
        exercise_type: 2,
      };
    }

    // Normal mode
    if (currentIndex >= exercises.length) return null;
    return exercises[currentIndex];
  },

  getPhaseProgress: () => {
    const { phases, currentIndex, isActive, reinforcementStarted, reinforcementIndex, errorWords } = get();
    if (!isActive) return null;

    // Reinforcement phase
    if (reinforcementStarted) {
      return {
        phaseIndex: phases.length, // After all normal phases
        exerciseInPhase: reinforcementIndex + 1,
        totalInPhase: errorWords.length,
        phaseName: 'Reinforcement',
        phaseNameRu: 'Повторение ошибок',
        phaseType: 'reinforcement' as const,
      };
    }

    // Normal phases
    if (phases.length === 0) return null;

    // Calculate which phase and position within it
    let exercisesSeen = 0;
    for (let i = 0; i < phases.length; i++) {
      const phase = phases[i];
      const phaseStart = exercisesSeen;
      const phaseEnd = exercisesSeen + phase.count;

      if (currentIndex >= phaseStart && currentIndex < phaseEnd) {
        return {
          phaseIndex: i,
          exerciseInPhase: currentIndex - phaseStart + 1,
          totalInPhase: phase.count,
          phaseName: phase.name,
          phaseNameRu: phase.name_ru,
          phaseType: phase.phase_type,
        };
      }
      exercisesSeen = phaseEnd;
    }

    // Fallback to last phase
    const lastPhase = phases[phases.length - 1];
    return {
      phaseIndex: phases.length - 1,
      exerciseInPhase: lastPhase.count,
      totalInPhase: lastPhase.count,
      phaseName: lastPhase.name,
      phaseNameRu: lastPhase.name_ru,
      phaseType: lastPhase.phase_type,
    };
  },

  isInReinforcement: () => {
    return get().reinforcementStarted;
  },
}));
