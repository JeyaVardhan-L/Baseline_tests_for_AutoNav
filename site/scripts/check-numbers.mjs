// Verifies that every number rendered on the built site equals the value in artifacts/ (the source of truth).
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('..');
const dist = path.resolve('dist');
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]));
const published = JSON.parse(fs.readFileSync(path.join(root, 'artifacts', 'published.json'), 'utf-8')).runs;
const re = /<span class="num"[^>]*data-run="([^"]+)"[^>]*data-file="([^"]+)"[^>]*data-path="([^"]+)"[^>]*data-digits="([^"]+)"[^>]*>([^<]*)<\/span>/g;
let checked = 0, bad = 0;
for (const f of walk(dist).filter((x) => x.endsWith('.html'))) {
  const html = fs.readFileSync(f, 'utf-8');
  for (const m of html.matchAll(re)) {
    const [, run, file, p, digits, shown] = m;
    checked++;
    if (!published.includes(run)) { console.error(`NOT PUBLISHED: ${run} (${path.basename(f)})`); bad++; continue; }
    let v = JSON.parse(fs.readFileSync(path.join(root, 'artifacts', 'runs', run, file), 'utf-8'));
    for (const k of p.split('.')) v = v == null ? null : v[k];
    const expected = typeof v === 'number' ? v.toFixed(Number(digits)) : v == null ? 'UNAVAILABLE' : String(v);
    if (expected !== shown.trim()) { console.error(`MISMATCH ${run} ${file}:${p}  page="${shown}" artifact="${expected}"`); bad++; }
  }
}
// no private paths or secrets in the build
const pat = [/[A-Za-z]:[\\/]+Users[\\/]/, /drive\.google\.com/, /\/home\/[a-z]/];
const emailPat = /[\w.+-]+@[\w-]+\.[\w.-]+/;   // not applied to bundled vendor JavaScript
for (const f of walk(dist).filter((x) => /\.(html|json|js|css|csv)$/.test(x))) {
  const t = fs.readFileSync(f, 'utf-8');
  for (const p of pat) if (p.test(t)) { console.error(`PRIVATE PATTERN ${p} in ${path.relative(dist, f)}`); bad++; }
  if (/\.(html|json|csv)$/.test(f) && emailPat.test(t)) { console.error(`E-MAIL ADDRESS in ${path.relative(dist, f)}`); bad++; }
}
console.log(`checked ${checked} rendered numbers against artifacts/; ${bad} problem(s)`);
process.exit(bad ? 1 : 0);