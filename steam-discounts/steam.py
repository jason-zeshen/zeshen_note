"""Fetch currently-discounted Steam games and sort them by discount.

Pure standard library — no external dependencies. Works as an importable
module (``fetch_discounts``) and as a CLI:

    python3 steam.py --cc us --min 50 --json > out.json
    python3 steam.py --cc us --csv  > out.csv
    python3 steam.py --limit 40                # human-readable table

Data source: Steam's public store search endpoint with ``specials=1``, which
paginates through *every* game currently on sale (not just the featured few).
The response is JSON whose ``results_html`` field holds the row markup, which
we parse defensively with regexes so small markup changes don't break us.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SEARCH_URL = "https://store.steampowered.com/search/results/"
FEATURED_URL = "https://store.steampowered.com/api/featuredcategories"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


class SteamBlockedError(RuntimeError):
    """Raised when the network can't reach Steam (block page, TLS interception, etc.)."""


def _ssl_context() -> ssl.SSLContext:
    """SSL context that honors a custom CA bundle.

    Useful behind a TLS-intercepting proxy (e.g. Zscaler): point
    ``STEAM_CA_BUNDLE`` or ``SSL_CERT_FILE`` at the corporate CA bundle, or
    drop it at ``~/zscaler-ca-bundle.pem`` and it's picked up automatically.
    """
    bundle = os.environ.get("STEAM_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
    if not bundle:
        default = Path.home() / "zscaler-ca-bundle.pem"
        if default.is_file():
            bundle = str(default)
    if bundle and Path(bundle).is_file():
        return ssl.create_default_context(cafile=bundle)
    return ssl.create_default_context()


_SSL_CTX = _ssl_context()


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _http_get(url: str, params: dict | None = None, timeout: int = 25) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raise SteamBlockedError(
            f"Steam returned HTTP {exc.code}. It may be rate-limiting or "
            f"blocking this request. Try again shortly."
        ) from exc
    except ssl.SSLError as exc:
        raise SteamBlockedError(
            "TLS verification to Steam failed — likely a TLS-intercepting proxy "
            "(e.g. Zscaler). Point STEAM_CA_BUNDLE at your corporate CA bundle "
            f"(detail: {exc})."
        ) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in str(reason):
            raise SteamBlockedError(
                "TLS verification to Steam failed — likely a TLS-intercepting proxy "
                "(e.g. Zscaler). Set STEAM_CA_BUNDLE to your corporate CA bundle, "
                "or run on an unrestricted network."
            ) from exc
        raise SteamBlockedError(
            f"Could not reach Steam ({reason}). Check your network/proxy, or "
            f"whether Steam is blocked here."
        ) from exc

    text = raw.decode("utf-8", errors="replace")
    # Corporate proxies (e.g. Zscaler) may return a 200 page that isn't Steam.
    lowered = text[:4000].lower()
    if "zscaler" in lowered or "internet security by" in lowered:
        raise SteamBlockedError(
            "The network returned a proxy/block page instead of Steam. "
            "Steam appears to be blocked here (corporate policy). "
            "Run this on an unrestricted network, or set HTTPS_PROXY."
        )
    return text


# ---------------------------------------------------------------------------
# Parsing the search results HTML
# ---------------------------------------------------------------------------
# Split *before* each row anchor (lookahead) so the opening <a href=...> tag
# stays inside the chunk and we can still read the href.
_ROW_SPLIT = re.compile(r'(?=<a\s+[^>]*class="[^"]*search_result_row)', re.IGNORECASE)

_RE_APPID = re.compile(r'data-ds-appid="(\d+)"')
_RE_HREF = re.compile(r'href="([^"]+)"')
_RE_NAME = re.compile(r'<span class="title">(.*?)</span>', re.DOTALL)
_RE_IMG = re.compile(r'<img[^>]+src="([^"]+)"')
# Discount percent shows up a few different ways across Steam markup revisions.
_RE_DISCOUNT = [
    re.compile(r'discount_pct[^>]*>\s*-?\s*(\d+)\s*%'),
    re.compile(r'search_discount[^>]*>\s*<span>\s*-?\s*(\d+)\s*%'),
    re.compile(r'-\s*(\d+)\s*%\s*</div>'),
]
_RE_ORIG = [
    re.compile(r'discount_original_price[^>]*>(.*?)</div>', re.DOTALL),
    re.compile(r'<strike>(.*?)</strike>', re.DOTALL),
    re.compile(r'strikethrough[^>]*>(.*?)</span>', re.DOTALL),
]
_RE_FINAL = [
    re.compile(r'discount_final_price[^>]*>(.*?)</div>', re.DOTALL),
]
# Older layout: <div class="col search_price discounted ..."><strike>orig</strike><br>final</div>
# Require a space/quote after "search_price" so we don't match search_price_discount_combined.
_RE_SEARCH_PRICE = re.compile(r'search_price[ "][^>]*>(.*?)</div>', re.DOTALL)
_RE_STRIKE = re.compile(r'<strike>.*?</strike>', re.DOTALL)
_RE_TAGS = re.compile(r'<[^>]+>')


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _RE_TAGS.sub("", text)
    text = html.unescape(text)
    return " ".join(text.split()).strip()


def _first(patterns, chunk: str) -> str | None:
    for pat in patterns:
        m = pat.search(chunk)
        if m:
            return m.group(1)
    return None


def _extract_prices(chunk: str) -> tuple[str, str]:
    """Return (original, final) display prices, handling both Steam layouts."""
    original = _clean(_first(_RE_ORIG, chunk))
    final = _clean(_first(_RE_FINAL, chunk))
    if not final:
        m = _RE_SEARCH_PRICE.search(chunk)
        if m:
            block = m.group(1)
            # Drop the struck-through original; what remains is the final price.
            final = _clean(_RE_STRIKE.sub("", block))
    return original, final


def _price_to_float(price: str) -> float | None:
    """Best-effort numeric value from a display price like '$9.99' or '9,99€'."""
    if not price:
        return None
    if re.search(r"free", price, re.IGNORECASE):
        return 0.0
    digits = re.sub(r"[^\d.,]", "", price)
    if not digits:
        return None
    # If both separators present, the last one is the decimal separator.
    if "," in digits and "." in digits:
        if digits.rfind(",") > digits.rfind("."):
            digits = digits.replace(".", "").replace(",", ".")
        else:
            digits = digits.replace(",", "")
    elif "," in digits:
        # Assume comma is the decimal separator (EU) if it looks like one.
        if re.match(r"^\d{1,3},\d{2}$", digits):
            digits = digits.replace(",", ".")
        else:
            digits = digits.replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return None


def _parse_rows(results_html: str) -> list[dict]:
    parts = _ROW_SPLIT.split(results_html)
    games: list[dict] = []
    seen: set[str] = set()
    # parts[0] is whatever preceded the first row; each later part is one row body.
    for chunk in parts[1:]:
        appid = _first([_RE_APPID], chunk)
        discount_raw = _first(_RE_DISCOUNT, chunk)
        if discount_raw is None:
            continue  # no discount on this row
        discount = int(discount_raw)
        if discount <= 0:
            continue
        key = appid or _clean(_first([_RE_NAME], chunk))
        if key in seen:
            continue
        seen.add(key)

        name = _clean(_first([_RE_NAME], chunk))
        href = _first([_RE_HREF], chunk)
        img = _first([_RE_IMG], chunk)
        original, final = _extract_prices(chunk)

        games.append(
            {
                "appid": int(appid) if appid and appid.isdigit() else None,
                "name": name or "(unknown)",
                "discount_percent": discount,
                "original_price": original,
                "final_price": final,
                "final_price_value": _price_to_float(final),
                "url": html.unescape(href) if href else None,
                "image": html.unescape(img) if img else None,
            }
        )
    return games


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def fetch_discounts(
    cc: str = "us",
    lang: str = "english",
    page_size: int = 100,
    max_pages: int = 40,
    sleep: float = 0.4,
    progress=None,
) -> list[dict]:
    """Return all currently-discounted games, sorted by discount desc.

    ``max_pages`` caps how far we page (page_size games per page). Raise it or
    set it to 0 for "no cap" if you truly want every last title.
    """
    games: list[dict] = []
    seen: set = set()
    start = 0
    page = 0
    total = None
    while True:
        params = {
            "query": "",
            "start": start,
            "count": page_size,
            "specials": 1,
            "infinite": 1,
            "cc": cc,
            "l": lang,
        }
        text = _http_get(SEARCH_URL, params)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SteamBlockedError(
                "Steam search returned non-JSON (likely a block/redirect page)."
            ) from exc

        total = payload.get("total_count", total)
        rows = _parse_rows(payload.get("results_html", "") or "")
        added = 0
        for g in rows:
            k = g["appid"] or g["name"]
            if k in seen:
                continue
            seen.add(k)
            games.append(g)
            added += 1

        page += 1
        if progress:
            progress(page, len(games), total)

        start += page_size
        # Stop when: no new rows, exhausted the reported total, or hit the cap.
        if added == 0:
            break
        if total is not None and start >= total:
            break
        if max_pages and page >= max_pages:
            break
        time.sleep(sleep)

    games.sort(
        key=lambda g: (
            -g["discount_percent"],
            g["final_price_value"] if g["final_price_value"] is not None else 1e12,
            g["name"].lower(),
        )
    )
    return games


# (appid, name, discount %, original price in USD)
_DEMO_RAW = [
    (1245620, "ELDEN RING", 30, 59.99),
    (1091500, "Cyberpunk 2077", 50, 59.99),
    (1174180, "Red Dead Redemption 2", 67, 59.99),
    (292030, "The Witcher 3: Wild Hunt", 80, 39.99),
    (271590, "Grand Theft Auto V", 63, 29.99),
    (1086940, "Baldur's Gate 3", 20, 59.99),
    (1145360, "Hades", 55, 24.99),
    (413150, "Stardew Valley", 25, 14.99),
    (105600, "Terraria", 66, 9.99),
    (367520, "Hollow Knight", 50, 14.99),
    (620, "Portal 2", 90, 9.99),
    (782330, "DOOM Eternal", 75, 39.99),
    (814380, "Sekiro: Shadows Die Twice", 40, 59.99),
    (632470, "Disco Elysium - The Final Cut", 85, 39.99),
    (588650, "Dead Cells", 50, 24.99),
    (1817070, "Marvel's Spider-Man Remastered", 45, 59.99),
]


def demo_discounts(cc: str = "us") -> list[dict]:
    """Static sample data so the UI can be demoed without reaching Steam."""
    out = []
    for appid, name, pct, original in _DEMO_RAW:
        final = round(original * (100 - pct) / 100, 2)
        out.append(
            {
                "appid": appid,
                "name": name,
                "discount_percent": pct,
                "original_price": f"${original:.2f}",
                "final_price": f"${final:.2f}",
                "final_price_value": final,
                "url": f"https://store.steampowered.com/app/{appid}/",
                "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg",
            }
        )
    out.sort(key=lambda g: (-g["discount_percent"], g["final_price_value"]))
    return out


def fetch_featured(cc: str = "us", lang: str = "english") -> list[dict]:
    """Smaller, all-JSON alternative: Steam's 'specials' featured category."""
    text = _http_get(FEATURED_URL, {"cc": cc, "l": lang})
    data = json.loads(text)
    items = (data.get("specials") or {}).get("items", [])
    out = []
    for it in items:
        if not it.get("discounted"):
            continue
        out.append(
            {
                "appid": it.get("id"),
                "name": it.get("name", "(unknown)"),
                "discount_percent": it.get("discount_percent", 0),
                "original_price": f"{(it.get('original_price') or 0) / 100:.2f}",
                "final_price": f"{(it.get('final_price') or 0) / 100:.2f}",
                "final_price_value": (it.get("final_price") or 0) / 100,
                "url": f"https://store.steampowered.com/app/{it.get('id')}/",
                "image": it.get("header_image") or it.get("large_capsule_image"),
            }
        )
    out.sort(key=lambda g: -g["discount_percent"])
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fetch Steam discounts, sorted by %.")
    p.add_argument("--cc", default="us", help="country/currency code (us, uk, de, cn, jp...)")
    p.add_argument("--lang", default="english")
    p.add_argument("--min", type=int, default=0, help="minimum discount percent")
    p.add_argument("--limit", type=int, default=0, help="max games to output (0 = all)")
    p.add_argument("--max-pages", type=int, default=40, help="page cap (0 = no cap)")
    p.add_argument("--source", choices=["search", "featured"], default="search")
    p.add_argument("--demo", action="store_true",
                   help="use built-in sample data (no network)")
    p.add_argument("--json", action="store_true", help="emit JSON")
    p.add_argument("--csv", action="store_true", help="emit CSV")
    args = p.parse_args(argv)

    def progress(page, count, total):
        print(f"  page {page}: {count} discounted games so far"
              f"{f' (of ~{total} results)' if total else ''}...",
              file=sys.stderr)

    try:
        if args.demo:
            games = demo_discounts(args.cc)
        elif args.source == "featured":
            games = fetch_featured(args.cc, args.lang)
        else:
            games = fetch_discounts(args.cc, args.lang,
                                    max_pages=args.max_pages, progress=progress)
    except SteamBlockedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.min:
        games = [g for g in games if g["discount_percent"] >= args.min]
    if args.limit:
        games = games[: args.limit]

    if args.json:
        json.dump(games, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["discount_%", "name", "original", "final", "appid", "url"])
        for g in games:
            w.writerow([g["discount_percent"], g["name"], g["original_price"],
                        g["final_price"], g["appid"], g["url"]])
    else:
        print(f"\n{len(games)} discounted games (cc={args.cc}):\n")
        for g in games:
            print(f"  -{g['discount_percent']:>3}%  "
                  f"{(g['final_price'] or '?'):>8}  "
                  f"(was {g['original_price'] or '?'})  {g['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
