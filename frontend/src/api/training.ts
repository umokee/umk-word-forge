import { apiFetch } from './client';
import type {
  TrainingSession,
  StartSessionResult,
  AnswerSubmit,
  AnswerResult,
  SessionSummary,
} from '../types';

export interface CreateSessionParams {
  duration_minutes?: number;
}

export function createSession(
  params: CreateSessionParams = {},
): Promise<StartSessionResult> {
  return apiFetch<StartSessionResult>('/training/session', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function getSession(sessionId: number): Promise<TrainingSession> {
  return apiFetch<TrainingSession>(`/training/session/${sessionId}`);
}

export function submitAnswer(
  sessionId: number,
  answer: AnswerSubmit,
): Promise<AnswerResult> {
  return apiFetch<AnswerResult>(`/training/session/${sessionId}/answer`, {
    method: 'POST',
    body: JSON.stringify(answer),
  });
}

export function endSession(sessionId: number): Promise<SessionSummary> {
  return apiFetch<SessionSummary>(`/training/session/${sessionId}/end`, {
    method: 'POST',
  });
}
