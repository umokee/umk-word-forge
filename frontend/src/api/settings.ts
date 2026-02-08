import { apiFetch } from './client';
import type { Settings, SettingsUpdate } from '../types';

export function getSettings(): Promise<Settings> {
  return apiFetch<Settings>('/settings');
}

export function updateSettings(data: SettingsUpdate): Promise<Settings> {
  return apiFetch<Settings>('/settings', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
