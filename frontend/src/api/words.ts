import { apiFetch } from './client';
import type { Word, WordListItem, WordCreate, PaginatedWords } from '../types';

export interface GetWordsParams {
  page?: number;
  per_page?: number;
  search?: string;
  cefr_level?: string;
  part_of_speech?: string;
}

export function getWords(params: GetWordsParams = {}): Promise<PaginatedWords> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', String(params.page));
  if (params.per_page) query.set('per_page', String(params.per_page));
  if (params.search) query.set('search', params.search);
  if (params.cefr_level) query.set('cefr_level', params.cefr_level);
  if (params.part_of_speech) query.set('part_of_speech', params.part_of_speech);

  const qs = query.toString();
  return apiFetch<PaginatedWords>(`/words${qs ? `?${qs}` : ''}`);
}

export function getWord(id: number): Promise<Word> {
  return apiFetch<Word>(`/words/${id}`);
}

export function searchWords(q: string): Promise<WordListItem[]> {
  return apiFetch<WordListItem[]>(`/words/search?q=${encodeURIComponent(q)}`);
}

export function createWord(data: WordCreate): Promise<Word> {
  return apiFetch<Word>('/words', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function deleteWord(id: number): Promise<void> {
  return apiFetch<void>(`/words/${id}`, {
    method: 'DELETE',
  });
}
