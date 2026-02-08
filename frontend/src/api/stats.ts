import { apiFetch } from './client';
import type {
  DashboardData,
  DailyStats,
  CoverageData,
  HeatmapEntry,
} from '../types';

export function getDashboard(): Promise<DashboardData> {
  return apiFetch<DashboardData>('/stats/dashboard');
}

export interface GetDailyStatsParams {
  from?: string;
  to?: string;
}

export function getDailyStats(
  params: GetDailyStatsParams = {},
): Promise<DailyStats[]> {
  const query = new URLSearchParams();
  if (params.from) query.set('from', params.from);
  if (params.to) query.set('to', params.to);

  const qs = query.toString();
  return apiFetch<DailyStats[]>(`/stats/daily${qs ? `?${qs}` : ''}`);
}

export function getCoverage(): Promise<CoverageData> {
  return apiFetch<CoverageData>('/stats/coverage');
}

export function getHeatmap(year?: number): Promise<HeatmapEntry[]> {
  const query = year ? `?year=${year}` : '';
  return apiFetch<HeatmapEntry[]>(`/stats/heatmap${query}`);
}
