// @ts-ignore
import Plotly from 'plotly.js-dist-min';

const root = document.getElementById('charts')!;
const BASE = root.dataset.base || '/';
const MODE = root.dataset.mode || 'showcase';
const url = (p: string) => (MODE === 'lab' ? `/api/runs/${p}` : `${BASE}data/runs/${p}`);
const css = (n: string) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const bench = [css('--bench-1'), css('--bench-2'), css('--bench-3'), css('--bench-4')];
const ink = css('--color-ink');
const layout = (title: string, y: string, extra: any = {}) => ({
  title: { text: title, font: { size: 14 } }, margin: { l: 56, r: 16, t: 40, b: 48 }, font: { family: css('--font-geist') },
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', yaxis: { title: y, gridcolor: css('--color-hairline') },
  xaxis: { gridcolor: css('--color-hairline') }, legend: { orientation: 'h', y: -0.25 }, ...extra,
});
const cfg = { responsive: true, displaylogo: false };
const get = async (p: string) => (await fetch(p)).json();
const deadline = (ms: number, x0 = 0, x1 = 1, xref = 'paper') => ({ type: 'line', xref, x0, x1, y0: ms, y1: ms, line: { color: ink, dash: 'dash', width: 1.5 } });

async function runList(): Promise<any[]> {
  const idx = MODE === 'lab' ? await get('/api/runs') : (await get(`${BASE}data/index.json`)).runs;
  return idx.filter((r: any) => r.status === undefined || r.status === 'completed');
}
const label = (r: any) => `${r.variant} · ${r.profile}${r.mode === 'single-frame' ? ' (single-frame)' : ''}`;

async function perRun(runId: string) {
  const [series, summary] = await Promise.all([get(url(`${runId}/viz/series.json`)), get(url(`${runId}/summary.json`))]);
  const col = (name: string) => series.rows.map((r: any[]) => r[series.columns.indexOf(name)]);
  const frames = col('frame_index'), warm = col('warmup');
  const ms = summary.deadline.deadline_ms;
  const keep = (a: any[]) => a.map((v, i) => (warm[i] ? null : v));
  Plotly.react('c-frames', [
    { x: frames, y: keep(col('preprocess_ms')), name: 'preprocess', mode: 'lines', line: { color: bench[3], width: 1.5 } },
    { x: frames, y: keep(col('register_ms')), name: 'register (ICP)', mode: 'lines', line: { color: bench[1], width: 1.5 } },
    { x: frames, y: keep(col('total_ms')), name: 'total', mode: 'lines', line: { color: bench[0], width: 2 } },
  ], layout('Per-frame latency (repeat 0; warm-up frames not drawn)', 'ms', { xaxis: { title: 'frame index' }, shapes: [deadline(ms)] }), cfg);
  const tot = col('total_ms').filter((v: any, i: number) => v !== null && !warm[i]);
  Plotly.react('c-hist', [{ x: tot, type: 'histogram', marker: { color: bench[0] }, nbinsx: 30 }],
    layout('Distribution of total latency', 'frames', { xaxis: { title: 'ms' }, shapes: [{ ...deadline(ms), type: 'line', xref: 'x', yref: 'paper', x0: ms, x1: ms, y0: 0, y1: 1 }] }), cfg);
  const it = col('icp_iterations'), inl = col('inlier_ratio');
  if (it.some((v: any) => v !== null)) {
    Plotly.react('c-icp', [
      { x: frames, y: it, name: 'ICP iterations', mode: 'lines', line: { color: bench[1] } },
      { x: frames, y: inl, name: 'inlier ratio', yaxis: 'y2', mode: 'lines', line: { color: bench[2] } },
    ], layout('Convergence per frame', 'iterations', { xaxis: { title: 'frame index' }, yaxis2: { overlaying: 'y', side: 'right', range: [0, 1.05], title: 'inlier ratio' } }), cfg);
  }
  const traj = await get(url(`${runId}/viz/trajectory.json`)).catch(() => null);
  if (traj) {
    Plotly.react('c-ate', [{ x: traj.t_s, y: traj.ate_m, mode: 'lines', line: { color: css('--viz-estimate') }, name: 'position error' }],
      layout('Position error after rigid alignment', 'm', { xaxis: { title: 'time (s)' } }), cfg);
  }
}

async function compare() {
  const runs = (await runList()).filter((r: any) => r.mode === 'pipeline');
  if (!runs.length) return;
  const sums = await Promise.all(runs.map((r: any) => get(url(`${r.run_id}/summary.json`))));
  const x = runs.map(label);
  const ms = sums[0].deadline.deadline_ms;
  const traces = ['p50', 'p95', 'p99'].map((k, i) => ({ x, y: sums.map((s: any) => s.latency_ms.total_ms[k]), type: 'bar', name: k.toUpperCase(), marker: { color: bench[i] } }));
  Plotly.react('c-compare', traces, layout('Latency percentiles by run', 'ms', { barmode: 'group', shapes: [deadline(ms)] }), cfg);
  Plotly.react('c-viol', [{ x, y: sums.map((s: any) => s.deadline.pipeline_total_ms.violation_percent), type: 'bar', marker: { color: bench[0] } }],
    layout('Deadline violation rate', '% of frames', { yaxis: { range: [0, 100], title: '% of frames' } }), cfg);
}

(async () => {
  const runs = await runList();
  const sel = document.getElementById('run') as HTMLSelectElement;
  sel.innerHTML = runs.map((r: any) => `<option value="${r.run_id}">${r.dataset} · ${label(r)}</option>`).join('');
  if (runs.length) { perRun(sel.value); sel.addEventListener('change', () => perRun(sel.value)); }
  compare();
})();