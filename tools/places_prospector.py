#!/usr/bin/env python3
"""
Pull local businesses from the Google Places API (New) into a CSV.

A single Places text search caps at 60 results, so covering a metro means
tiling it: lay a grid of overlapping circles over the target area, search each
one, and dedupe by place ID. That is what --radius-km and --tile-km control.

Places does not return email addresses. --enrich-emails visits each business
website afterwards and pulls contact addresses out of the HTML.

Long runs checkpoint as they go. Every finished tile and every scraped site is
appended to a state directory, so re-running the same command picks up where it
left off instead of starting over. Delete the state directory to force a fresh
run, or pass --restart.

    export GOOGLE_PLACES_API_KEY=...
    python3 tools/places_prospector.py \
        --query "window cleaning" \
        --center 33.4484,-112.0740 \
        --radius-km 60 \
        --out window_cleaners_phoenix.csv

Every metro, emails only:

    python3 tools/places_prospector.py \
        --query "window cleaning" \
        --centers-file tools/metros-us-top25.txt \
        --out window_cleaners.csv --enrich-emails --emails-only
"""

import argparse
import csv
import html
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Ask only for the fields we write out. The field mask drives billing tier, so
# adding fields here costs money on every call.
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.businessStatus",
        "places.primaryTypeDisplayName",
        "places.googleMapsUri",
        "places.location",
        "nextPageToken",
    ]
)

CSV_COLUMNS = [
    "place_id",
    "name",
    "address",
    "phone",
    "website",
    "email",
    "all_emails",
    "rating",
    "review_count",
    "business_status",
    "category",
    "maps_url",
    "latitude",
    "longitude",
    "source_tile",
]

EARTH_KM_PER_DEG_LAT = 110.574

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# "info [at] example [dot] com" and friends, which small business sites use to
# dodge naive scrapers. Worth handling; it is a meaningful slice of the misses.
OBFUSCATED_RE = re.compile(
    r"([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\{at\}|\s+at\s+|&#64;|%40)\s*"
    r"([A-Za-z0-9.-]+?)\s*(?:\[dot\]|\(dot\)|\{dot\}|\s+dot\s+|\.)\s*([A-Za-z]{2,})",
    re.IGNORECASE,
)

# Addresses that show up on nearly every site and are never the business.
EMAIL_NOISE = re.compile(
    r"(^|@)(example|sentry|wixpress|squarespace|godaddy|shopify|domain|yourdomain|"
    r"email|test|sample|no-?reply|donotreply|do-not-reply|privacy|abuse|postmaster)\.?",
    re.IGNORECASE,
)
EMAIL_NOISE_EXT = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|css|js|woff2?|ttf|ico|mp4|pdf)$", re.IGNORECASE
)
NOISE_DOMAINS = {
    "sentry.io",
    "wix.com",
    "wixpress.com",
    "squarespace.com",
    "godaddy.com",
    "shopify.com",
    "cloudflare.com",
    "example.com",
    "google.com",
    "facebook.com",
    "schema.org",
    "w3.org",
}

CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/contact.html",
    "/about",
    "/about-us",
    "/get-a-quote",
    "/quote",
    "/free-estimate",
    "/estimate",
    "/book",
]

CONTACT_LINK_RE = re.compile(
    r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.{0,80}?)</a>', re.IGNORECASE | re.DOTALL
)
CONTACT_WORDS = re.compile(r"contact|about|quote|estimate|reach|touch", re.IGNORECASE)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# --------------------------------------------------------------------------
# checkpoint state
# --------------------------------------------------------------------------


class RunState:
    """Append-only checkpoint so a killed run can resume.

    Three files, all JSON-lines so a partial write at the moment of a crash
    costs one record rather than the whole file:
      places.jsonl   every place row discovered
      tiles.done     one line per finished tile
      emails.jsonl   scrape result per place, including the empty ones
    """

    def __init__(self, state_dir):
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.places_path = self.dir / "places.jsonl"
        self.tiles_path = self.dir / "tiles.done"
        self.emails_path = self.dir / "emails.jsonl"
        self.places = {}
        self.done_tiles = set()
        self.scraped = {}

    def load(self):
        if self.places_path.exists():
            for line in self.places_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # torn final write from a hard kill
                self.places[row["place_id"]] = row
        if self.tiles_path.exists():
            self.done_tiles = {
                ln.strip()
                for ln in self.tiles_path.read_text(encoding="utf-8").splitlines()
                if ln.strip()
            }
        if self.emails_path.exists():
            for line in self.emails_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self.scraped[rec["place_id"]] = rec.get("emails", [])
        return self

    @staticmethod
    def _append(path, text):
        with path.open("a", encoding="utf-8") as fh:
            fh.write(text + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def add_place(self, row):
        if row["place_id"] in self.places:
            return False
        self.places[row["place_id"]] = row
        self._append(self.places_path, json.dumps(row))
        return True

    def finish_tile(self, key):
        self.done_tiles.add(key)
        self._append(self.tiles_path, key)

    def add_emails(self, place_id, emails):
        self.scraped[place_id] = emails
        self._append(self.emails_path, json.dumps({"place_id": place_id, "emails": emails}))


# --------------------------------------------------------------------------
# geo
# --------------------------------------------------------------------------


def build_grid(center_lat, center_lon, radius_km, tile_km):
    """Circle centers covering a radius_km disc, each searched at tile_km radius.

    Squares of side s inscribe in circles of radius s/sqrt(2), so stepping by
    tile_km * sqrt(2) tiles the plane with no gaps. Step slightly tighter to
    absorb the latitude distortion at the edges of a wide area.
    """
    step_km = tile_km * 1.35
    step_lat = step_km / EARTH_KM_PER_DEG_LAT
    lon_km_per_deg = EARTH_KM_PER_DEG_LAT * math.cos(math.radians(center_lat))
    if lon_km_per_deg < 1:  # near the poles; nothing sane to tile
        lon_km_per_deg = 1
    step_lon = step_km / lon_km_per_deg

    steps = int(math.ceil(radius_km / step_km))
    tiles = []
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            lat = center_lat + i * step_lat
            lon = center_lon + j * step_lon
            # Keep tiles whose center falls inside the requested disc, plus one
            # tile of slack so the boundary is covered rather than clipped.
            dx = (lon - center_lon) * lon_km_per_deg
            dy = (lat - center_lat) * EARTH_KM_PER_DEG_LAT
            if math.hypot(dx, dy) <= radius_km + tile_km:
                tiles.append((lat, lon))
    return tiles


# --------------------------------------------------------------------------
# places search
# --------------------------------------------------------------------------


# Configuration problems, not transient ones. Google reports an invalid key as
# HTTP 400 INVALID_ARGUMENT rather than a 401, so the reason has to be read out
# of the body; status code alone cannot tell these apart from a bad query.
FATAL_REASONS = {
    "API_KEY_INVALID": "the API key is not valid",
    "API_KEY_SERVICE_BLOCKED": "this key is not allowed to call the Places API",
    "API_KEY_HTTP_REFERRER_BLOCKED": "the key's referrer restriction blocks this caller",
    "API_KEY_IP_ADDRESS_BLOCKED": "the key's IP restriction blocks this machine",
    "SERVICE_DISABLED": "Places API (New) is not enabled on this Google Cloud project",
    "BILLING_DISABLED": "billing is not enabled on this Google Cloud project",
    "ACCESS_TOKEN_EXPIRED": "the credentials have expired",
}


def fatal_api_error(resp):
    """Return a human explanation if this error will repeat on every request."""
    try:
        err = resp.json().get("error", {})
    except ValueError:
        return None
    for detail in err.get("details", []):
        reason = detail.get("reason")
        if reason in FATAL_REASONS:
            return f"{FATAL_REASONS[reason]} ({reason})"
    if err.get("status") == "PERMISSION_DENIED":
        return f"permission denied: {err.get('message', '')[:200]}"
    return None


def search_tile(session, api_key, query, lat, lon, radius_km, max_pages, sleep_s):
    """Text search one tile, following pagination. Returns raw place dicts."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {
        "textQuery": query,
        "pageSize": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": min(radius_km * 1000, 50000),
            }
        },
    }

    places, token = [], None
    for _ in range(max_pages):
        if token:
            body["pageToken"] = token
        try:
            resp = session.post(SEARCH_URL, headers=headers, json=body, timeout=30)
        except requests.RequestException as exc:
            print(f"  ! network error: {exc}", file=sys.stderr)
            return places, False

        if resp.status_code == 429:
            print("  ! rate limited, backing off 10s", file=sys.stderr)
            time.sleep(10)
            continue
        if resp.status_code != 200:
            fatal = fatal_api_error(resp)
            if fatal:
                # A bad key or a disabled API fails identically on every tile,
                # so stop now rather than grinding through the whole grid.
                sys.exit(f"\nstopping: {fatal}")
            print(f"  ! HTTP {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
            return places, False

        data = resp.json()
        places.extend(data.get("places", []))
        token = data.get("nextPageToken")
        if not token:
            break
        # Places rejects a page token used too quickly after it is issued.
        time.sleep(max(sleep_s, 2.0))

    return places, True


def to_row(place, tile):
    loc = place.get("location") or {}
    return {
        "place_id": place.get("id", ""),
        "name": (place.get("displayName") or {}).get("text", ""),
        "address": place.get("formattedAddress", ""),
        "phone": place.get("nationalPhoneNumber")
        or place.get("internationalPhoneNumber", ""),
        "website": place.get("websiteUri", ""),
        "email": "",
        "all_emails": "",
        "rating": place.get("rating", ""),
        "review_count": place.get("userRatingCount", ""),
        "business_status": place.get("businessStatus", ""),
        "category": (place.get("primaryTypeDisplayName") or {}).get("text", ""),
        "maps_url": place.get("googleMapsUri", ""),
        "latitude": loc.get("latitude", ""),
        "longitude": loc.get("longitude", ""),
        "source_tile": f"{tile[0]:.4f},{tile[1]:.4f}",
    }


# --------------------------------------------------------------------------
# email extraction
# --------------------------------------------------------------------------


def decode_cf_email(hex_str):
    """Undo Cloudflare's email obfuscation.

    Cloudflare rewrites addresses to data-cfemail hex, where the first byte is
    an XOR key for the rest. Common on small business sites, so decoding it is
    worth the dozen lines.
    """
    try:
        data = bytes.fromhex(hex_str)
    except ValueError:
        return ""
    if len(data) < 2:
        return ""
    key = data[0]
    return "".join(chr(b ^ key) for b in data[1:])


def harvest(text):
    """Every address form we know how to read out of one page of HTML."""
    found = []

    for hex_str in re.findall(r'data-cfemail=["\']([0-9a-fA-F]+)["\']', text):
        decoded = decode_cf_email(hex_str)
        if decoded:
            found.append(decoded)

    # mailto: links are the highest-signal source, so they go in first.
    for raw in re.findall(r'mailto:([^"\'?>\s]+)', text, re.IGNORECASE):
        found.append(html.unescape(raw))

    for block in re.findall(
        r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        found.extend(EMAIL_RE.findall(block))

    unescaped = html.unescape(text)
    found.extend(EMAIL_RE.findall(unescaped))
    found.extend(f"{u}@{d}.{t}" for u, d, t in OBFUSCATED_RE.findall(unescaped))

    return found


def clean_emails(candidates, site_host):
    """Filter junk and sort so the business's own domain comes first."""
    root = site_host.lower().removeprefix("www.")
    keep = []
    for raw in candidates:
        addr = raw.strip().strip(".,;:()<>\"'").lower()
        addr = addr.split("?")[0]
        if addr.count("@") != 1 or len(addr) > 100 or len(addr) < 6:
            continue
        if EMAIL_NOISE.search(addr) or EMAIL_NOISE_EXT.search(addr):
            continue
        domain = addr.split("@")[1]
        if domain in NOISE_DOMAINS or "." not in domain:
            continue
        if addr not in keep:
            keep.append(addr)

    on_domain = [a for a in keep if a.split("@")[1] in (root, "www." + root)]
    off_domain = [a for a in keep if a not in on_domain]
    return on_domain + off_domain


def discover_contact_links(base_url, page_html, limit):
    """Follow the site's own contact/about links rather than only guessing paths."""
    base_host = urlparse(base_url).netloc
    out = []
    for href, label in CONTACT_LINK_RE.findall(page_html):
        if not CONTACT_WORDS.search(href) and not CONTACT_WORDS.search(label):
            continue
        url = urljoin(base_url, html.unescape(href.strip()))
        if urlparse(url).netloc != base_host:
            continue
        url = url.split("#")[0]
        if url not in out and url.rstrip("/") != base_url.rstrip("/"):
            out.append(url)
        if len(out) >= limit:
            break
    return out


def scrape_emails(session, website, timeout, sleep_s, max_pages):
    """Homepage first, then contact links it advertises, then guessed paths."""
    host = urlparse(website).netloc
    collected, visited = [], set()

    def fetch(url):
        if url in visited or len(visited) >= max_pages:
            return None
        visited.add(url)
        try:
            resp = session.get(
                url, headers=BROWSER_HEADERS, timeout=timeout, allow_redirects=True
            )
        except requests.RequestException:
            return None
        ctype = resp.headers.get("Content-Type", "")
        if resp.status_code != 200 or "html" not in ctype.lower():
            return None
        return resp.text

    home = fetch(website)
    if home:
        collected.extend(harvest(home))
        queue = discover_contact_links(website, home, limit=4)
    else:
        queue = []

    queue.extend(urljoin(website, p) for p in CONTACT_PATHS)

    for url in queue:
        if len(visited) >= max_pages:
            break
        page = fetch(url)
        if page:
            collected.extend(harvest(page))
        time.sleep(sleep_s)

    return clean_emails(collected, host)


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def parse_center(text):
    try:
        lat_s, lon_s = text.split(",")
        return float(lat_s.strip()), float(lon_s.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"center must look like '33.4484,-112.0740', got {text!r}"
        )


def load_centers(args):
    if args.centers_file:
        centers = []
        for line in Path(args.centers_file).read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                centers.append(parse_center(line))
        if not centers:
            sys.exit(f"no usable coordinates in {args.centers_file}")
        return centers
    if args.center:
        return [args.center]
    sys.exit("pass --center or --centers-file")


def write_output(state, args):
    rows = list(state.places.values())
    for row in rows:
        emails = state.scraped.get(row["place_id"], [])
        row["email"] = emails[0] if emails else ""
        row["all_emails"] = ";".join(emails)

    out_path = Path(args.out)
    if args.emails_only:
        seen, unique = set(), []
        for row in rows:
            for addr in state.scraped.get(row["place_id"], []):
                if addr not in seen:
                    seen.add(addr)
                    unique.append({"email": addr, "business": row["name"]})
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["email", "business"])
            writer.writeheader()
            writer.writerows(unique)
        return len(unique)

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(
        description="Pull local businesses from Google Places into a CSV."
    )
    ap.add_argument("--query", required=True, help='e.g. "window cleaning"')
    ap.add_argument("--center", type=parse_center, help='"lat,lon" of the metro')
    ap.add_argument("--centers-file", help='file of "lat,lon" lines, one per metro')
    ap.add_argument("--radius-km", type=float, default=40.0, help="area to cover")
    ap.add_argument("--tile-km", type=float, default=8.0, help="radius per search")
    ap.add_argument("--out", required=True, help="CSV output path")
    ap.add_argument("--max-pages", type=int, default=3, help="pages per tile (max 3)")
    ap.add_argument("--sleep", type=float, default=0.4, help="delay between calls")
    ap.add_argument("--enrich-emails", action="store_true", help="crawl sites for email")
    ap.add_argument(
        "--emails-only",
        action="store_true",
        help="write just the deduped addresses instead of the full record",
    )
    ap.add_argument("--email-timeout", type=float, default=10.0)
    ap.add_argument(
        "--pages-per-site", type=int, default=5, help="max pages fetched per website"
    )
    ap.add_argument("--state-dir", help="checkpoint dir (default: <out>.state)")
    ap.add_argument("--restart", action="store_true", help="ignore existing checkpoint")
    ap.add_argument("--search-only", action="store_true", help="skip the email stage")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        sys.exit("set GOOGLE_PLACES_API_KEY (Places API New must be enabled)")

    state_dir = args.state_dir or f"{args.out}.state"
    if args.restart and Path(state_dir).exists():
        for f in Path(state_dir).glob("*"):
            f.unlink()
    state = RunState(state_dir).load()
    if state.places or state.done_tiles:
        print(
            f"resuming: {len(state.places)} businesses, {len(state.done_tiles)} tiles "
            f"done, {len(state.scraped)} sites scraped",
            file=sys.stderr,
        )

    centers = load_centers(args)
    session = requests.Session()

    for c_idx, (lat, lon) in enumerate(centers, 1):
        tiles = build_grid(lat, lon, args.radius_km, args.tile_km)
        pending = [
            t for t in tiles if f"{args.query}|{t[0]:.4f},{t[1]:.4f}" not in state.done_tiles
        ]
        print(
            f"[{c_idx}/{len(centers)}] {lat:.4f},{lon:.4f} -> {len(tiles)} tiles "
            f"({len(pending)} pending)",
            file=sys.stderr,
        )
        for t_idx, tile in enumerate(pending, 1):
            places, ok = search_tile(
                session,
                api_key,
                args.query,
                tile[0],
                tile[1],
                args.tile_km,
                min(args.max_pages, 3),
                args.sleep,
            )
            new = sum(state.add_place(to_row(p, tile)) for p in places if p.get("id"))
            # Only mark the tile done on a clean pass, so a network blip gets
            # retried on the next run instead of silently losing the tile.
            if ok:
                state.finish_tile(f"{args.query}|{tile[0]:.4f},{tile[1]:.4f}")
            print(
                f"  tile {t_idx}/{len(pending)}: {len(places)} results, "
                f"{new} new, {len(state.places)} total",
                file=sys.stderr,
            )
            time.sleep(args.sleep)

    if not state.places:
        sys.exit("no results — check the query, the coordinates, and the API key")

    if args.enrich_emails and not args.search_only:
        todo = [
            r
            for r in state.places.values()
            if r["website"] and r["place_id"] not in state.scraped
        ]
        have_sites = sum(1 for r in state.places.values() if r["website"])
        print(
            f"\nemail stage: {have_sites} of {len(state.places)} have a website, "
            f"{len(todo)} left to scrape",
            file=sys.stderr,
        )
        hits = sum(1 for v in state.scraped.values() if v)
        for i, row in enumerate(todo, 1):
            emails = scrape_emails(
                session,
                row["website"],
                args.email_timeout,
                args.sleep,
                args.pages_per_site,
            )
            state.add_emails(row["place_id"], emails)
            if emails:
                hits += 1
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} scanned, {hits} with an email", file=sys.stderr)
                write_output(state, args)  # keep the CSV usable mid-run
            time.sleep(args.sleep)

    written = write_output(state, args)
    addresses = {a for v in state.scraped.values() for a in v}
    print(
        f"\nwrote {written} rows to {args.out}\n"
        f"  {len(state.places)} businesses, {len(addresses)} unique email addresses\n"
        f"  checkpoint kept in {state_dir} (delete it or pass --restart to start over)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
