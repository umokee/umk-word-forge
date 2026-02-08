const BASE_URL = '/api';

function getApiKey(): string {
  return localStorage.getItem('wordforge_api_key') || '';
}

export function setApiKey(key: string): void {
  localStorage.setItem('wordforge_api_key', key);
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const apiKey = getApiKey();
  const method = (options?.method || 'GET').toUpperCase();
  const hasBody = options?.body !== undefined;
  const headers: Record<string, string> = {
    ...(hasBody || method === 'POST' || method === 'PUT' || method === 'PATCH'
      ? { 'Content-Type': 'application/json' }
      : {}),
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
    ...(options?.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    throw new Error('AUTH_REQUIRED');
  }

  if (!res.ok) {
    const error = await res.json().catch(() => {
      // Non-JSON response (e.g. nginx HTML error page) — provide a
      // human-readable hint so the error screen is more helpful.
      if (res.status === 400) {
        return { detail: 'Bad request — ensure you are using HTTPS' };
      }
      if (res.status === 502 || res.status === 503) {
        return { detail: 'Backend is not reachable — it may still be starting' };
      }
      return { detail: `HTTP ${res.status}` };
    });
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return undefined as T;

  return res.json();
}
