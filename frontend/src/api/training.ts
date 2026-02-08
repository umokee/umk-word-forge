import { apiFetch } from './client';
import type {
  TrainingSession,
  StartSessionResult,
  AnswerSubmit,
  AnswerResult,
  SessionSummary,
  PhrasalVerbSessionResult,
  PhrasalVerbAnswerSubmit,
  PhrasalVerbAnswerResult,
  IrregularVerbSessionResult,
  IrregularVerbAnswerSubmit,
  IrregularVerbAnswerResult,
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

// ---------------------------------------------------------------------------
// Phrasal Verb Training API
// ---------------------------------------------------------------------------

export function createPhrasalSession(
  params: CreateSessionParams = {},
): Promise<PhrasalVerbSessionResult> {
  return apiFetch<PhrasalVerbSessionResult>('/training/session/phrasal', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function submitPhrasalAnswer(
  sessionId: number,
  answer: PhrasalVerbAnswerSubmit,
): Promise<PhrasalVerbAnswerResult> {
  return apiFetch<PhrasalVerbAnswerResult>(
    `/training/session/${sessionId}/phrasal/answer`,
    {
      method: 'POST',
      body: JSON.stringify(answer),
    },
  );
}

// ---------------------------------------------------------------------------
// Irregular Verb Training API
// ---------------------------------------------------------------------------

export function createIrregularSession(
  params: CreateSessionParams = {},
): Promise<IrregularVerbSessionResult> {
  return apiFetch<IrregularVerbSessionResult>('/training/session/irregular', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function submitIrregularAnswer(
  sessionId: number,
  answer: IrregularVerbAnswerSubmit,
): Promise<IrregularVerbAnswerResult> {
  return apiFetch<IrregularVerbAnswerResult>(
    `/training/session/${sessionId}/irregular/answer`,
    {
      method: 'POST',
      body: JSON.stringify(answer),
    },
  );
}
