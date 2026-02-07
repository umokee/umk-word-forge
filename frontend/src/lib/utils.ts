import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatPercent(n: number): string {
  return `${Math.round(n * 100)}%`;
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('ru-RU');
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
