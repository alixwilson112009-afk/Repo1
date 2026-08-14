#!/usr/bin/env python3
"""
Diagnose a Google Places API key and say, in plain words, what to fix.

    python3 tools/checkkey.py

Reads .places-api-key (or GOOGLE_PLACES_API_KEY), checks its shape, makes one
cheap Places call, and translates whatever comes back into the actual next step.
Stdlib only, so it works before anything is installed.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"

# reason -> (what it means, what to do about it)
DIAGNOSES = {
    "API_KEY_INVALID": (
        "Google does not recognise this key string.",
        [
            "Most often the key was copied incompletely — check the length above.",
            "Re-copy it from Google Cloud Console -> APIs & Services -> Credentials",
            "  (click the copy icon next to the key rather than selecting the text).",
            "A brand new key can take up to 5 minutes to start working.",
            "Then delete .places-api-key and run: bash tools/start.sh",
        ],
    ),
    "API_KEY_SERVICE_BLOCKED": (
        "The key is real, but it is not allowed to call the Places API.",
        [
            "Google Cloud Console -> APIs & Services -> Credentials -> click your key",
            "Under 'API restrictions', either pick 'Don't restrict key',",
            "  or select 'Places API (New)' in the list.",
            "Save, wait a minute, try again.",
        ],
    ),
    "SERVICE_DISABLED": (
        "Places API (New) is not switched on for this project.",
        [
            "Google Cloud Console -> APIs & Services -> Library",
            "Search for 'Places API (New)' — the one with (New) in the name.",
            "Click it, then click Enable. Wait a minute, try again.",
        ],
    ),
    "BILLING_DISABLED": (
        "The project has no billing account attached.",
        [
            "Google requires a card on file even for the free tier.",
            "Google Cloud Console -> Billing -> link a billing account.",
            "You still get the monthly free credit; the card is for overage.",
        ],
    ),
    "API_KEY_HTTP_REFERRER_BLOCKED": (
        "The key is restricted to websites, so a script cannot use it.",
        [
            "Console -> Credentials -> your key -> 'Application restrictions'",
            "Set it to 'None'. (Or 'IP addresses' with this machine's IP.)",
        ],
    ),
    "API_KEY_IP_ADDRESS_BLOCKED": (
        "The key is restricted to IP addresses that do not include this machine.",
        [
            "Console -> Credentials -> your key -> 'Application restrictions'",
            "Set it to 'None', or add this machine's public IP to the list.",
        ],
    ),
    "API_KEY_ANDROID_APP_BLOCKED": (
        "The key is restricted to Android apps, so a script cannot use it.",
        ["Console -> Credentials -> your key -> Application restrictions -> None."],
    ),
    "API_KEY_IOS_APP_BLOCKED": (
        "The key is restricted to iOS apps, so a script cannot use it.",
        ["Console -> Credentials -> your key -> Application restrictions -> None."],
    ),
}


def load_key():
    for path in (Path(".places-api-key"), Path(__file__).resolve().parent.parent / ".places-api-key"):
        if path.exists():
            return path.read_text().strip(), str(path)
    env = os.environ.get("GOOGLE_PLACES_API_KEY")
    if env:
        return env.strip(), "GOOGLE_PLACES_API_KEY"
    return None, None


def describe(key):
    print(f"  length          {len(key)} characters" + ("  (expected 39)" if len(key) != 39 else "  ✓"))
    print(f"  starts with     {key[:4]!r}" + ("  ✓" if key.startswith("AIza") else "  (expected 'AIza')"))
    print(f"  preview         {key[:6]}…{key[-4:]}" if len(key) > 12 else "  preview      (too short to mask)")

    problems = []
    if len(key) != 39:
        problems.append(
            "The length is wrong. A Google API key is exactly 39 characters, so this "
            "one looks " + ("cut short" if len(key) < 39 else "too long") + "."
        )
    if not key.startswith("AIza"):
        problems.append("Google API keys start with 'AIza'. This does not, so it may be a different credential.")
    if any(c in key for c in "\"' "):
        problems.append("There are quotes or spaces in the key — remove them.")
    return problems


def main():
    key, source = load_key()
    if not key:
        sys.exit(
            "No key found.\n"
            "Expected a file called .places-api-key in the prospector folder,\n"
            "or the GOOGLE_PLACES_API_KEY variable to be set."
        )

    print(f"\nChecking the key from {source}\n")
    problems = describe(key)

    if problems:
        print("\nProblems with the key itself:")
        for p in problems:
            print(f"  - {p}")
        print("\nFix that first — delete .places-api-key and run: bash tools/start.sh")
        if len(key) < 20:
            return 1  # too mangled for a live test to add anything

    print("\nAsking Google to test it...\n")
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"textQuery": "coffee shop"}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": "places.id",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            json.load(resp)
        print("  THE KEY WORKS. Places answered normally.")
        print("\n  Go back to the UI and start your run.")
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error", {})
        except json.JSONDecodeError:
            print(f"  HTTP {exc.code}: {body[:400]}")
            return 1

        reasons = [d.get("reason") for d in err.get("details", []) if d.get("reason")]
        print(f"  Google said: {err.get('status', exc.code)}")
        if err.get("message"):
            print(f"  {err['message'][:300]}")

        for reason in reasons:
            if reason in DIAGNOSES:
                meaning, steps = DIAGNOSES[reason]
                print(f"\n  WHAT IT MEANS: {meaning}\n\n  HOW TO FIX IT:")
                for step in steps:
                    print(f"    {step}")
                return 1
        if reasons:
            print(f"\n  Reason code: {', '.join(reasons)} (not one I have advice for)")
        return 1
    except urllib.error.URLError as exc:
        print(f"  Could not reach Google: {exc.reason}")
        print("  Check the Chromebook's internet connection and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
