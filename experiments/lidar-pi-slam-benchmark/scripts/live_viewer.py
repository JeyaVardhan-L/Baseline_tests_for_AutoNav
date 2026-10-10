#!/usr/bin/env python3
"""Local live SLAM dashboard. Standard-library server; no Flask/Node dependency.

Run on the Raspberry Pi, then open http://<PI-LAN-IP>:8765 on a laptop on the same LAN.
The benchmark can publish JSON to POST /api/update and refresh map.png on disk.
"""
from __future__ import annotations
import argparse, json, mimetypes, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_OUT = Path(__file__).resolve().parents[3] / "results" / "lidar-pi-slam-benchmark"
HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AutoNav · Live SLAM</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2b;--line:#25334c;--text:#e7eefc;--muted:#91a2bd;--accent:#63e6be;--warn:#ffd166}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{padding:18px 22px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
h1{font-size:20px;margin:0}small,.muted{color:var(--muted)}main{padding:18px;max-width:1500px;margin:auto}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(130px,1fr));gap:10px;margin-bottom:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;min-width:0}.label{font-size:12px;color:var(--muted)}.value{font-size:24px;font-weight:650;margin-top:4px;overflow-wrap:anywhere}
.layout{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(280px,1fr);gap:14px}.mapwrap{background:#080c15;border:1px solid var(--line);border-radius:10px;min-height:350px;display:flex;align-items:center;justify-content:center;overflow:hidden}
#map{max-width:100%;max-height:72vh;object-fit:contain}#empty{color:var(--muted);padding:30px;text-align:center}
canvas{width:100%;height:250px;display:block}.status{display:inline-flex;gap:7px;align-items:center}.dot{width:9px;height:9px;border-radius:50%;background:#65758e}.dot.live{background:var(--accent);box-shadow:0 0 12px #63e6be66}
.row{display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid var(--line)}.row:last-child{border:0}
button{background:#1c2940;border:1px solid #354765;color:var(--text);padding:7px 10px;border-radius:8px;cursor:pointer}
@media(max-width:900px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.layout{grid-template-columns:1fr}.mapwrap{min-height:260px}} 
</style></head><body>
<header><div><h1>AutoNav <span class="muted">/ Live SLAM</span></h1><small>Raspberry Pi 5 · BreezySLAM telemetry</small></div>
<div class="status"><span id="dot" class="dot"></span><span id="connection">Waiting for benchmark data</span><button id="pause">Pause updates</button></div></header>
<main>
<div class="metrics">
<div class="card"><div class="label">Scans processed</div><div id="scans" class="value">—</div></div>
<div class="card"><div class="label">Scan rate</div><div id="rate" class="value">—</div></div>
<div class="card"><div class="label">Last processing</div><div id="latency" class="value">—</div></div>
<div class="card"><div class="label">Pose (x, y)</div><div id="pose" class="value" style="font-size:18px">—</div></div>
<div class="card"><div class="label">Heading</div><div id="heading" class="value">—</div></div>
</div>
<div class="layout"><section class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><strong>Occupancy map</strong><small id="mapstamp">Waiting for map</small></div><div class="mapwrap"><img id="map" alt="Latest SLAM map" hidden><div id="empty">Start the benchmark with live publishing enabled.<br>The map will appear when the first map snapshot is written.</div></div></section>
<aside style="display:grid;gap:14px;align-content:start"><section class="card"><strong>Processing latency</strong><canvas id="chart" width="600" height="250"></canvas><small>Recent samples · milliseconds</small></section>
<section class="card"><strong>Runtime status</strong><div class="row"><span class="muted">Last update</span><span id="updated">—</span></div><div class="row"><span class="muted">Temperature</span><span id="temp">—</span></div><div class="row"><span class="muted">RSS memory</span><span id="rss">—</span></div><div class="row"><span class="muted">Deadline misses</span><span id="misses">—</span></div><div class="row"><span class="muted">Run mode</span><span id="mode">—</span></div></section>
<section class="card"><strong>Setup</strong><p class="muted">Keep the Pi and laptop on the same trusted network. This dashboard is intended for a private lab LAN, not exposure to the public internet.</p><button onclick="location.reload()">Reconnect</button></section></aside></div>
</main>
<script>
let paused=false,latencies=[],lastIndex=null,lastTime=null,lastMapStamp=null;
const $=id=>document.getElementById(id);
$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'Resume updates':'Pause updates';if(!paused)refresh()};
function set(id,v){$(id).textContent=v===undefined||v===null?'—':v}
function draw(){const c=$('chart'),ctx=c.getContext('2d'),w=c.width,h=c.height;ctx.clearRect(0,0,w,h);ctx.strokeStyle='#25334c';ctx.fillStyle='#91a2bd';ctx.lineWidth=1;for(let i=0;i<5;i++){let y=10+i*(h-30)/4;ctx.beginPath();ctx.moveTo(38,y);ctx.lineTo(w-8,y);ctx.stroke()}if(!latencies.length)return;const max=Math.max(10,...latencies)*1.15;ctx.fillStyle='#91a2bd';ctx.font='12px system-ui';ctx.fillText(max.toFixed(1)+' ms',3,14);ctx.strokeStyle='#63e6be';ctx.lineWidth=2;ctx.beginPath();latencies.forEach((v,i)=>{let x=38+i*(w-48)/Math.max(1,latencies.length-1),y=h-20-v/max*(h-40);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke()}
async function refresh(){if(paused)return;try{const r=await fetch('/api/state?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();$('dot').classList.toggle('live',!!d.running);set('connection',d.running?'Receiving live updates':'Viewer connected · waiting for new scans');set('scans',d.scans_processed);set('rate',d.scan_rate_hz==null?'—':Number(d.scan_rate_hz).toFixed(2)+' Hz');set('latency',d.processing_ms==null?'—':Number(d.processing_ms).toFixed(2)+' ms');set('pose',d.pose_x_m==null?'—':Number(d.pose_x_m).toFixed(2)+', '+Number(d.pose_y_m).toFixed(2)+' m');set('heading',d.pose_theta_deg==null?'—':Number(d.pose_theta_deg).toFixed(1)+'°');set('updated',d.updated_at||'—');set('temp',d.cpu_temperature_c==null?'—':Number(d.cpu_temperature_c).toFixed(1)+' °C');set('rss',d.process_rss_mb==null?'—':Number(d.process_rss_mb).toFixed(1)+' MB');set('misses',d.deadline_misses);set('mode',d.mode||'—');
if(d.processing_ms!=null&&d.sample_id!==lastIndex){latencies.push(Number(d.processing_ms));if(latencies.length>100)latencies.shift();lastIndex=d.sample_id;draw()}
if(d.map_available){$('map').hidden=false;$('empty').hidden=true;if(d.map_updated_at!==lastMapStamp){$('map').src='/map.png?ts='+Date.now();lastMapStamp=d.map_updated_at;set('mapstamp','Updated '+(d.map_updated_at||''))}}
}catch(e){$('dot').classList.remove('live');set('connection','Waiting for Pi / viewer server')} }
setInterval(refresh,500);refresh();
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    state_lock = threading.Lock()
    state = {"running": False, "mode": "waiting"}
    state_seen = 0.0

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_bytes(self, status, data, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.send_bytes(200, HTML.encode(), "text/html; charset=utf-8")
        if path == "/api/state":
            with self.state_lock:
                state = dict(self.state)
            state["running"] = bool(time.time() - self.state_seen < 3.0)
            map_path = DEFAULT_OUT / "live_map.png"
            if not map_path.exists():
                map_path = DEFAULT_OUT / "slam_map.png"
            state["map_available"] = map_path.exists()
            state["map_updated_at"] = str(map_path.stat().st_mtime_ns) if map_path.exists() else None
            return self.send_bytes(200, json.dumps(state).encode(), "application/json")
        if path == "/map.png":
            candidate = DEFAULT_OUT / "live_map.png"
            if not candidate.exists():
                candidate = DEFAULT_OUT / "slam_map.png"
            if candidate.exists():
                return self.send_bytes(200, candidate.read_bytes(), "image/png")
            return self.send_bytes(404, b"Map not ready", "text/plain")
        return self.send_bytes(404, b"Not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/api/update":
            return self.send_bytes(404, b"Not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 65536:
                return self.send_bytes(413, b"Invalid payload size", "text/plain")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            with self.state_lock:
                self.state = payload
                self.state_seen = time.time()
            return self.send_bytes(200, b'{"ok":true}', "application/json")
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_bytes(400, str(exc).encode(), "text/plain")

def main():
    global DEFAULT_OUT
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="0.0.0.0", help="Bind address; use 127.0.0.1 to restrict to this machine")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    DEFAULT_OUT = args.output_dir.expanduser().resolve()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"AutoNav live viewer: http://<PI-LAN-IP>:{args.port}")
    print(f"Map/output directory: {DEFAULT_OUT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping live viewer.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
