# Steam Discounts

Fetch every Steam game currently on sale, sorted by discount %, with a web page to browse them.

Pure Python **standard library** — no `pip install`, no dependencies. Just `python3`.

## Requirements

- **Python 3.7+** (uses `http.server.ThreadingHTTPServer`) — check with `python3 --version`.
- Nothing else. No virtualenv, no packages.
- Network access to `store.steampowered.com` (see [Network note](#network-note-important-on-corporate-machines) if you're behind a corporate proxy).

## Quick start

```bash
cd steam-discounts
python3 server.py                 # start the web app, then open http://localhost:8000
```

No network / just want to see the UI?

```bash
python3 server.py --demo          # built-in sample data; open http://localhost:8000
```

## Project layout

```
steam-discounts/
├── steam.py            # core: fetch + parse Steam discounts (also a CLI)
├── server.py           # tiny stdlib web server: API + serves the frontend
└── frontend/
    ├── index.html      # the page
    ├── style.css       # Steam-ish dark theme
    └── app.js          # filtering / sorting / region switch (client-side)
```

## Run the web app

```bash
cd steam-discounts
python3 server.py                       # default: http://localhost:8000
python3 server.py --port 9000           # custom port
python3 server.py --host 0.0.0.0        # listen on all interfaces (LAN access)
python3 server.py --demo                # serve built-in sample data (no network)
```

| Flag       | Default     | Meaning                                          |
| ---------- | ----------- | ------------------------------------------------ |
| `--host`   | `127.0.0.1` | Bind address (`0.0.0.0` to expose on the LAN)    |
| `--port`   | `8000`      | Port to listen on                                |
| `--demo`   | off         | Serve built-in sample data instead of live fetch |

- First load fetches from Steam (~10–30s) and **caches** the result in memory for 30 min.
- The page lets you: filter by name, change **region** (US/UK/DE/CN/JP/…), re-sort
  (discount ↑↓, price ↑↓, name), set a **min-discount** slider, and **↻ Refresh** (bypasses cache).

## Command line

`steam.py` works standalone — print a table, or export JSON/CSV:

```bash
python3 steam.py                       # human-readable table (default region = us)
python3 steam.py --cc uk --min 50      # UK prices, only 50%+ off
python3 steam.py --limit 20            # top 20 by discount
python3 steam.py --json > deals.json   # JSON, sorted by discount desc
python3 steam.py --csv  > deals.csv    # spreadsheet-friendly
python3 steam.py --max-pages 0         # no page cap: truly *all* discounts
python3 steam.py --demo                # built-in sample data (no network)
```

| Flag           | Default    | Meaning                                                             |
| -------------- | ---------- | ------------------------------------------------------------------- |
| `--cc`         | `us`       | Country/currency code (`us`, `uk`, `de`, `cn`, `jp`, `ru`, `br`, …) |
| `--lang`       | `english`  | Steam store language                                                |
| `--min`        | `0`        | Minimum discount % to include                                       |
| `--limit`      | (all)      | Max number of rows to output                                        |
| `--max-pages`  | `40`       | Paging cap (40 × 100 = 4000 games); `0` = unlimited                 |
| `--source`     | `search`   | `search` = all specials, `featured` = featured-specials only        |
| `--json`       | off        | Output JSON instead of a table                                      |
| `--csv`        | off        | Output CSV instead of a table                                       |
| `--demo`       | off        | Use built-in sample data instead of a live fetch                    |

## HTTP API

The server exposes one JSON endpoint (handy for scripting):

```
GET /api/discounts
```

| Query param | Example | Meaning                                        |
| ----------- | ------- | ---------------------------------------------- |
| `cc`        | `uk`    | Region / currency (default `us`)               |
| `min`       | `50`    | Minimum discount %                             |
| `limit`     | `100`   | Max rows returned                              |
| `refresh`   | `1`     | Bypass the 30-min cache and re-fetch           |
| `demo`      | `1`     | Return built-in sample data                    |

```bash
curl 'http://localhost:8000/api/discounts?cc=uk&min=50&limit=20'
curl 'http://localhost:8000/api/discounts?demo=1'
```

Response shape:

```json
{
  "cc": "us",
  "demo": false,
  "count": 123,
  "games": [
    {
      "appid": "1245620",
      "name": "ELDEN RING",
      "discount_percent": 30,
      "original_price": "$59.99",
      "final_price": "$41.99",
      "final_price_value": 41.99,
      "url": "https://store.steampowered.com/app/1245620/",
      "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg"
    }
  ]
}
```

## Demo mode (no network)

To see the UI without reaching Steam (e.g. on a network that blocks it):

```bash
python3 server.py --demo      # serves built-in sample data; open http://localhost:8000
python3 steam.py --demo       # same data on the command line
```

The page shows a `⚠ DEMO data (not live)` tag so it's never mistaken for real prices.
You can also hit the API directly with `?demo=1` (e.g. `/api/discounts?demo=1`).

## How it works

- **Data source:** Steam's public store search endpoint with `specials=1`
  (`store.steampowered.com/search/results/`), paged 100 at a time until Steam's
  reported `total_count` is exhausted. This covers *all* games on sale, not just
  the handful in the "featured specials" widget.
- The response is JSON whose `results_html` field holds row markup; `steam.py`
  parses it defensively with several fallback regexes so minor Steam markup
  changes don't break extraction. Prices are kept as display strings **and** a
  parsed numeric value (for sorting across currency formats).
- `--source featured` uses the all-JSON `featuredcategories` endpoint instead —
  smaller and more stable, but only the featured specials.

## Network note (important on corporate machines)

Steam must be reachable from wherever the server/CLI runs.

- On this workspace's WSL box, **Steam is blocked by corporate Zscaler policy**
  (category block), so a live fetch here returns a block page / HTTP 403. Run it
  on an unrestricted network (home machine, personal laptop) and it works.
- If you're behind a **TLS-intercepting proxy** (Zscaler et al.) but Steam *is*
  allowed, point the tool at your corporate CA bundle so TLS verifies:

  ```bash
  export STEAM_CA_BUNDLE=~/zscaler-ca-bundle.pem   # or SSL_CERT_FILE
  ```

  (`~/zscaler-ca-bundle.pem` is auto-detected if present.) You can also set the
  standard `HTTPS_PROXY` env var.

The tool detects these cases and returns a clear message instead of a stack trace.

## Notes / limits

- Prices and discounts are Steam's own values for the selected region.
- Region-locked or unreleased titles may not appear for every `cc`.
- Not affiliated with Valve; this only reads Steam's public store endpoints.
