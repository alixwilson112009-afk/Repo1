# FRED economic data downloader

A beginner-friendly Python script that pulls economic data from the
[FRED API](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) and
saves it as CSV files.

## What it downloads

| Series ID  | What it is                | Frequency | History starts |
|------------|---------------------------|-----------|----------------|
| `FEDFUNDS` | Federal funds rate        | Monthly   | 1954           |
| `CPIAUCSL` | Consumer Price Index      | Monthly   | 1947           |
| `UNRATE`   | Unemployment rate         | Monthly   | 1948           |
| `DGS10`    | 10-year Treasury yield    | Daily     | 1962           |
| `GDPC1`    | Real GDP                  | Quarterly | 1947           |
| `SP500`    | S&P 500 index             | Daily     | last 10 years* |

\* FRED's licensing only permits 10 years of S&P 500 history. That's a limit on
FRED's side, not a bug in the script.

## What it produces

Everything lands in a `data/` folder next to the script:

- `FEDFUNDS.csv`, `CPIAUCSL.csv`, ... — one file per series
- `combined_all_series.csv` — every series lined up by date, full detail
- `combined_monthly.csv` — same data collapsed to one row per month

## Get a free API key

1. Go to <https://fredaccount.stlouisfed.org/apikeys>
2. Register (free, no credit card) or log in
3. Click **Request API Key**, describe your use, agree to the terms
4. Copy the 32-character key
5. Paste it into `fred_data.py` on the `FRED_API_KEY = "PASTE_YOUR_KEY_HERE"` line

Alternatively, set it as an environment variable, which keeps it out of the file:

```bash
export FRED_API_KEY=your_key_here
```

## Run it

```bash
pip install requests pandas
python fred_data.py
```

## Adding more series

Edit the `SERIES` dictionary near the top of `fred_data.py`. Add one line per
series in the form `"SERIES_ID": "friendly_column_name",`. Nothing else needs
to change — the per-series CSVs, the combined file, and the monthly file all
pick it up automatically.

Find series IDs by searching <https://fred.stlouisfed.org>; the ID is the last
part of the URL (e.g. `fred.stlouisfed.org/series/UNRATE` → `UNRATE`).
