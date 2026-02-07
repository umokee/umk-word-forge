// ---------------------------------------------------------------------------
// Words
// ---------------------------------------------------------------------------

export interface WordContext {
  id: number;
  word_id: number;
  sentence_en: string;
  sentence_ru: string | null;
  source: string | null;
  difficulty: number;
}

export interface Word {
  id: number;
  english: string;
  transcription: string | null;
  part_of_speech: string | null;
  translations: string[];
  frequency_rank: number | null;
  cefr_level: string | null;
  contexts: WordContext[];
}

export interface WordListItem {
  id: number;
  english: string;
  transcription: string | null;
  part_of_speech: string | null;
  translations: string[];
  frequency_rank: number | null;
  cefr_level: string | null;
}

export interface PaginatedWords {
  items: WordListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface WordCreate {
  english: string;
  transcription?: string | null;
  part_of_speech?: string | null;
  translations?: string[];
  frequency_rank?: number | null;
  cefr_level?: string | null;
}

// ---------------------------------------------------------------------------
// Learning
// ---------------------------------------------------------------------------

export interface UserWord {
  id: number;
  word_id: number;
  mastery_level: number;
  consecutive_correct: number;
  consecutive_wrong: number;
  fsrs_stability: number;
  fsrs_difficulty: number;
  fsrs_state: number;
  fsrs_reps: number;
  fsrs_lapses: number;
  next_review_at: string | null;
  created_at: string | null;
}

export interface UserWordWithWord extends UserWord {
  english: string;
  transcription: string | null;
  translations: string[];
  part_of_speech: string | null;
}

export interface PaginatedUserWords {
  items: UserWord[];
  total: number;
  page: number;
  per_page: number;
}

export interface ReviewCreate {
  exercise_type: number;
  rating: number;
  response_time_ms: number;
  correct: boolean;
}

export interface MasteryResult {
  new_level: number;
  level_changed: boolean;
  next_review: string | null;
}

export interface LearningStats {
  total_words: number;
  by_level: Record<number, number>;
  by_state: Record<string, number>;
}

export interface DueWords {
  overdue: UserWordWithWord[];
  learning: UserWordWithWord[];
  new_available: number;
}

// ---------------------------------------------------------------------------
// Training
// ---------------------------------------------------------------------------

export interface TrainingSession {
  id: number;
  started_at: string;
  ended_at: string | null;
  words_reviewed: number;
  words_new: number;
  correct_count: number;
  total_count: number;
  duration_seconds: number;
  accuracy: number;
}

export interface SessionProgress {
  current_index: number;
  total_words: number;
  correct: number;
  wrong: number;
}

export interface Exercise {
  word_id: number;
  exercise_type: number;
  english: string;
  transcription: string | null;
  translations: string[];
  part_of_speech: string | null;
  options?: string[] | null;
  sentence_en?: string | null;
  sentence_ru?: string | null;
  scrambled_words?: string[] | null;
  hint?: string | null;
  reverse?: boolean;
}

export interface AnswerSubmit {
  word_id: number;
  answer: string;
  response_time_ms: number;
}

export interface AnswerResult {
  correct: boolean;
  rating: number;
  correct_answer: string;
  feedback: string | null;
  mastery_level: number;
  level_changed: boolean;
}

export interface SessionSummary {
  total_words: number;
  correct: number;
  wrong: number;
  accuracy: number;
  new_words_learned: number;
  time_spent_seconds: number;
  level_ups: number;
}

export interface StartSessionResult {
  session_id: number;
  exercises: Exercise[];
  total_words: number;
}

// ---------------------------------------------------------------------------
// Stats / Dashboard
// ---------------------------------------------------------------------------

export interface DashboardData {
  streak: number;
  today_reviewed: number;
  today_learned: number;
  today_accuracy: number;
  weekly_data: DailyStats[];
  level_distribution: Record<string, number>;
  coverage_percent: number;
  total_words_known: number;
}

export interface DailyStats {
  date: string;
  words_reviewed: number;
  words_learned: number;
  time_spent: number;
  accuracy: number;
  streak: number;
}

export interface CoverageData {
  known_words: number;
  coverage_percent: number;
  next_milestone: {
    words_needed: number;
    coverage_at_milestone: number;
    words_remaining: number;
  };
}

export interface HeatmapEntry {
  date: string;
  count: number;
  level: number;
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export interface Settings {
  daily_new_words: number;
  session_duration_minutes: number;
  preferred_exercises: number[];
  tts_enabled: boolean;
  tts_speed: number;
  keyboard_shortcuts: boolean;
}

export interface SettingsUpdate {
  daily_new_words?: number;
  session_duration_minutes?: number;
  preferred_exercises?: number[];
  tts_enabled?: boolean;
  tts_speed?: number;
  keyboard_shortcuts?: boolean;
}

// ---------------------------------------------------------------------------
// Exercise Component Props
// ---------------------------------------------------------------------------

export interface ExerciseProps {
  exercise: Exercise;
  onAnswer: (answer: string, timeMs: number) => void;
}

export interface FreeProductionFeedback {
  grammar_ok: boolean;
  word_usage_ok: boolean;
  natural: boolean;
  feedback_ru: string;
  corrected?: string;
}
