import { apiFetch } from './client';
import type {
  UserWordWithWord,
  PaginatedUserWords,
  ReviewCreate,
  MasteryResult,
  LearningStats,
  DueWords,
} from '../types';

export interface GetLearningWordsParams {
  page?: number;
  per_page?: number;
  level?: number;
  state?: number;
}

export function getLearningWords(
  params: GetLearningWordsParams = {},
): Promise<PaginatedUserWords> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', String(params.page));
  if (params.per_page) query.set('per_page', String(params.per_page));
  if (params.level !== undefined) query.set('level', String(params.level));
  if (params.state !== undefined) query.set('state', String(params.state));

  const qs = query.toString();
  return apiFetch<PaginatedUserWords>(`/learning/words${qs ? `?${qs}` : ''}`);
}

export function getLearningWord(wordId: number): Promise<UserWordWithWord> {
  return apiFetch<UserWordWithWord>(`/learning/words/${wordId}`);
}

export function getDueWords(): Promise<DueWords> {
  return apiFetch<DueWords>('/learning/due');
}

export function getLearningStats(): Promise<LearningStats> {
  return apiFetch<LearningStats>('/learning/stats');
}

export function initializeWord(wordId: number): Promise<UserWordWithWord> {
  return apiFetch<UserWordWithWord>(`/learning/words/${wordId}/initialize`, {
    method: 'POST',
  });
}

export function recordReview(
  wordId: number,
  review: ReviewCreate,
): Promise<MasteryResult> {
  return apiFetch<MasteryResult>(`/learning/words/${wordId}/review`, {
    method: 'POST',
    body: JSON.stringify(review),
  });
}
