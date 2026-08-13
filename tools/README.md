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

Many metros, with email enrichment:

```bash
python3 tools/places_prospector.py \
    --query "window cleaning" \
    --centers-file tools/metros-us-top25.txt \
    --radius-km 40 \
    --out window_cleaners_us.csv \
    --enrich-emails
```

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

Places has no email field at any tier. `--enrich-emails` visits each business
website afterwards, checks the homepage and the usual contact pages, and prefers
an address on the business's own domain. Expect roughly a third to a half of
records with a website to yield an address; the rest use contact forms only.

### Before you use the output

- Google's Maps Platform terms allow using this data for your own business but
  prohibit redistributing or reselling Places content.
- CAN-SPAM treats automated harvesting of email addresses as an aggravated
  violation when the harvested addresses are then emailed commercially. Sending
  to businesses you have a genuine reason to contact is ordinary; bulk-blasting
  a scraped list is where the penalties sit.
- Check the phone column against the DNC rules that apply to you before dialing.
