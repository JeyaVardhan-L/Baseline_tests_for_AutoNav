const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const get = async (u: string) => (await fetch(u)).json();
const fill = (el: HTMLSelectElement, items: string[]) => (el.innerHTML = items.map((i) => `<option>${i}</option>`).join(''));

(async () => {
  const cfg = await get('/api/config');
  fill($('f-dataset'), Object.keys(cfg.datasets)); fill($('f-variant'), cfg.variants.filter((v: string) => true)); fill($('f-profile'), Object.keys(cfg.profiles));
  const claim = () => { $('f-claim').textContent = cfg.profiles[($('f-profile') as HTMLSelectElement).value]; };
  $('f-profile').addEventListener('change', claim); claim();

  async function history() {
    const runs = await get('/api/runs');
    $('history').querySelector('tbody')!.innerHTML = runs.map((r: any) => `<tr>
      <td><input type="checkbox" data-run="${r.run_id}" aria-label="select ${r.run_id}"></td>
      <td><span class="mono">${r.run_id}</span><br><span class="muted">${r.status} · ${r.variant ?? ''} · ${r.profile ?? ''} · ${r.evidence ?? ''}</span></td>
      <td>${r.p50_ms?.toFixed(1) ?? '–'}</td><td>${r.p95_ms?.toFixed(1) ?? '–'}</td><td>${r.p99_ms?.toFixed(1) ?? '–'}</td>
      <td>${r.violation_percent?.toFixed(1) ?? '–'} %</td><td>${r.ate_rmse_m?.toFixed(2) ?? '–'}</td>
      <td><button class="outline" data-pub="${r.run_id}" data-state="${r.published}">${r.published ? 'Unpublish' : 'Publish'}</button></td></tr>`).join('');
    $('history').querySelectorAll('button[data-pub]').forEach((b) => b.addEventListener('click', async () => {
      const el = b as HTMLButtonElement;
      await fetch('/api/publish', { method: 'POST', body: JSON.stringify({ run_id: el.dataset.pub, publish: el.dataset.state !== 'true' }) });
      history();
    }));
  }

  $('f-run').addEventListener('click', async () => {
    const body = { dataset: ($('f-dataset') as HTMLSelectElement).value, window: ($('f-window') as HTMLInputElement).value, variant: ($('f-variant') as HTMLSelectElement).value,
      profile: ($('f-profile') as HTMLSelectElement).value, repeats: Number(($('f-repeats') as HTMLInputElement).value), mode: ($('f-mode') as HTMLSelectElement).value };
    const res = await fetch('/api/run', { method: 'POST', body: JSON.stringify(body) });
    const j = await res.json();
    if (!res.ok) { $('f-status').textContent = j.error; return; }
    const poll = async () => {
      const s = await get(`/api/jobs/${j.job_id}`);
      const fp = s.frame_progress, rp = s.run_progress;
      $('f-status').textContent = s.state === 'running'
        ? `Running${rp ? ` · repeat ${rp.repeat}/${rp.repeats}` : ''}${fp ? ` · frame ${fp.frames_done}/${fp.frames_total}` : ''}`
        : `${s.state}${s.run_id ? ' · ' + s.run_id : ''}`;
      if (s.state === 'running') setTimeout(poll, 1500); else history();
    };
    poll();
  });

  $('compare').addEventListener('click', async () => {
    const ids = [...document.querySelectorAll('input[data-run]:checked')].map((e) => (e as HTMLInputElement).dataset.run!).slice(0, 3);
    const sums = await Promise.all(ids.map((id) => get(`/api/runs/${id}/summary.json`)));
    $('compare-out').innerHTML = `<table><thead><tr><th>Run</th><th>P50</th><th>P95</th><th>P99</th><th>Max</th><th>Violation %</th><th>ATE RMSE</th></tr></thead><tbody>${sums.map((s: any, i: number) => `<tr><td class="mono">${ids[i]}</td><td>${s.latency_ms.total_ms.p50.toFixed(1)}</td><td>${s.latency_ms.total_ms.p95.toFixed(1)}</td><td>${s.latency_ms.total_ms.p99.toFixed(1)}</td><td>${s.latency_ms.total_ms.max.toFixed(1)}</td><td>${s.deadline.pipeline_total_ms.violation_percent.toFixed(1)}</td><td>${s.accuracy?.ate_m?.rmse?.toFixed(2) ?? '–'}</td></tr>`).join('')}</tbody></table>`;
  });
  history();
})();