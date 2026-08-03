"""
fred_data.py
============

Downloads a handful of important economic data series from the FRED API
(Federal Reserve Economic Data, run by the St. Louis Fed) and saves them
as CSV files you can open in Excel, Google Sheets, or Colab.

What you get when you run this:
  * One CSV per series          -> data/FEDFUNDS.csv, data/CPIAUCSL.csv, ...
  * One combined CSV            -> data/combined_all_series.csv
  * One tidy monthly CSV        -> data/combined_monthly.csv

-------------------------------------------------------------------------
HOW TO GET YOUR FREE FRED API KEY  (takes about 2 minutes, it is free)
-------------------------------------------------------------------------
An "API key" is just a long string of letters and numbers that tells FRED
who is asking for data. It is free and instant.

  1. Go to:  https://fredaccount.stlouisfed.org/apikeys
  2. You will be asked to log in. If you do not have an account yet, click
     "Register" and sign up with your email address. (Free, no credit card.)
  3. Once logged in you will land on the "API Keys" page.
  4. Click the "Request API Key" button.
  5. It asks what you will use it for. Type something simple and true, e.g.
     "Personal project to learn about APIs and economic data."
  6. Check the box agreeing to the terms, then click "Request API Key".
  7. Your key appears on screen right away. It looks something like:
        abcdef1234567890abcdef1234567890
     (32 characters, all lowercase letters and numbers.)
  8. Copy that string.
  9. Paste it into this file, on the FRED_API_KEY line just below --
     between the quotes, replacing the words PASTE_YOUR_KEY_HERE.

That is it. You never need to request a second key; the same one works
forever and for every series.

NOTE ON KEEPING IT PRIVATE: an API key is like a password -- it is tied to
your account. Don't post it publicly or commit it to a public GitHub repo.
This script also accepts the key from an environment variable named
FRED_API_KEY, which is the safer habit once you are comfortable. If that
variable exists it wins; otherwise the value typed below is used.
"""

# ---------------------------------------------------------------------------
# STEP 0: Import the libraries (tools) we need.
# ---------------------------------------------------------------------------
# "import" loads code somebody else already wrote so we don't have to.
import os        # built in: lets us read environment variables + make folders
import time      # built in: lets us pause briefly between requests
import requests  # third party: the standard way to fetch things over the web
import pandas as pd  # third party: spreadsheet-like tables in Python
                     # ("pd" is just a nickname so we can type less)


# ---------------------------------------------------------------------------
# STEP 1: PASTE YOUR API KEY HERE.
# ---------------------------------------------------------------------------
# Replace PASTE_YOUR_KEY_HERE with the 32-character key from the steps above.
# Keep the quotes! In Python, text must be wrapped in quotes.
FRED_API_KEY = "PASTE_YOUR_KEY_HERE"

# If you set an environment variable called FRED_API_KEY, we use that instead.
# os.environ.get(...) means "look it up, and if it isn't there, fall back to
# the second value". Beginners can ignore this line entirely.
FRED_API_KEY = os.environ.get("FRED_API_KEY", FRED_API_KEY)


# ---------------------------------------------------------------------------
# STEP 2: Decide which data series we want.
# ---------------------------------------------------------------------------
# Every dataset on FRED has a short code called a "series ID". For example the
# unemployment rate is "UNRATE". You can find any series' ID by searching on
# https://fred.stlouisfed.org and looking at the end of the page's web address:
#     https://fred.stlouisfed.org/series/UNRATE   <-- the ID is UNRATE
#
# This is a Python "dictionary": pairs of  key: value.
# Here the key is the FRED series ID and the value is a friendly column name
# we'll use in the combined spreadsheet.
#
# >>> THIS IS THE PLACE TO EDIT IF YOU WANT MORE DATA. <<<
# Just add another line in the same format:  "SERIESID": "friendly_name",
# Everything else in the script adapts automatically -- no other changes needed.
# A few popular extras you could paste in:
#     "PAYEMS":    "nonfarm_payrolls",     # total jobs in the US
#     "MORTGAGE30US": "mortgage_30yr",     # 30-year mortgage rate
#     "PCEPI":     "pce_price_index",      # the Fed's preferred inflation gauge
#     "HOUST":     "housing_starts",       # new homes being built
#     "DEXUSEU":   "usd_eur_exchange",     # dollars per euro
#     "T10Y2Y":    "yield_curve_10y_2y",   # the famous recession indicator
SERIES = {
    "FEDFUNDS":  "fed_funds_rate",     # Effective Federal Funds Rate, % (monthly)
    "CPIAUCSL":  "cpi",                # Consumer Price Index, index level (monthly)
    "UNRATE":    "unemployment_rate",  # Unemployment Rate, % (monthly)
    "DGS10":     "treasury_10y",       # 10-Year Treasury Yield, % (daily)
    "GDPC1":     "real_gdp",           # Real GDP, billions of 2017 $ (quarterly)
    "SP500":     "sp500",              # S&P 500 index level (daily, last 10 yrs only)
}

# Where to put the CSV files. This creates a folder named "data" next to the
# script if it doesn't already exist.
OUTPUT_FOLDER = "data"

# The two web addresses ("endpoints") we will call on FRED's server.
# An endpoint is just a URL that returns data instead of a web page.
OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES_INFO_URL = "https://api.stlouisfed.org/fred/series"


# ---------------------------------------------------------------------------
# STEP 3: A function that downloads ONE series.
# ---------------------------------------------------------------------------
# A "function" is a reusable chunk of code with a name. We define it once here,
# then call it six times below (once per series) instead of copy-pasting.
def fetch_series(series_id, column_name):
    """Download the full history of one FRED series.

    Returns a pandas DataFrame (a table) with two columns: date and the value.
    """
    print(f"  Downloading {series_id} ...", end=" ", flush=True)

    # These are the "query parameters" -- the questions we're asking FRED.
    # requests turns this dictionary into a URL that looks like:
    #   ...observations?series_id=UNRATE&api_key=xxx&file_type=json&...
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",        # ask for JSON, which Python reads easily
        "observation_start": "1776-07-04",  # FRED's earliest allowed date, so
                                            # we always get the FULL history
        "limit": 100000,            # max rows per request (100,000 is the cap;
                                    # none of our series is anywhere near this)
    }

    # Actually make the request over the internet. timeout=30 means "give up
    # after 30 seconds" so the script can't hang forever.
    response = requests.get(OBSERVATIONS_URL, params=params, timeout=30)

    # ---- Error checking: tell the user clearly what went wrong. ----
    # HTTP status 400 from FRED usually means a bad or missing API key.
    if response.status_code == 400:
        raise SystemExit(
            f"\n\nFRED rejected the request for {series_id}.\n"
            f"FRED said: {response.json().get('error_message', 'no message')}\n"
            "The most common cause is a missing or mistyped API key.\n"
            "Open this file and check the FRED_API_KEY line near the top."
        )
    # raise_for_status() throws an error for any other failure (500, 404, ...).
    response.raise_for_status()

    # .json() converts FRED's response text into Python dictionaries/lists.
    # The part we want lives under the "observations" key and looks like:
    #   [{"date": "1954-07-01", "value": "0.80", ...}, ...]
    observations = response.json()["observations"]

    # Hand that list of records to pandas, which turns it into a table.
    df = pd.DataFrame(observations)

    # Keep only the two columns we care about (FRED also sends realtime_start
    # and realtime_end, which are about data revisions -- not needed here).
    df = df[["date", "value"]]

    # FRED sends everything as text. Convert the types so we can do math later:
    #   - dates become real dates
    #   - values become numbers
    # FRED uses "." to mean "no data for this day" (e.g. market holidays).
    # errors="coerce" turns anything unconvertible, including ".", into NaN
    # (Not a Number = pandas' word for "blank").
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Rename "value" to the friendly name so the combined file is readable.
    df = df.rename(columns={"value": column_name})

    print(f"got {len(df):,} rows "
          f"({df['date'].min().date()} to {df['date'].max().date()})")
    return df


# ---------------------------------------------------------------------------
# STEP 4: A small helper that asks FRED for a series' human-readable title.
# ---------------------------------------------------------------------------
# This is optional sugar -- it just lets us print "Unemployment Rate" instead
# of only "UNRATE" so the output is friendlier.
def fetch_series_title(series_id):
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
    try:
        response = requests.get(SERIES_INFO_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()["seriess"][0]["title"]
    except Exception:
        # If this extra call fails for any reason, don't crash the whole script.
        return series_id


# ---------------------------------------------------------------------------
# STEP 5: The main routine -- this is what actually runs.
# ---------------------------------------------------------------------------
def main():
    # -- Guard clause: stop early with a friendly message if the key is missing.
    if FRED_API_KEY == "PASTE_YOUR_KEY_HERE" or not FRED_API_KEY:
        raise SystemExit(
            "No API key found.\n\n"
            "Open fred_data.py, find the line that says:\n"
            '    FRED_API_KEY = "PASTE_YOUR_KEY_HERE"\n'
            "and paste your free key between the quotes.\n"
            "Get one in ~2 minutes at https://fredaccount.stlouisfed.org/apikeys"
        )

    # Create the output folder. exist_ok=True means "don't complain if it's
    # already there".
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print(f"Fetching {len(SERIES)} series from FRED...\n")

    # This list will collect each downloaded table so we can merge them later.
    frames = []

    # Loop over the dictionary. .items() gives us both the key and the value.
    for series_id, column_name in SERIES.items():
        title = fetch_series_title(series_id)
        print(f"{series_id}  ({title})")

        df = fetch_series(series_id, column_name)

        # ---- Save this one series to its own CSV. ----
        single_path = os.path.join(OUTPUT_FOLDER, f"{series_id}.csv")
        # index=False stops pandas from writing an extra unnamed counter column.
        df.to_csv(single_path, index=False)
        print(f"  Saved {single_path}\n")

        # Set 'date' as the row label (the "index"). This is what lets pandas
        # line the series up by date automatically in the next step.
        frames.append(df.set_index("date"))

        # Be polite to FRED's servers. Their limit is 120 requests per minute
        # and we're nowhere near it, but pausing is good manners.
        time.sleep(0.3)

    # -----------------------------------------------------------------------
    # STEP 6: Combine everything into one wide table, lined up by date.
    # -----------------------------------------------------------------------
    # pd.concat(..., axis=1) glues the tables together side by side, matching
    # rows on the shared date index. join="outer" keeps EVERY date that appears
    # in ANY series, so nothing is thrown away.
    #
    # Because the series have different frequencies (daily / monthly /
    # quarterly), most rows will have blanks in most columns. That is expected
    # and correct -- real GDP genuinely has no value for a random Tuesday.
    combined = pd.concat(frames, axis=1, join="outer").sort_index()

    combined_path = os.path.join(OUTPUT_FOLDER, "combined_all_series.csv")
    combined.to_csv(combined_path)  # keep the index here: it's the date column
    print(f"Saved combined file: {combined_path}  "
          f"({len(combined):,} rows x {len(combined.columns)} columns)")

    # -----------------------------------------------------------------------
    # STEP 7: Also save a monthly version, which is much easier to eyeball.
    # -----------------------------------------------------------------------
    # resample("ME") regroups the rows into calendar months ("ME" = month end).
    # .last() takes the final observation within each month for each column.
    # Then ffill() ("forward fill") carries the most recent known value forward
    # into months that have none -- this is what makes quarterly GDP show up on
    # every month instead of only 4 times a year.
    #
    # Heads up: forward-filling repeats a value rather than inventing one, but
    # it does mean a GDP figure appears on months it wasn't actually measured.
    # For eyeballing trends that's fine; for serious analysis use the file
    # above instead.
    monthly = combined.resample("ME").last().ffill()

    monthly_path = os.path.join(OUTPUT_FOLDER, "combined_monthly.csv")
    monthly.to_csv(monthly_path)
    print(f"Saved monthly file:  {monthly_path}  "
          f"({len(monthly):,} rows x {len(monthly.columns)} columns)")

    # -----------------------------------------------------------------------
    # STEP 8: Print the last few rows so you can see it worked.
    # -----------------------------------------------------------------------
    print("\nMost recent 6 months:\n")
    print(monthly.tail(6).to_string())
    print("\nDone. Your CSVs are in the '{}' folder.".format(OUTPUT_FOLDER))


# This line means "only run main() if this file was executed directly".
# It's a standard Python convention. If someone imports this file to reuse
# fetch_series(), main() won't fire unexpectedly.
if __name__ == "__main__":
    main()
