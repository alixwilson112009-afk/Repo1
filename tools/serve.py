#!/usr/bin/env python3
"""
Local web UI for places_prospector.py — start a run, watch progress, grab the CSV.

Runs on your own machine, so there is no function timeout to work around, no
hosting bill, and the API key stays in your shell instead of a cloud provider's
environment panel.

    export GOOGLE_PLACES_API_KEY=...
    python3 tools/serve.py

Then open http://127.0.0.1:8000.

Progress is read straight out of the prospector's checkpoint directory rather
than by parsing its output, so the two stay decoupled: the line counts in
places.jsonl, tiles.done and emails.jsonl are the progress. Closing the browser
does not stop the run, and reopening it reattaches to the job in flight.

Stdlib only — nothing to install beyond what the prospector already needs.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from places_prospector import build_grid, parse_center  # noqa: E402

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "places_prospector.py"


def count_lines(path):
    try:
        with open(path, "rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


class Job:
    """One prospector subprocess, plus whatever we can learn about its progress."""

    def __init__(self):
        self.lock = threading.Lock()
        self.proc = None
        self.started = None
        self.finished = None
        self.error = None
        self.params = {}
        self.tiles_total = 0
        self.out_path = None
        self.state_dir = None
        self.lines = []

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, params):
        with self.lock:
            if self.running:
                raise RuntimeError("a run is already in progress")

            centers = []
            if params.get("centers_file"):
                path = Path(params["centers_file"])
                if not path.is_absolute():
                    path = HERE.parent / path
                if not path.exists():
                    raise RuntimeError(f"centers file not found: {path}")
                for line in path.read_text().splitlines():
                    line = line.split("#", 1)[0].strip()
                    if line:
                        centers.append(parse_center(line))
                center_args = ["--centers-file", str(path)]
            else:
                centers = [parse_center(params["center"])]
                center_args = ["--center", params["center"]]

            radius = float(params.get("radius_km", 40))
            tile = float(params.get("tile_km", 8))
            self.tiles_total = sum(
                len(build_grid(lat, lon, radius, tile)) for lat, lon in centers
            )

            out = params.get("out") or "prospects.csv"
            self.out_path = (HERE.parent / out).resolve()
            self.state_dir = Path(f"{self.out_path}.state")

            cmd = [
                sys.executable,
                "-u",
                str(SCRIPT),
                "--query",
                params["query"],
                *center_args,
                "--radius-km",
                str(radius),
                "--tile-km",
                str(tile),
                "--out",
                str(self.out_path),
            ]
            if params.get("enrich_emails"):
                cmd.append("--enrich-emails")
            if params.get("emails_only"):
                cmd.append("--emails-only")
            if params.get("restart"):
                cmd.append("--restart")

            if not os.environ.get("GOOGLE_PLACES_API_KEY"):
                raise RuntimeError(
                    "GOOGLE_PLACES_API_KEY is not set in the shell running this server"
                )

            self.lines = []
            self.error = None
            self.finished = None
            self.started = time.time()
            self.params = dict(params, tiles_total=self.tiles_total)
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(HERE.parent),
            )
            threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self):
        proc = self.proc
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self.lines.append(line)
                del self.lines[:-200]
        code = proc.wait()
        self.finished = time.time()
        if code != 0:
            tail = "\n".join(self.lines[-6:])
            self.error = f"exited with code {code}\n{tail}"

    def stop(self):
        if self.running:
            self.proc.terminate()

    def status(self):
        st = {
            "running": self.running,
            "started": self.started,
            "elapsed": (self.finished or time.time()) - self.started
            if self.started
            else 0,
            "error": self.error,
            "params": self.params,
            "tiles_total": self.tiles_total,
            "tiles_done": 0,
            "businesses": 0,
            "scraped": 0,
            "emails": 0,
            "sites_total": 0,
            "phase": "idle",
            "log": self.lines[-8:],
            "ready": False,
        }
        if not self.started:
            return st

        if self.state_dir and self.state_dir.exists():
            st["tiles_done"] = count_lines(self.state_dir / "tiles.done")
            st["businesses"] = count_lines(self.state_dir / "places.jsonl")

            emails_path = self.state_dir / "emails.jsonl"
            scraped = hits = 0
            try:
                with open(emails_path, encoding="utf-8") as fh:
                    for line in fh:
                        if not line.strip():
                            continue
                        scraped += 1
                        try:
                            if json.loads(line).get("emails"):
                                hits += 1
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass
            st["scraped"] = scraped
            st["emails"] = hits

            # Websites are only known once places.jsonl exists; count them so the
            # email stage has a real denominator instead of a guess.
            sites = 0
            try:
                with open(self.state_dir / "places.jsonl", encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            if json.loads(line).get("website"):
                                sites += 1
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass
            st["sites_total"] = sites

        searching = st["tiles_done"] < st["tiles_total"]
        if not self.running:
            st["phase"] = "error" if self.error else "done"
        elif searching:
            st["phase"] = "searching"
        else:
            st["phase"] = "emails" if self.params.get("enrich_emails") else "writing"

        # Overall fraction: the search stage is the first half when an email
        # pass follows it, the whole bar when it does not.
        tiles_frac = st["tiles_done"] / st["tiles_total"] if st["tiles_total"] else 0
        if self.params.get("enrich_emails"):
            email_frac = st["scraped"] / st["sites_total"] if st["sites_total"] else 0
            st["progress"] = 0.5 * tiles_frac + 0.5 * email_frac
        else:
            st["progress"] = tiles_frac
        if st["phase"] == "done":
            st["progress"] = 1.0

        # ETA from observed throughput so far, which beats a fixed per-tile guess.
        if st["progress"] > 0.01 and self.running:
            st["eta"] = st["elapsed"] / st["progress"] - st["elapsed"]
        else:
            st["eta"] = None

        st["ready"] = bool(self.out_path and self.out_path.exists())
        st["out_name"] = self.out_path.name if self.out_path else None
        return st


JOB = Job()

PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Prospector</title>
<style>
  :root{--bg:#fff;--fg:#16181d;--mut:#666e7a;--line:#e3e6ea;--acc:#2f6df6;--ok:#12855b;--err:#c0392b;--card:#f7f8fa}
  @media(prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#e9ecf1;--mut:#98a1ad;--line:#2a2e36;--acc:#6a9bff;--ok:#35c48c;--err:#ff7a6b;--card:#1b1e24}}
  *{box-sizing:border-box}
  body{margin:0;padding:2rem 1rem;background:var(--bg);color:var(--fg);
       font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
  .wrap{max-width:660px;margin:0 auto}
  h1{font-size:1.3rem;margin:0 0 .25rem}
  p.sub{color:var(--mut);margin:0 0 1.75rem}
  fieldset{border:1px solid var(--line);border-radius:10px;padding:1.1rem;margin:0 0 1rem}
  legend{padding:0 .4rem;color:var(--mut);font-size:.8rem;text-transform:uppercase;letter-spacing:.06em}
  label{display:block;margin:.7rem 0 .25rem;font-size:.85rem;color:var(--mut)}
  input[type=text],input[type=number]{width:100%;padding:.55rem .7rem;border:1px solid var(--line);
       border-radius:7px;background:var(--bg);color:var(--fg);font:inherit;font-size:.9rem}
  .row{display:flex;gap:.75rem}.row>div{flex:1}
  .chk{display:flex;align-items:center;gap:.5rem;margin:.6rem 0;font-size:.9rem;color:var(--fg)}
  .chk input{margin:0}
  button{padding:.6rem 1.1rem;border:0;border-radius:7px;background:var(--acc);color:#fff;
         font:inherit;font-weight:600;cursor:pointer}
  button.ghost{background:transparent;color:var(--mut);border:1px solid var(--line)}
  button:disabled{opacity:.45;cursor:not-allowed}
  .bar{height:9px;background:var(--line);border-radius:5px;overflow:hidden;margin:.9rem 0 .6rem}
  .bar>i{display:block;height:100%;background:var(--acc);width:0;transition:width .4s ease}
  .bar.done>i{background:var(--ok)}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.6rem;margin:1rem 0}
  .tile{background:var(--card);border-radius:8px;padding:.6rem .7rem}
  .tile b{display:block;font-size:1.15rem;font-variant-numeric:tabular-nums}
  .tile span{font-size:.72rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
  .status{display:flex;justify-content:space-between;align-items:baseline;font-size:.88rem}
  .status .ph{font-weight:600}
  .mut{color:var(--mut)}
  pre{background:var(--card);border-radius:8px;padding:.7rem .8rem;font-size:.75rem;
      overflow-x:auto;max-height:150px;color:var(--mut);margin:.8rem 0 0}
  .err{color:var(--err);white-space:pre-wrap;font-size:.85rem;margin-top:.7rem}
  a.dl{display:inline-block;margin-top:.9rem;padding:.6rem 1.1rem;background:var(--ok);
       color:#fff;text-decoration:none;border-radius:7px;font-weight:600}
  #panel{display:none}
</style>
<div class="wrap">
  <h1>Places prospector</h1>
  <p class="sub">Runs locally. Closing this tab will not stop a run.</p>

  <form id="f">
    <fieldset>
      <legend>Search</legend>
      <label>Query</label>
      <input type="text" name="query" value="window cleaning" required>
      <label>Metro centers file <span class="mut">— leave blank to use a single center</span></label>
      <input type="text" name="centers_file" value="tools/metros-us-top25.txt">
      <label>Single center <span class="mut">— "lat,lon", used only if the file above is blank</span></label>
      <input type="text" name="center" placeholder="33.4484,-112.0740">
      <div class="row">
        <div><label>Radius km</label><input type="number" name="radius_km" value="40" step="1"></div>
        <div><label>Tile km</label><input type="number" name="tile_km" value="8" step="1"></div>
      </div>
      <label>Output CSV</label>
      <input type="text" name="out" value="window_cleaners.csv">
    </fieldset>
    <fieldset>
      <legend>Options</legend>
      <div class="chk"><input type="checkbox" name="enrich_emails" id="e" checked><label for="e" style="margin:0">Scrape websites for emails <span class="mut">(slow — adds hours)</span></label></div>
      <div class="chk"><input type="checkbox" name="emails_only" id="o"><label for="o" style="margin:0">Emails-only CSV</label></div>
      <div class="chk"><input type="checkbox" name="restart" id="r"><label for="r" style="margin:0">Ignore checkpoint and start over</label></div>
    </fieldset>
    <button id="go">Start run</button>
    <button type="button" class="ghost" id="stop" disabled>Stop</button>
  </form>

  <div id="panel">
    <fieldset style="margin-top:1.25rem">
      <legend>Progress</legend>
      <div class="status">
        <span class="ph" id="phase">—</span>
        <span class="mut"><span id="clock">0:00</span> elapsed · <span id="eta">—</span></span>
      </div>
      <div class="bar" id="bar"><i id="fill"></i></div>
      <div class="grid">
        <div class="tile"><b id="m-tiles">0</b><span>tiles</span></div>
        <div class="tile"><b id="m-biz">0</b><span>businesses</span></div>
        <div class="tile"><b id="m-scan">0</b><span>sites read</span></div>
        <div class="tile"><b id="m-mail">0</b><span>emails</span></div>
      </div>
      <div class="err" id="err"></div>
      <a class="dl" id="dl" href="/api/download" style="display:none">Download CSV</a>
      <pre id="log"></pre>
    </fieldset>
  </div>
</div>
<script>
const $ = id => document.getElementById(id);
const hhmm = s => { s=Math.max(0,Math.round(s));
  const h=Math.floor(s/3600), m=Math.floor(s%3600/60), x=s%60;
  return h ? `${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`
           : `${m}:${String(x).padStart(2,'0')}`; };

$('f').onsubmit = async ev => {
  ev.preventDefault();
  const fd = new FormData(ev.target), body = {};
  for (const [k,v] of fd.entries()) body[k] = v;
  ['enrich_emails','emails_only','restart'].forEach(k => body[k] = fd.has(k));
  $('go').disabled = true; $('err').textContent = '';
  const r = await fetch('/api/start', {method:'POST', body:JSON.stringify(body)});
  if (!r.ok) { $('err').textContent = await r.text(); $('go').disabled = false; return; }
  $('panel').style.display = 'block';
  poll();
};
$('stop').onclick = () => fetch('/api/stop', {method:'POST'});

async function poll(){
  let s;
  try { s = await (await fetch('/api/status')).json(); } catch { setTimeout(poll,2000); return; }
  if (!s.started) { setTimeout(poll,2000); return; }
  $('panel').style.display = 'block';

  const labels = {searching:'Searching Places', emails:'Reading websites',
                  writing:'Writing CSV', done:'Finished', error:'Failed', idle:'Idle'};
  $('phase').textContent = labels[s.phase] || s.phase;
  $('clock').textContent = hhmm(s.elapsed);
  $('eta').textContent = s.eta ? hhmm(s.eta)+' left' : (s.running ? 'estimating…' : 'done');
  $('fill').style.width = (100*(s.progress||0)).toFixed(1)+'%';
  $('bar').className = 'bar' + (s.phase==='done' ? ' done' : '');
  $('m-tiles').textContent = s.tiles_done + '/' + s.tiles_total;
  $('m-biz').textContent   = s.businesses;
  $('m-scan').textContent  = s.scraped + (s.sites_total ? '/'+s.sites_total : '');
  $('m-mail').textContent  = s.emails;
  $('log').textContent = (s.log||[]).join('\\n');
  $('err').textContent = s.error || '';
  $('go').disabled = s.running;
  $('stop').disabled = !s.running;
  $('dl').style.display = s.ready ? 'inline-block' : 'none';
  if (s.running) setTimeout(poll, 2000);
}
poll();
</script>
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass  # the prospector's own output is the interesting log

    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, PAGE, "text/html; charset=utf-8")
        if path == "/api/status":
            return self._send(200, json.dumps(JOB.status()))
        if path == "/api/download":
            out = JOB.out_path
            if not out or not out.exists():
                return self._send(404, "no CSV yet", "text/plain")
            data = out.read_bytes()
            return self._send(
                200,
                data,
                "text/csv",
                {"Content-Disposition": f'attachment; filename="{out.name}"'},
            )
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/stop":
            JOB.stop()
            return self._send(200, json.dumps({"ok": True}))
        if path == "/api/start":
            length = int(self.headers.get("Content-Length", 0))
            try:
                params = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, "bad JSON", "text/plain")
            if not params.get("query"):
                return self._send(400, "query is required", "text/plain")
            try:
                JOB.start(params)
            except Exception as exc:
                return self._send(400, str(exc), "text/plain")
            return self._send(200, json.dumps({"ok": True}))
        self._send(404, "not found", "text/plain")


def main():
    ap = argparse.ArgumentParser(description="Local UI for the Places prospector.")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help="loopback by default; anything else exposes an unauthenticated "
        "endpoint that spends your Places quota",
    )
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument(
        "--display-url",
        help="address to print and open, when it differs from the bind address "
        "(ChromeOS reaches the Linux container by hostname, not loopback)",
    )
    args = ap.parse_args()

    if not os.environ.get("GOOGLE_PLACES_API_KEY"):
        print("warning: GOOGLE_PLACES_API_KEY is not set; runs will fail", file=sys.stderr)

    # ChromeOS puts the Linux container behind its own NAT, so binding wide
    # there exposes the server to the browser rather than to the network.
    on_crostini = Path("/dev/.cros_milestone").exists()
    if args.host not in ("127.0.0.1", "localhost") and not on_crostini:
        print(
            f"warning: binding to {args.host} — this server has no authentication, "
            "and anyone who can reach it can spend your API quota",
            file=sys.stderr,
        )

    url = args.display_url or f"http://{args.host}:{args.port}"
    print(f"prospector UI on {url}   (ctrl-c to quit)", file=sys.stderr)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        JOB.stop()
        print("\nstopped", file=sys.stderr)


if __name__ == "__main__":
    main()
