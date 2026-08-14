# Prospecting tools

## Quick start

```bash
bash tools/start.sh
```

Checks Python, installs the one library needed, asks for your API key once and
remembers it, then starts the UI and prints the address to open. Safe to re-run;
after the first time it goes straight to starting the server.

### On a Chromebook

ChromeOS runs Linux in a container that the browser reaches by hostname rather
than through loopback, so `localhost` will not work. `start.sh` detects this,
binds accordingly, and prints the right address — **http://penguin.linux.test:8000**.

First time only, turn the Linux container on: Settings → About ChromeOS →
Developers → Linux development environment → Turn on. School- or work-managed
Chromebooks often have this disabled by an administrator, in which case none of
this can run locally.

A Chromebook that sleeps mid-run will interrupt it. Keep it plugged in with the
lid open, and set Settings → Device → Power → "Keep display on". If it does
sleep, the checkpoint means re-running the same command resumes rather than
starting over.

## serve.py — local UI

A progress bar, an elapsed timer, an ETA, and a download button, served from
your own machine. `start.sh` launches this for you; to run it directly:

```bash
export GOOGLE_PLACES_API_KEY=...
python3 tools/serve.py          # opens http://127.0.0.1:8000
```

Fill in the form, hit start, watch it work. Closing the browser does not stop
the run, and reopening the page reattaches to the job in flight. Stdlib only —
nothing to install beyond `requests`, which the prospector already needs.

Progress is read out of the checkpoint directory rather than by parsing output,
so the count of tiles, businesses, sites read, and emails found always reflects
the real state on disk.

### Why not Netlify, Vercel, or Lambda

Serverless functions cap out long before this job finishes — Netlify Functions
at 10 seconds, Netlify Background Functions at 15 minutes, Vercel and Lambda in
the same range. A full run is measured in hours. There is also no persistent
filesystem between invocations, so the checkpoint would not survive, and a
public endpoint that triggers Places calls is a public endpoint that spends your
API budget.

If you do want it hosted rather than local, use something with a real
always-on process and a disk — Railway, Render, Fly.io, or any small VPS —
and put authentication in front of it. `--host 0.0.0.0` will bind publicly but
this server has no auth of its own, so do not expose it directly.

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
