# FRED economic data downloader

A beginner-friendly Python script that pulls 28 US economic series from the
[FRED API](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) and
saves them as CSV files.

## What it downloads

**Rates & monetary**

| Series ID | What it is | Freq | Starts |
|---|---|---|---|
| `FEDFUNDS` | Federal funds rate | Monthly | 1954 |
| `DGS3MO` | 3-month Treasury yield | Daily | 1981 |
| `DGS2` | 2-year Treasury yield | Daily | 1976 |
| `DGS10` | 10-year Treasury yield | Daily | 1962 |
| `DGS30` | 30-year Treasury yield | Daily | 1977 |
| `T10Y2Y` | 10yr–2yr yield curve spread | Daily | 1976 |
| `MORTGAGE30US` | 30-year fixed mortgage rate | Weekly | 1971 |
| `M2SL` | M2 money supply | Monthly | 1959 |

**Inflation & prices**

| Series ID | What it is | Freq | Starts |
|---|---|---|---|
| `CPIAUCSL` | CPI, all items | Monthly | 1947 |
| `CPILFESL` | Core CPI (ex food & energy) | Monthly | 1957 |
| `PCEPI` | PCE price index | Monthly | 1959 |
| `PCEPILFE` | Core PCE — the Fed's actual target | Monthly | 1959 |
| `PPIACO` | Producer prices, all commodities | Monthly | 1913 |
| `DCOILWTICO` | WTI crude oil, $/barrel | Daily | 1986 |

**Growth & output**

| Series ID | What it is | Freq | Starts |
|---|---|---|---|
| `GDPC1` | Real GDP | Quarterly | 1947 |
| `INDPRO` | Industrial production | Monthly | 1919 |
| `RSAFS` | Advance retail sales | Monthly | 1992 |
| `HOUST` | Housing starts | Monthly | 1959 |

**Labor**

| Series ID | What it is | Freq | Starts |
|---|---|---|---|
| `PAYEMS` | Nonfarm payrolls | Monthly | 1939 |
| `UNRATE` | Unemployment rate | Monthly | 1948 |
| `ICSA` | Initial jobless claims | Weekly | 1967 |
| `CIVPART` | Labor force participation rate | Monthly | 1948 |
| `CES0500000003` | Average hourly earnings | Monthly | 2006 |

**Markets & sentiment**

| Series ID | What it is | Freq | Starts |
|---|---|---|---|
| `SP500` | S&P 500 index | Daily | last 10 yrs* |
| `VIXCLS` | VIX volatility index | Daily | 1990 |
| `BAMLH0A0HYM2` | High-yield corporate bond spread | Daily | 1996 |
| `DTWEXBGS` | Broad trade-weighted dollar index | Daily | 2006 |
| `UMCSENT` | U. Michigan consumer sentiment | Monthly | 1978 |

\* FRED's licensing only permits 10 years of S&P 500 history. That's a FRED
limit, not a bug in the script.

## What it produces

Everything lands in a `data/` folder next to the script:

- `FEDFUNDS.csv`, `DGS10.csv`, ... — one file per series, native frequency
- `combined_monthly.csv` — **the main one.** All series resampled to monthly
  and forward-filled, so every row is complete
- `combined_all_series.csv` — every original date preserved, blanks left blank
- A summary table printed to screen: series, frequency, date range, row count,
  and whether it succeeded

## Get a free API key

1. Go to <https://fredaccount.stlouisfed.org/apikeys>
2. Register (free, no credit card) or log in
3. Click **Request API Key**, describe your use, agree to the terms
4. Copy the 32-character key

Then give it to the script one of three ways — it checks in this order:

**In Google Colab (recommended):** click the key icon in the left sidebar →
**Add new secret** → name it exactly `FRED_API` → paste the key → enable
**Notebook access**. The script finds it automatically and your key never
appears in the notebook.

**In a terminal:** `export FRED_API_KEY=your_key_here`

**Or** type it into the `FRED_API_KEY` line near the top of `fred_data.py`.
Easiest to start with, but never commit that to a public repo.

## Run it

```bash
pip install requests pandas
python fred_data.py
```

Takes roughly a minute — it makes about 56 requests, well inside FRED's limit
of 120/minute.

## Adding or removing series

Edit the `SERIES` dictionary near the top of `fred_data.py` — that's the only
place. Add a line in the form `"SERIES_ID": "friendly_column_name",`, or delete
a line (or comment it out with `#`) to drop one. The individual CSVs, both
combined files, and the summary table all adapt automatically.

Find series IDs by searching <https://fred.stlouisfed.org>; the ID is the last
part of the URL (e.g. `fred.stlouisfed.org/series/UNRATE` → `UNRATE`).

## Two things to know before you trust this data

**Dates are when the data *happened*, not when it was *published*.** March
unemployment is dated March 1st but wasn't released until early April.

**FRED serves the latest revised numbers.** Payrolls and GDP get revised for
years. The value in this file for a past month is often not what anyone saw at
the time.

Both matter enormously if you're backtesting a strategy — together they let you
"see" numbers before they existed. For point-in-time data as originally
published, use [ALFRED](https://alfred.stlouisfed.org/), FRED's archival
sibling.
