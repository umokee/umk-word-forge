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

export interface VerbForms {
  past?: string;
  past_participle?: string;
  present_participle?: string;
  third_person?: string;
}

export interface Collocation {
  en: string;
  ru: string;
}

export interface PhrasalVerb {
  phrase: string;
  meaning_en?: string;
  meaning_ru: string;
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

  // Linguistic enrichment
  verb_forms?: VerbForms | null;
  collocations?: Collocation[] | null;
  phrasal_verbs?: PhrasalVerb[] | null;
  usage_notes?: string[] | null;
}

export interface AnswerSubmit {
  word_id: number;
  answer: string;
  response_time_ms: number;
  exercise_type: number;
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
  // Training
  daily_new_words: number;
  session_duration_minutes: number;
  max_reviews_per_session: number;
  new_words_position: 'start' | 'middle' | 'end';
  exercise_direction: 'en_to_ru' | 'ru_to_en' | 'mixed';
  show_transcription: boolean;
  show_example_translation: boolean;
  auto_play_audio: boolean;
  hint_delay_seconds: number;
  preferred_exercises: number[];

  // Interface
  keyboard_shortcuts: boolean;
  show_progress_details: boolean;
  session_end_summary: boolean;
  animation_speed: 'fast' | 'normal' | 'slow' | 'none';
  font_size: 'small' | 'normal' | 'large';

  // TTS
  tts_enabled: boolean;
  tts_speed: number;
  tts_voice: string;
  tts_auto_play_exercises: boolean;

  // Daily Goal
  daily_goal_type: 'words' | 'minutes' | 'exercises';
  daily_goal_value: number;

  // AI
  gemini_api_key: string | null;
  ai_feedback_language: 'ru' | 'en';
  ai_difficulty_context: 'simple' | 'medium' | 'natural';
}

export interface SettingsUpdate {
  daily_new_words?: number;
  session_duration_minutes?: number;
  max_reviews_per_session?: number;
  new_words_position?: string;
  exercise_direction?: string;
  show_transcription?: boolean;
  show_example_translation?: boolean;
  auto_play_audio?: boolean;
  hint_delay_seconds?: number;
  preferred_exercises?: number[];
  keyboard_shortcuts?: boolean;
  show_progress_details?: boolean;
  session_end_summary?: boolean;
  animation_speed?: string;
  font_size?: string;
  tts_enabled?: boolean;
  tts_speed?: number;
  tts_voice?: string;
  tts_auto_play_exercises?: boolean;
  daily_goal_type?: string;
  daily_goal_value?: number;
  gemini_api_key?: string | null;
  ai_feedback_language?: string;
  ai_difficulty_context?: string;
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

// ---------------------------------------------------------------------------
// Phrasal Verbs
// ---------------------------------------------------------------------------

export interface PhrasalVerbDefinition {
  en: string;
  ru: string;
}

export interface PhrasalVerbFull {
  id: number;
  phrase: string;
  base_verb: string;
  particle: string;
  translations: string[];
  definitions: PhrasalVerbDefinition[];
  frequency_rank: number | null;
  cefr_level: string | null;
  is_separable: boolean;
}

export interface PhrasalVerbContext {
  id: number;
  phrasal_verb_id: number;
  sentence_en: string;
  sentence_ru: string | null;
  source: string | null;
  difficulty: number;
}

export interface UserPhrasalVerb {
  id: number;
  phrasal_verb_id: number;
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

export interface UserPhrasalVerbWithPhrasal extends UserPhrasalVerb {
  phrase: string;
  base_verb: string;
  particle: string;
  translations: string[];
  definitions: PhrasalVerbDefinition[];
  is_separable: boolean;
}

export interface PhrasalVerbExercise {
  phrasal_verb_id: number;
  exercise_type: number;
  phrase: string;
  base_verb: string;
  particle: string;
  translations: string[];
  definitions: PhrasalVerbDefinition[];
  is_separable: boolean;
  options?: string[] | null;
  sentence_en?: string | null;
  sentence_ru?: string | null;
  hint?: string | null;
  particle_options?: string[] | null;
  separability_options?: string[] | null;
}

export interface PhrasalVerbAnswerSubmit {
  phrasal_verb_id: number;
  answer: string;
  response_time_ms: number;
  exercise_type: number;
}

export interface PhrasalVerbAnswerResult {
  correct: boolean;
  rating: number;
  correct_answer: string;
  feedback: string | null;
  mastery_level: number;
  level_changed: boolean;
}

export interface PhrasalVerbSessionResult {
  session_id: number;
  exercises: PhrasalVerbExercise[];
  total_items: number;
}

export interface DuePhrasalVerbs {
  overdue: UserPhrasalVerbWithPhrasal[];
  learning: UserPhrasalVerbWithPhrasal[];
  new_available: number;
}

// ---------------------------------------------------------------------------
// Irregular Verbs
// ---------------------------------------------------------------------------

export interface IrregularVerbFull {
  id: number;
  base_form: string;
  past_simple: string;
  past_participle: string;
  translations: string[];
  transcription_base: string | null;
  transcription_past: string | null;
  transcription_participle: string | null;
  frequency_rank: number | null;
  cefr_level: string | null;
  verb_pattern: string;
}

export interface IrregularVerbContext {
  id: number;
  irregular_verb_id: number;
  sentence_en: string;
  sentence_ru: string | null;
  verb_form_used: string | null;
  source: string | null;
  difficulty: number;
}

export interface UserIrregularVerb {
  id: number;
  irregular_verb_id: number;
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

export interface UserIrregularVerbWithIrregular extends UserIrregularVerb {
  base_form: string;
  past_simple: string;
  past_participle: string;
  translations: string[];
  verb_pattern: string;
  transcription_base: string | null;
  transcription_past: string | null;
  transcription_participle: string | null;
}

export interface IrregularVerbExercise {
  irregular_verb_id: number;
  exercise_type: number;
  base_form: string;
  past_simple: string;
  past_participle: string;
  translations: string[];
  verb_pattern: string;
  transcription_base: string | null;
  transcription_past: string | null;
  transcription_participle: string | null;
  options?: string[] | null;
  sentence_en?: string | null;
  sentence_ru?: string | null;
  hint?: string | null;
  target_form?: string | null;
  given_form?: string | null;
}

export interface IrregularVerbAnswerSubmit {
  irregular_verb_id: number;
  answer: string;
  response_time_ms: number;
  exercise_type: number;
}

export interface IrregularVerbAnswerResult {
  correct: boolean;
  rating: number;
  correct_answer: string;
  feedback: string | null;
  mastery_level: number;
  level_changed: boolean;
}

export interface IrregularVerbSessionResult {
  session_id: number;
  exercises: IrregularVerbExercise[];
  total_items: number;
}

export interface DueIrregularVerbs {
  overdue: UserIrregularVerbWithIrregular[];
  learning: UserIrregularVerbWithIrregular[];
  new_available: number;
}

// ---------------------------------------------------------------------------
// Training Mode Selection
// ---------------------------------------------------------------------------

export type TrainingMode = 'words' | 'phrasal' | 'irregular';

export interface TrainingSelectorProps {
  onModeSelect: (mode: TrainingMode) => void;
}

// ---------------------------------------------------------------------------
// Exercise Component Props for Phrasal and Irregular
// ---------------------------------------------------------------------------

export interface PhrasalVerbExerciseProps {
  exercise: PhrasalVerbExercise;
  onAnswer: (answer: string, timeMs: number) => void;
}

export interface IrregularVerbExerciseProps {
  exercise: IrregularVerbExercise;
  onAnswer: (answer: string, timeMs: number) => void;
}
