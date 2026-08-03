"""
fred_data.py
============

Downloads a broad set of US economic data from the FRED API (Federal Reserve
Economic Data, run by the St. Louis Fed) and saves it as CSV files you can open
in Excel, Google Sheets, or Colab.

What you get when you run this:
  * One CSV per series      -> data/FEDFUNDS.csv, data/DGS10.csv, ...
  * A monthly combined CSV  -> data/combined_monthly.csv   (the main one)
  * A full-detail combined  -> data/combined_all_series.csv (every original date)
  * A summary table printed at the end showing what succeeded and what didn't

-------------------------------------------------------------------------
HOW TO GET YOUR FREE FRED API KEY  (about 2 minutes, free, no credit card)
-------------------------------------------------------------------------
An "API key" is just a long string of letters and numbers that tells FRED who
is asking for data.

  1. Go to:  https://fredaccount.stlouisfed.org/apikeys
  2. Log in, or click "Register" and sign up with your email.
  3. Click the "Request API Key" button.
  4. Describe your use, e.g. "Personal project to learn about APIs."
  5. Check the terms box, click "Request API Key".
  6. Your key appears immediately -- 32 lowercase letters and numbers, like:
        abcdef1234567890abcdef1234567890

-------------------------------------------------------------------------
WHERE TO PUT THE KEY -- three options, checked in this order
-------------------------------------------------------------------------
1. GOOGLE COLAB SECRET (recommended, and what this script expects):
     In Colab, click the key icon in the left sidebar ("Secrets"), click
     "Add new secret", name it exactly  FRED_API  , paste your key as the
     value, and flip on "Notebook access". The script finds it automatically.
     This keeps your key out of the notebook, so it is never saved or shared
     along with your code.

2. ENVIRONMENT VARIABLE (if you are running in a terminal):
     export FRED_API_KEY=your_key_here

3. TYPED DIRECTLY INTO THIS FILE, on the FRED_API_KEY line below. Easiest to
   start with, but be careful never to commit it to a public GitHub repo --
   an API key is tied to your account, like a password.

-------------------------------------------------------------------------
A NOTE ON PUBLICATION LAG (important if you care about trading)
-------------------------------------------------------------------------
Every row in these files is stamped with the date the data DESCRIBES, not the
date it was PUBLISHED. Those are very different things. March's unemployment
rate is dated March 1st but was not published until early April.

FRED also serves the LATEST REVISED value of everything. Payrolls and GDP get
revised for years afterward, so the number sitting in this file for a past
month is often not the number anyone actually saw at the time.

Together those two facts mean this data is great for understanding history but
misleading for backtesting a trading strategy -- it lets you "see" numbers
before they existed. If you need point-in-time data, look up ALFRED, FRED's
archival sibling, which serves the vintages as they were originally published.
"""

# ---------------------------------------------------------------------------
# STEP 0: Import the libraries (tools) we need.
# ---------------------------------------------------------------------------
# "import" loads code somebody else already wrote so we don't have to.
import os        # built in: read environment variables, make folders
import time      # built in: pause between requests
import requests  # third party: the standard way to fetch things over the web
import pandas as pd  # third party: spreadsheet-like tables in Python
                     # ("pd" is just a nickname so we can type less)


# ---------------------------------------------------------------------------
# STEP 1: Find the API key.
# ---------------------------------------------------------------------------
# If you want to type your key straight into this file, replace
# PASTE_YOUR_KEY_HERE below. Keep the quotes -- in Python, text needs quotes.
FRED_API_KEY = "PASTE_YOUR_KEY_HERE"


def find_api_key():
    """Look for the API key in the three places described at the top.

    Returns the key as a string, or None if it isn't found anywhere.
    """
    # --- Option 1: a Google Colab secret named FRED_API ---
    # The "try / except" pattern means "attempt this; if it fails, don't crash,
    # just move on". We need it because `google.colab` only exists inside
    # Colab -- on a normal computer the import fails, which is fine.
    try:
        from google.colab import userdata
        key = userdata.get("FRED_API")
        if key:
            print("Using API key from Colab secret 'FRED_API'.")
            return key.strip()
    except Exception:
        # Not running in Colab, or the secret isn't set / not enabled for this
        # notebook. Either way, fall through and try the next option.
        pass

    # --- Option 2: an environment variable ---
    # We accept either name so it works no matter which you set.
    for name in ("FRED_API_KEY", "FRED_API"):
        key = os.environ.get(name)
        if key:
            print(f"Using API key from environment variable '{name}'.")
            return key.strip()

    # --- Option 3: typed into this file ---
    if FRED_API_KEY and FRED_API_KEY != "PASTE_YOUR_KEY_HERE":
        print("Using API key typed into fred_data.py.")
        return FRED_API_KEY.strip()

    # Nothing found.
    return None


# ---------------------------------------------------------------------------
# STEP 2: Decide which data series we want.
# ---------------------------------------------------------------------------
# Every dataset on FRED has a short code called a "series ID". You can find any
# series' ID by searching https://fred.stlouisfed.org and reading it off the
# end of the web address:
#     https://fred.stlouisfed.org/series/UNRATE   <-- the ID is UNRATE
#
# This is a Python "dictionary": pairs of  key: value.
# The key is the FRED series ID; the value is the friendly column name used in
# the combined spreadsheets.
#
# >>> THIS IS THE ONE PLACE TO EDIT. <<<
# Add a series:    put a new line anywhere below, same format.
# Remove a series: delete its line (or put a # in front to disable it).
# Everything downstream -- the individual CSVs, both combined files, and the
# summary table -- adapts automatically. No other part of the script changes.
#
# The "# ---- category ----" lines are just comments to keep things readable.
# Python ignores them; they have no effect on grouping.
SERIES = {
    # ---- Rates & monetary policy ----
    "FEDFUNDS":      "fed_funds_rate",             # Effective Fed Funds Rate, %
    "DGS3MO":        "treasury_3m",                # 3-month Treasury yield, %
    "DGS2":          "treasury_2y",                # 2-year Treasury yield, %
    "DGS10":         "treasury_10y",               # 10-year Treasury yield, %
    "DGS30":         "treasury_30y",               # 30-year Treasury yield, %
    "T10Y2Y":        "yield_curve_10y_2y",         # 10yr minus 2yr spread, %
    "MORTGAGE30US":  "mortgage_30yr",              # 30-year fixed mortgage, %
    "M2SL":          "m2_money_supply",            # M2 money stock, $ billions

    # ---- Inflation & prices ----
    "CPIAUCSL":      "cpi",                        # CPI, all items (index)
    "CPILFESL":      "core_cpi",                   # CPI less food & energy
    "PCEPI":         "pce_price_index",            # PCE price index
    "PCEPILFE":      "core_pce_price_index",       # Core PCE -- the Fed's target
    "PPIACO":        "ppi_all_commodities",        # Producer prices, all commodities
    "DCOILWTICO":    "wti_crude_oil",              # WTI crude oil, $/barrel

    # ---- Growth & output ----
    "GDPC1":         "real_gdp",                   # Real GDP, billions of 2017 $
    "INDPRO":        "industrial_production",      # Industrial production (index)
    "RSAFS":         "retail_sales",               # Advance retail sales, $ millions
    "HOUST":         "housing_starts",             # Housing starts, thousands

    # ---- Labor market ----
    "PAYEMS":        "nonfarm_payrolls",           # Total nonfarm jobs, thousands
    "UNRATE":        "unemployment_rate",          # Unemployment rate, %
    "ICSA":          "initial_jobless_claims",     # Weekly initial claims
    "CIVPART":       "labor_force_participation",  # Participation rate, %
    "CES0500000003": "avg_hourly_earnings",        # Avg hourly earnings, $

    # ---- Markets & sentiment ----
    "SP500":         "sp500",                      # S&P 500 (FRED gives 10 yrs only)
    "VIXCLS":        "vix",                        # VIX volatility index
    "BAMLH0A0HYM2":  "high_yield_spread",          # High-yield bond spread, %
    "DTWEXBGS":      "dollar_index",               # Broad trade-weighted dollar
    "UMCSENT":       "consumer_sentiment",         # U. Michigan sentiment
}

# Where to put the CSV files. Created automatically if it doesn't exist.
OUTPUT_FOLDER = "data"

# The two web addresses ("endpoints") we call on FRED's server. An endpoint is
# just a URL that returns data instead of a web page.
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES_INFO_URL = "https://api.stlouisfed.org/fred/series"


# ---------------------------------------------------------------------------
# STEP 3: A helper that fetches a URL and retries if the network hiccups.
# ---------------------------------------------------------------------------
# Downloading ~28 series means ~56 requests. Over a home or Colab connection,
# it is normal for one to occasionally time out. Rather than let a single blip
# ruin the whole run, we try up to three times, waiting a bit longer each time.
def get_with_retries(url, params, attempts=3):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            # timeout=30 means "give up after 30 seconds" so we can't hang forever.
            response = requests.get(url, params=params, timeout=30)

            # FRED answers with HTTP status 400 when something about the request
            # is wrong -- almost always a bad or missing API key. Retrying will
            # not help, so we stop immediately and report it.
            if response.status_code == 400:
                message = response.json().get("error_message", "no message given")
                raise ValueError(f"FRED rejected the request: {message}")

            # Raise an error for any other failure status (500, 404, ...).
            response.raise_for_status()
            return response

        except ValueError:
            # A bad key is not worth retrying -- pass it straight up.
            raise
        except Exception as error:
            last_error = error
            if attempt < attempts:
                wait = 2 ** attempt          # 2 seconds, then 4 seconds
                print(f"    (attempt {attempt} failed, retrying in {wait}s)")
                time.sleep(wait)

    # All attempts used up -- report the final error to the caller.
    raise last_error


# ---------------------------------------------------------------------------
# STEP 4: Ask FRED for a series' metadata (its title and how often it updates).
# ---------------------------------------------------------------------------
# This is a separate, small API call. We use it so the summary table can show
# real frequencies straight from FRED instead of us hardcoding guesses.
def fetch_series_metadata(series_id, api_key):
    params = {"series_id": series_id, "api_key": api_key, "file_type": "json"}
    try:
        # attempts=1: metadata is only a nice-to-have, so don't burn time
        # retrying it. The real data call below does its own retrying.
        response = get_with_retries(SERIES_INFO_URL, params, attempts=1)
        info = response.json()["seriess"][0]
        return {
            "title": info.get("title", series_id),
            # frequency_short is "D" daily, "W" weekly, "M" monthly,
            # "Q" quarterly, "A" annual.
            "frequency": info.get("frequency_short", "?"),
        }
    except Exception:
        # Metadata is a nice-to-have. If it fails, carry on with placeholders
        # rather than losing the actual data.
        return {"title": series_id, "frequency": "?"}


# ---------------------------------------------------------------------------
# STEP 5: Download ONE series' full history.
# ---------------------------------------------------------------------------
# A "function" is a reusable chunk of code with a name. We define it once and
# call it 28 times below, instead of copy-pasting.
def fetch_series(series_id, column_name, api_key):
    """Download the full history of one FRED series.

    Returns a pandas DataFrame (a table) with a date column and a value column.
    """
    # These are the "query parameters" -- the questions we're asking FRED.
    # requests turns this dictionary into a URL that looks like:
    #   ...observations?series_id=UNRATE&api_key=xxx&file_type=json&...
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",                 # JSON is easy for Python to read
        "observation_start": "1776-07-04",   # FRED's earliest allowed date, so
                                             # we always get the FULL history
        "limit": 100000,                     # max rows per request (the cap).
                                             # No series here is close to this;
                                             # if one ever were, you would need
                                             # to page through with "offset".
    }

    response = get_with_retries(OBSERVATIONS_URL, params)

    # .json() converts FRED's response text into Python lists/dictionaries.
    # The part we want lives under "observations" and looks like:
    #   [{"date": "1954-07-01", "value": "0.80", ...}, ...]
    observations = response.json()["observations"]

    if not observations:
        raise ValueError("FRED returned zero observations")

    # Hand that list of records to pandas, which turns it into a table.
    df = pd.DataFrame(observations)

    # Keep only the two columns we care about. (FRED also sends realtime_start
    # and realtime_end, which describe data revisions -- not needed here.)
    df = df[["date", "value"]]

    # FRED sends everything as text. Convert the types so we can do math later:
    #   - dates become real dates
    #   - values become real numbers
    # FRED writes "." to mean "no data for this date" (market holidays, etc.).
    # errors="coerce" turns anything unconvertible, including ".", into NaN
    # (Not a Number = pandas' word for "blank").
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Rename "value" to the friendly name so the combined files are readable.
    df = df.rename(columns={"value": column_name})
    return df


# ---------------------------------------------------------------------------
# STEP 6: The main routine -- this is what actually runs.
# ---------------------------------------------------------------------------
def main():
    api_key = find_api_key()

    # Guard clause: stop early, with a helpful message, if there's no key.
    if not api_key:
        raise SystemExit(
            "\nNo FRED API key found.\n\n"
            "Pick whichever is easiest:\n"
            "  * In Colab: click the key icon in the left sidebar, add a secret\n"
            "    named FRED_API, paste your key, enable 'Notebook access'.\n"
            "  * In a terminal: export FRED_API_KEY=your_key_here\n"
            "  * Or edit the FRED_API_KEY line near the top of this file.\n\n"
            "Get a free key in ~2 minutes:\n"
            "  https://fredaccount.stlouisfed.org/apikeys"
        )

    # Create the output folder. exist_ok=True means "fine if it already exists".
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print(f"\nFetching {len(SERIES)} series from FRED...\n")

    frames = []   # each successfully downloaded table, for merging later
    summary = []  # one record per series, for the report at the end
    failures = [] # series that did not come back, so we can flag them clearly

    # Loop over the dictionary. .items() gives us the key and the value.
    for series_id, column_name in SERIES.items():
        print(f"{series_id:<15} {column_name}")

        # ---- Error handling: one bad series must not kill the whole run. ----
        # Everything risky goes inside "try". If any of it raises an error, we
        # jump to "except", record the failure, and carry on with the next
        # series instead of crashing.
        try:
            meta = fetch_series_metadata(series_id, api_key)
            df = fetch_series(series_id, column_name, api_key)

            # Save this one series to its own CSV.
            # index=False stops pandas writing an extra unnamed counter column.
            single_path = os.path.join(OUTPUT_FOLDER, f"{series_id}.csv")
            df.to_csv(single_path, index=False)

            # Count only real numbers, ignoring the "." blanks we converted.
            valid_rows = int(df[column_name].notna().sum())

            print(f"    {len(df):,} rows, {df['date'].min().date()} to "
                  f"{df['date'].max().date()}  ->  {single_path}")

            # Set 'date' as the row label (the "index"). This is what lets
            # pandas line the series up by date automatically further down.
            frames.append(df.set_index("date"))

            summary.append({
                "series_id": series_id,
                "name": column_name,
                "freq": meta["frequency"],
                "start": df["date"].min().date(),
                "end": df["date"].max().date(),
                "rows": len(df),
                "values": valid_rows,
                "status": "ok",
            })

        except Exception as error:
            # A clear, un-scary warning -- then keep going.
            print(f"    WARNING: could not download {series_id} -- {error}")
            print(f"    Skipping it and continuing with the rest.")
            failures.append((series_id, str(error)))
            summary.append({
                "series_id": series_id,
                "name": column_name,
                "freq": "-", "start": "-", "end": "-",
                "rows": 0, "values": 0,
                "status": "FAILED",
            })

        # Be polite to FRED's servers. Their limit is 120 requests per minute;
        # we are well under it, but pausing is good manners.
        time.sleep(0.3)

    # If literally everything failed there is nothing to combine.
    if not frames:
        raise SystemExit(
            "\nNo series downloaded successfully, so there is nothing to "
            "combine.\nCheck your internet connection and your API key."
        )

    # -----------------------------------------------------------------------
    # STEP 7: Combine everything, lined up by date.
    # -----------------------------------------------------------------------
    # pd.concat(..., axis=1) glues the tables side by side, matching rows on the
    # shared date index. join="outer" keeps EVERY date appearing in ANY series,
    # so nothing is thrown away.
    combined = pd.concat(frames, axis=1, join="outer").sort_index()

    # Save the untouched, full-detail version first. Daily series keep their
    # daily rows here, so most cells are blank -- real GDP genuinely has no
    # value for a random Tuesday. That is correct, not a bug. This file is the
    # honest record; the monthly one below is the convenient one.
    detailed_path = os.path.join(OUTPUT_FOLDER, "combined_all_series.csv")
    combined.to_csv(detailed_path)  # keep the index: it is the date column

    # -----------------------------------------------------------------------
    # STEP 8: Resample to monthly and forward-fill.
    # -----------------------------------------------------------------------
    # Our series update at wildly different speeds: VIX is daily, jobless
    # claims weekly, CPI monthly, GDP quarterly. To compare them in one table
    # they need a common grid, and monthly is the natural choice -- it is the
    # frequency most US macro data is published at.
    #
    # resample("ME") regroups rows into calendar months ("ME" = month end).
    # .last() takes the final observation within each month.
    #
    # Why .last() rather than .mean()? Because it answers a cleaner question:
    # "what was the most recent value available at the end of this month?"
    # That matches how you would actually look at data in real life. (For
    # weekly series like jobless claims, .mean() would give a smoother monthly
    # average -- swap it in if that is what you want.)
    monthly = combined.resample("ME").last()

    # ---- Why forward-fill (ffill) is the right call here ----
    # ffill carries the last known value forward into months that have none.
    # Q1 GDP then shows up in January, February and March instead of only once.
    #
    # It is right because these series are LEVELS that persist. GDP does not
    # cease to exist in February just because it is only measured quarterly --
    # the most recent published figure remains the best available description
    # of the economy until a newer one replaces it. Forward-filling repeats a
    # real number you actually knew; it never invents one. Without it, any
    # chart or comparison would be riddled with holes, and most pandas
    # operations would silently drop those rows.
    #
    # ---- When forward-fill is the WRONG call ----
    # 1. STATISTICS. A GDP value repeated across three months is one
    #    observation, not three. Correlations and R-squared get inflated,
    #    volatility gets understated, and regressions treat copied values as
    #    independent evidence. For serious statistical work use the
    #    full-detail file above and let the blanks stay blank.
    # 2. RATES OF CHANGE. Month-over-month growth on filled data shows fake
    #    0% months followed by an artificial jump when the real number lands.
    #    Compute growth rates from the native frequency instead.
    # 3. BACKTESTING. This is the big one. ffill spreads a value across the
    #    months it DESCRIBES, but that value was not PUBLISHED until weeks
    #    later. Q1 GDP is dated January 1st and was not released until late
    #    April -- so a backtest reading this column in January is seeing the
    #    future. See the publication-lag note at the top of this file.
    # 4. STALE SERIES. If a series is discontinued, ffill will happily repeat
    #    its final value forever, making dead data look alive.
    monthly = monthly.ffill()

    monthly_path = os.path.join(OUTPUT_FOLDER, "combined_monthly.csv")
    monthly.to_csv(monthly_path)

    # -----------------------------------------------------------------------
    # STEP 9: Print the summary report.
    # -----------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)

    # Turning the list of records into a DataFrame gives us tidy aligned
    # columns for free, rather than fiddling with manual spacing.
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

    ok_count = sum(1 for row in summary if row["status"] == "ok")
    print(f"\n{ok_count} of {len(SERIES)} series downloaded successfully.")

    # Repeat any failures at the very bottom, where they cannot be missed
    # after scrolling past a long log.
    if failures:
        print(f"\n{len(failures)} series FAILED:")
        for series_id, message in failures:
            print(f"  - {series_id}: {message}")
        print("\nThe other series were saved normally. A failure is usually a")
        print("temporary network problem -- just run the script again.")

    print(f"\nFiles written to the '{OUTPUT_FOLDER}' folder:")
    print(f"  {detailed_path:<40} {len(combined):,} rows x "
          f"{len(combined.columns)} cols  (full detail)")
    print(f"  {monthly_path:<40} {len(monthly):,} rows x "
          f"{len(monthly.columns)} cols  (monthly, forward-filled)")
    print(f"  ...plus {ok_count} individual series CSVs.")

    # Show the tail so you can see it worked. Wide tables wrap awkwardly in a
    # terminal, so we print the last 3 months of the first 8 columns only.
    print("\nLast 3 months (first 8 columns):\n")
    print(monthly.iloc[-3:, :8].to_string())


# This means "only run main() if this file was executed directly". It is a
# standard Python convention: if someone imports this file to reuse
# fetch_series(), main() will not fire unexpectedly.
if __name__ == "__main__":
    main()
