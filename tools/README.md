# Prospecting tools

## places_prospector.py

Pulls local businesses out of the Google Places API (New) into a CSV for outreach.

### Setup

1. In Google Cloud, create a project and enable **Places API (New)** — not the
   legacy Places API; the endpoints differ and this script targets the new one.
2. Create an API key and restrict it to the Places API.
3. `export GOOGLE_PLACES_API_KEY=...`

### Run

One metro:

```bash
python3 tools/places_prospector.py \
    --query "window cleaning" \
    --center 33.4484,-112.0740 \
    --radius-km 60 \
    --out window_cleaners_phoenix.csv
```

Every metro, emails only:

```bash
python3 tools/places_prospector.py \
    --query "window cleaning" \
    --centers-file tools/metros-us-top25.txt \
    --radius-km 40 \
    --out window_cleaners_us.csv \
    --enrich-emails --emails-only
```

`--emails-only` writes a two-column `email,business` CSV, deduped across the
whole run, instead of the full business record. Drop the flag to get everything.

### Resuming

Long runs checkpoint as they go, into `<out>.csv.state/` by default. Every
finished tile and every scraped site is appended immediately, so a run that dies
at hour six loses at most the tile in flight. Re-run the exact same command to
resume; it reports what it recovered and skips the completed work.

```
resuming: 4213 businesses, 892 tiles done, 1150 sites scraped
```

A tile is only marked done on a clean pass, so a network blip gets retried
rather than silently dropped. The CSV is also rewritten every 25 sites during
the email stage, so the partial output is usable while the run continues.

Pass `--restart` to discard the checkpoint, or `--search-only` to gather
businesses now and run the slow email stage later.

### Why tiling

One Places text search returns at most 60 results no matter how large the search
area is. To cover a whole metro the script lays a grid of small overlapping
circles across the target area, searches each, and dedupes by place ID. Smaller
`--tile-km` finds more businesses and costs more calls:

| radius-km | tile-km | tiles per metro |
|-----------|---------|-----------------|
| 40        | 8       | 61              |
| 60        | 8       | 121             |
| 60        | 5       | 293             |

### Cost

Text Search bills per request, and every page of results is its own request.
A 61-tile metro is up to 183 requests. The Maps Platform free tier covers a
useful amount of this; set a budget cap and a quota limit on the key before a
large run, because a 25-metro sweep at `--tile-km 5` is several thousand calls.

### Emails

Places has no email field at any tier, so `--enrich-emails` visits each business
website afterwards. Per site it reads the homepage, follows whatever
contact/about links that page advertises, then tries the usual guessed paths,
stopping at `--pages-per-site` (default 5).

It reads four forms of address:

- plain text and `mailto:` links
- `data-cfemail` hex, which is how Cloudflare obfuscates addresses
- `application/ld+json` business schema blocks
- `info [at] example [dot] com` style hand-obfuscation

Results are filtered against platform noise (Wix, Squarespace, Shopify, Sentry)
and sorted so an address on the business's own domain comes first. Expect
roughly a third to a half of records that have a website to yield an address;
the rest run contact forms with no published address, and no scraper gets those.

### Before you use the output

- Google's Maps Platform terms allow using this data for your own business but
  prohibit redistributing or reselling Places content.
- CAN-SPAM treats automated harvesting of email addresses as an aggravated
  violation when the harvested addresses are then emailed commercially. Sending
  to businesses you have a genuine reason to contact is ordinary; bulk-blasting
  a scraped list is where the penalties sit.
- Check the phone column against the DNC rules that apply to you before dialing.
