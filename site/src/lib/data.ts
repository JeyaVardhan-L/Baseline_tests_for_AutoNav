// Build-time data access. The site renders what tools/export_site_data.py copied into public/data.
import fs from 'node:fs';
import path from 'node:path';

const DATA = path.resolve('public/data');

export const MODE: 'lab' | 'showcase' = (import.meta.env.PUBLIC_MODE === 'lab' ? 'lab' : 'showcase');

export function readJson<T = any>(rel: string, fallback: T | null = null): T | null {
  const p = path.join(DATA, rel);
  if (!fs.existsSync(p)) return fallback;
  return JSON.parse(fs.readFileSync(p, 'utf-8')) as T;
}

export interface RunItem {
  run_id: string; dataset: string; evidence: string; variant: string; profile: string; mode: string; label: string;
  window: { start: number; stop: number; n_frames: number; of_total: number };
  commit: string; git_dirty: boolean | null; started_utc: string; cpu_model: string; hardware_label: string;
  p50_ms?: number; p90_ms?: number; p95_ms?: number; p99_ms?: number; max_ms?: number;
  violation_percent?: number; ate_rmse_m?: number; accepted_percent?: number;
}

export function runs(): RunItem[] {
  return readJson<{ runs: RunItem[] }>('index.json', { runs: [] })!.runs;
}
export const run = (id: string) => readJson(`runs/${id}/run.json`);
export const summary = (id: string) => readJson(`runs/${id}/summary.json`);
export const verdicts = (id: string) => readJson(`runs/${id}/verdicts.json`);
export const base = (import.meta.env.BASE_URL as string).replace(/\/?$/, '/');

export const fmt = (v: number | null | undefined, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? 'UNAVAILABLE' : v.toFixed(d));