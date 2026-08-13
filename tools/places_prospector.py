#!/usr/bin/env python3
"""
Pull local businesses from the Google Places API (New) into a CSV.

A single Places text search caps out at 60 results, so covering a metro means
tiling it: lay a grid of overlapping circles over the target area, search each
one, and dedupe by place ID. That is what --radius-km and --tile-km control.

Places does not return email addresses. --enrich-emails visits each business
website afterwards and pulls contact addresses out of the HTML; expect a hit
rate around a third to a half.

    export GOOGLE_PLACES_API_KEY=...
    python3 tools/places_prospector.py \
        --query "window cleaning" \
        --center 33.4484,-112.0740 \
        --radius-km 60 \
        --out window_cleaners_phoenix.csv

Multiple metros in one run:

    python3 tools/places_prospector.py \
        --query "window cleaning" \
        --centers-file metros.txt \
        --out window_cleaners.csv --enrich-emails
"""

import argparse
import csv
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

EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE
)

# Addresses that show up on nearly every site and are never the business.
EMAIL_NOISE = re.compile(
    r"(^|@)(example|sentry|wixpress|squarespace|godaddy|domain|yourdomain|"
    r"email|test|no-?reply|donotreply)\.?",
    re.IGNORECASE,
)
EMAIL_NOISE_EXT = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js|woff2?)$", re.IGNORECASE)

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/get-a-quote"]


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
    for page in range(max_pages):
        if token:
            body["pageToken"] = token
        try:
            resp = session.post(SEARCH_URL, headers=headers, json=body, timeout=30)
        except requests.RequestException as exc:
            print(f"  ! network error: {exc}", file=sys.stderr)
            break

        if resp.status_code == 429:
            print("  ! rate limited, backing off 10s", file=sys.stderr)
            time.sleep(10)
            continue
        if resp.status_code != 200:
            print(f"  ! HTTP {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
            break

        data = resp.json()
        places.extend(data.get("places", []))
        token = data.get("nextPageToken")
        if not token:
            break
        # Places rejects a page token used too quickly after it is issued.
        time.sleep(max(sleep_s, 2.0))

    return places


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
        "rating": place.get("rating", ""),
        "review_count": place.get("userRatingCount", ""),
        "business_status": place.get("businessStatus", ""),
        "category": (place.get("primaryTypeDisplayName") or {}).get("text", ""),
        "maps_url": place.get("googleMapsUri", ""),
        "latitude": loc.get("latitude", ""),
        "longitude": loc.get("longitude", ""),
        "source_tile": f"{tile[0]:.4f},{tile[1]:.4f}",
    }


def clean_emails(candidates, site_host):
    """Drop junk matches and prefer an address on the business's own domain."""
    seen = []
    for raw in candidates:
        addr = raw.strip().strip(".,;:()<>\"'").lower()
        if EMAIL_NOISE.search(addr) or EMAIL_NOISE_EXT.search(addr):
            continue
        if len(addr) > 100 or addr.count("@") != 1:
            continue
        if addr not in seen:
            seen.append(addr)
    if not seen:
        return ""
    root = site_host.lower().removeprefix("www.")
    for addr in seen:
        if addr.endswith("@" + root) or addr.endswith("." + root):
            return addr
    return seen[0]


def scrape_email(session, website, timeout, sleep_s):
    """Look for a contact address on the homepage, then common contact pages."""
    host = urlparse(website).netloc
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }

    for path in [""] + CONTACT_PATHS:
        url = urljoin(website, path) if path else website
        try:
            resp = session.get(
                url, headers=headers, timeout=timeout, allow_redirects=True
            )
        except requests.RequestException:
            continue
        if resp.status_code != 200 or "html" not in resp.headers.get(
            "Content-Type", ""
        ):
            continue

        html = resp.text
        found = EMAIL_RE.findall(html)
        # mailto: links are the highest-signal source, so weight them first.
        mailtos = re.findall(r'mailto:([^"\'?>\s]+)', html, re.IGNORECASE)
        email = clean_emails(mailtos + found, host)
        if email:
            return email
        time.sleep(sleep_s)

    return ""


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
    ap.add_argument("--email-timeout", type=float, default=10.0)
    ap.add_argument("--raw-dump", help="also write the raw API responses here")
    args = ap.parse_args()

    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        sys.exit("set GOOGLE_PLACES_API_KEY (Places API New must be enabled)")

    centers = load_centers(args)
    session = requests.Session()

    rows, raw = {}, []
    for c_idx, (lat, lon) in enumerate(centers, 1):
        tiles = build_grid(lat, lon, args.radius_km, args.tile_km)
        print(
            f"[{c_idx}/{len(centers)}] {lat:.4f},{lon:.4f} -> {len(tiles)} tiles",
            file=sys.stderr,
        )
        for t_idx, tile in enumerate(tiles, 1):
            places = search_tile(
                session,
                api_key,
                args.query,
                tile[0],
                tile[1],
                args.tile_km,
                min(args.max_pages, 3),
                args.sleep,
            )
            new = 0
            for place in places:
                pid = place.get("id")
                if pid and pid not in rows:
                    rows[pid] = to_row(place, tile)
                    new += 1
            if args.raw_dump:
                raw.extend(places)
            print(
                f"  tile {t_idx}/{len(tiles)}: {len(places)} results, "
                f"{new} new, {len(rows)} total",
                file=sys.stderr,
            )
            time.sleep(args.sleep)

    if not rows:
        sys.exit("no results — check the query, the coordinates, and the API key")

    if args.enrich_emails:
        with_sites = [r for r in rows.values() if r["website"]]
        print(
            f"\nenriching {len(with_sites)} of {len(rows)} records that have a website",
            file=sys.stderr,
        )
        hits = 0
        for i, row in enumerate(with_sites, 1):
            row["email"] = scrape_email(
                session, row["website"], args.email_timeout, args.sleep
            )
            if row["email"]:
                hits += 1
            if i % 25 == 0 or i == len(with_sites):
                print(f"  {i}/{len(with_sites)} scanned, {hits} emails", file=sys.stderr)
            time.sleep(args.sleep)

    out_path = Path(args.out)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows.values())

    if args.raw_dump:
        Path(args.raw_dump).write_text(json.dumps(raw, indent=2))

    emails = sum(1 for r in rows.values() if r["email"])
    sites = sum(1 for r in rows.values() if r["website"])
    phones = sum(1 for r in rows.values() if r["phone"])
    print(
        f"\nwrote {len(rows)} businesses to {out_path}\n"
        f"  {phones} with a phone, {sites} with a website, {emails} with an email",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
