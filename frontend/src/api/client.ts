const BASE_URL = '/api';

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const method = (options?.method || 'GET').toUpperCase();
  const hasBody = options?.body !== undefined;
  const headers: Record<string, string> = {
    ...(hasBody || method === 'POST' || method === 'PUT' || method === 'PATCH'
      ? { 'Content-Type': 'application/json' }
      : {}),
    ...(options?.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => {
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
