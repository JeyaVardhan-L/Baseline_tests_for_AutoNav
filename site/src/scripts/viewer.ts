import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const root = document.getElementById('viewer')!;
const BASE = root.dataset.base || '/';
const MODE = root.dataset.mode || 'showcase';
const dataUrl = (p: string) => (MODE === 'lab' ? `/api/runs/${p.replace(/^runs\//, '')}` : `${BASE}data/${p}`);
const css = (n: string) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const ROLE_COLOR: Record<string, string> = {
  source_before: css('--viz-source'), source_after: css('--viz-source'), target: css('--viz-target'),
  stage_raw: '#a3a3a3', stage_range: '#737373', stage_voxel: '#171717', stage_outlier: '#171717',
};

const canvas = document.getElementById('gl') as HTMLCanvasElement;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);
const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
camera.up.set(0, 0, 1);
camera.position.set(25, -25, 18);
const controls = new OrbitControls(camera, canvas);
const axes = new THREE.AxesHelper(2);
scene.add(axes);
const groups = new Map<string, THREE.Object3D>();
let pointSize = 2;

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w * devicePixelRatio || canvas.height !== h * devicePixelRatio) {
    renderer.setPixelRatio(devicePixelRatio); renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
}
function loop() { resize(); controls.update(); renderer.render(scene, camera); requestAnimationFrame(loop); }
loop();

function clear() { groups.forEach((o) => scene.remove(o)); groups.clear(); (document.getElementById('layers') as HTMLElement).innerHTML = ''; }

async function loadCloud(layer: any, runPath: string) {
  const buf = new Uint16Array(await (await fetch(dataUrl(`${runPath}/viz/${layer.file}`))).arrayBuffer());
  const pos = new Float32Array(buf.length);
  for (let i = 0; i < buf.length; i += 3) for (let k = 0; k < 3; k++) pos[i + k] = layer.origin[k] + buf[i + k] * layer.scale;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const color = layer.role === 'stage' ? ROLE_COLOR['stage_' + layer.stage] : ROLE_COLOR[layer.role];
  const pts = new THREE.Points(g, new THREE.PointsMaterial({ color, size: pointSize, sizeAttenuation: false }));
  return pts;
}

function addToggle(id: string, label: string, obj: THREE.Object3D, on: boolean) {
  groups.set(id, obj); scene.add(obj); obj.visible = on;
  const l = document.createElement('label');
  l.style.display = 'block';
  l.innerHTML = `<input type="checkbox" ${on ? 'checked' : ''}> ${label}`;
  (l.firstElementChild as HTMLInputElement).addEventListener('change', (e) => { obj.visible = (e.target as HTMLInputElement).checked; });
  document.getElementById('layers')!.appendChild(l);
}

async function show(runId: string) {
  clear();
  const runPath = `runs/${runId}`;
  const manifest = await (await fetch(dataUrl(`${runPath}/viz/manifest.json`))).json();
  const prov = manifest.provenance;
  const pair = (document.getElementById('pair') as HTMLSelectElement).value;
  const pairInfo = manifest.pairs[pair] || {};
  const view = (document.getElementById('view') as HTMLSelectElement).value;
  let box = new THREE.Box3();
  if (view === 'clouds') {
    const wanted = manifest.layers.filter((l: any) => l.id.startsWith(pair + '_') || l.role === 'stage');
    for (const layer of wanted) {
      const pts = await loadCloud(layer, runPath);
      const on = layer.role !== 'stage' && layer.role !== 'source_before';
      const label = layer.role === 'stage' ? `Stage: ${layer.stage} (${layer.points_before_decimation.toLocaleString()} pts)` :
        `${layer.role.replace('_', ' ')} (frame ${layer.frame_index})`;
      addToggle(layer.id, label, pts, on || (layer.role === 'stage' && layer.stage === 'voxel' && !wanted.some((w: any) => w.role === 'target')));
      box.expandByObject(pts);
    }
  } else {
    const t = await (await fetch(dataUrl(`${runPath}/viz/trajectory.json`))).json().catch(() => null);
    if (t) {
      const line = (arr: number[][], color: string) => new THREE.Line(new THREE.BufferGeometry().setFromPoints(arr.map((p) => new THREE.Vector3(p[0], p[1], p[2]))), new THREE.LineBasicMaterial({ color }));
      const gt = line(t.gt_xyz, css('--viz-truth')); const est = line(t.est_aligned_xyz, css('--viz-estimate'));
      addToggle('gt', 'Ground truth', gt, true); addToggle('est', 'Estimate (aligned)', est, true);
      box.expandByObject(gt);
    }
  }
  if (!box.isEmpty()) {
    const c = box.getCenter(new THREE.Vector3()); const r = box.getSize(new THREE.Vector3()).length() / 2 || 10;
    controls.target.copy(c); camera.position.copy(c).add(new THREE.Vector3(r, -r, r * 0.7)); camera.far = r * 20; camera.updateProjectionMatrix();
  }
  const info = document.getElementById('provenance')!;
  const f = (x: number | undefined, d = 3) => (x === undefined ? 'n/a' : x.toFixed(d));
  info.innerHTML = `
    <p class="caption">Provenance</p>
    <table><tbody>
      <tr><th>Dataset / sequence</th><td>${prov.dataset} · ${prov.sequence}</td></tr>
      <tr><th>Sensor</th><td>${prov.sensor}</td></tr>
      <tr><th>Evidence</th><td><b>${prov.evidence}</b></td></tr>
      <tr><th>Frames</th><td>${view === 'clouds' ? (pairInfo.frame_index !== undefined ? `scan ${pairInfo.frame_index - 1} (target) and scan ${pairInfo.frame_index} (source), window ${manifest.window.start}–${manifest.window.stop}` : 'one frame') : `window ${manifest.window.start}–${manifest.window.stop}`}</td></tr>
      <tr><th>Stages / parameters</th><td>invalid-point removal → range ${prov.parameters.min_range}–${prov.parameters.max_range} m → voxel ${prov.parameters.voxel_size} m → ICP (max distance ${prov.parameters.max_correspondence_distance} m, ≤${prov.parameters.max_iterations} iterations)</td></tr>
      <tr><th>Run · commit · variant</th><td class="mono">${prov.run_id} · ${prov.commit.slice(0, 7)} · ${prov.variant}</td></tr>
      <tr><th>Hardware</th><td>${prov.hardware_label}</td></tr>
      ${pairInfo.icp_iterations !== undefined ? `<tr><th>This pair</th><td>${pairInfo.icp_iterations} iterations, inlier ratio ${f(pairInfo.inlier_ratio)}, residual ${f(pairInfo.residual_m)} m, ${pairInfo.accepted ? 'accepted' : 'rejected: ' + pairInfo.reject_reason}, ${f(pairInfo.total_ms, 0)} ms</td></tr>` : ''}
    </tbody></table>
    <p class="muted" style="margin-top:8px">${prov.attribution}</p>`;
}

(async () => {
  const idx = await (await fetch(dataUrl('index.json').replace('/api/runs/index.json', '/api/runs'))).json().catch(() => ({ runs: [] }));
  const runs = (idx.runs || idx).filter((r: any) => (r.status === undefined || r.status === 'completed'));
  const sel = document.getElementById('run') as HTMLSelectElement;
  sel.innerHTML = runs.map((r: any) => `<option value="${r.run_id}">${r.dataset} · ${r.variant} · ${r.profile}${r.mode === 'single-frame' ? ' · single-frame' : ''}</option>`).join('');
  const rerender = () => { if (sel.value) show(sel.value).catch((e) => { document.getElementById('provenance')!.textContent = 'No visual artifacts for this run: ' + e; }); };
  ['run', 'pair', 'view'].forEach((id) => document.getElementById(id)!.addEventListener('change', rerender));
  (document.getElementById('size') as HTMLInputElement).addEventListener('input', (e) => {
    pointSize = Number((e.target as HTMLInputElement).value);
    groups.forEach((o: any) => { if (o.material && 'size' in o.material) o.material.size = pointSize; });
  });
  (document.getElementById('axes') as HTMLInputElement).addEventListener('change', (e) => { axes.visible = (e.target as HTMLInputElement).checked; });
  const flip = document.getElementById('flip') as HTMLButtonElement;
  flip.addEventListener('click', () => {  // before / after registration
    const a = [...groups.keys()].find((k) => k.endsWith('source_before')); const b = [...groups.keys()].find((k) => k.endsWith('source_after'));
    if (a && b) { const showAfter = !groups.get(b)!.visible; groups.get(a)!.visible = !showAfter; groups.get(b)!.visible = showAfter; }
  });
  rerender();
})();