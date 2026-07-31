"""Tiny stdlib web server: serves the frontend and a /api/discounts endpoint.

    python3 server.py            # then open http://localhost:8000
    python3 server.py --port 9000

No external dependencies. Results are cached in memory per country code with a
TTL so refreshing the page doesn't hammer Steam.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import steam

FRONTEND_DIR = Path(__file__).parent / "frontend"
CACHE_TTL = 1800  # seconds
DEMO = False  # set by --demo: serve built-in sample data, never touch the network

_cache: dict[str, tuple[float, list[dict]]] = {}
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()

_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def get_discounts(cc: str, refresh: bool = False) -> list[dict]:
    now = time.time()
    if not refresh:
        hit = _cache.get(cc)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    # Serialize concurrent fetches for the same cc so we fetch once, not N times.
    with _lock_for(cc):
        hit = _cache.get(cc)
        if hit and not refresh and time.time() - hit[0] < CACHE_TTL:
            return hit[1]
        games = steam.fetch_discounts(cc=cc)
        _cache[cc] = (time.time(), games)
        return games


class Handler(BaseHTTPRequestHandler):
    server_version = "SteamDiscounts/1.0"

    def log_message(self, fmt, *args):  # quieter logging
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, rel: str):
        rel = rel.lstrip("/") or "index.html"
        path = (FRONTEND_DIR / rel).resolve()
        if not str(path).startswith(str(FRONTEND_DIR.resolve())) or not path.is_file():
            self.send_error(404, "Not found")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         _CONTENT_TYPES.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/discounts":
            self._handle_api(parse_qs(parsed.query))
            return
        if parsed.path == "/" or parsed.path == "":
            self._serve_static("index.html")
            return
        self._serve_static(parsed.path)

    def _handle_api(self, q: dict):
        cc = (q.get("cc", ["us"])[0] or "us").lower()
        refresh = q.get("refresh", ["0"])[0] in ("1", "true", "yes")
        try:
            min_pct = int(q.get("min", ["0"])[0])
        except ValueError:
            min_pct = 0
        try:
            limit = int(q.get("limit", ["0"])[0])
        except ValueError:
            limit = 0

        demo = DEMO or q.get("demo", ["0"])[0] in ("1", "true", "yes")
        if demo:
            games = steam.demo_discounts(cc)
            self._respond(games, cc, min_pct, limit, demo=True)
            return

        try:
            games = get_discounts(cc, refresh=refresh)
        except steam.SteamBlockedError as exc:
            self._send_json({"error": "blocked", "message": str(exc)}, status=502)
            return
        except Exception as exc:  # noqa: BLE001 - surface any fetch failure to UI
            self._send_json({"error": "fetch_failed", "message": str(exc)}, status=502)
            return

        self._respond(games, cc, min_pct, limit)

    def _respond(self, games, cc, min_pct, limit, demo=False):
        filtered = [g for g in games if g["discount_percent"] >= min_pct]
        if limit:
            filtered = filtered[:limit]
        ts = time.time() if demo else _cache.get(cc, (time.time(), None))[0]
        self._send_json(
            {
                "cc": cc,
                "demo": demo,
                "updated": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts)),
                "count": len(filtered),
                "total_available": len(games),
                "items": filtered,
            }
        )


def main(argv=None):
    p = argparse.ArgumentParser(description="Serve the Steam discounts UI.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--demo", action="store_true",
                   help="serve built-in sample data (no network needed)")
    args = p.parse_args(argv)

    global DEMO
    DEMO = args.demo

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Steam Discounts running at {url}  (Ctrl+C to stop)")
    if DEMO:
        print("DEMO MODE: showing built-in sample data (not live Steam data).")
    else:
        print("First load fetches from Steam and may take ~10-30s; results are cached.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
        httpd.shutdown()


if __name__ == "__main__":
    main()
