#!/usr/bin/env bash
# One-shot setup and launcher for the prospector UI.
#
# Checks Python, installs the one library that is needed, remembers your API
# key, and starts the local web UI. Safe to re-run; after the first time it
# skips straight to starting the server.
#
#   bash tools/start.sh
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPO_ROOT="$(pwd)"
KEY_FILE="$REPO_ROOT/.places-api-key"
PORT="${PORT:-8000}"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
warn() { printf '\033[33m%s\033[0m\n' "$1"; }
fail() { printf '\033[31m%s\033[0m\n' "$1" >&2; exit 1; }

# ---------------------------------------------------------------- environment
# ChromeOS runs Linux in a container whose loopback the Chrome browser cannot
# reach, so there we bind to all interfaces and hand out the container's
# hostname instead of localhost.
if [ -e /dev/.cros_milestone ]; then
  IS_CROSTINI=1
  BIND_HOST="0.0.0.0"
  OPEN_URL="http://penguin.linux.test:$PORT"
else
  IS_CROSTINI=0
  BIND_HOST="127.0.0.1"
  OPEN_URL="http://127.0.0.1:$PORT"
fi

bold "Prospector setup"
echo

# --------------------------------------------------------------------- python
command -v python3 >/dev/null 2>&1 || fail \
  "Python 3 is not installed. On Debian/Ubuntu/ChromeOS run:
    sudo apt-get update && sudo apt-get install -y python3"

PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "  Python $PYV found"

# ------------------------------------------------------------------- requests
# Debian 12 marks its Python as externally managed, so plain pip refuses to
# install. The distro package is the path of least resistance; fall back to pip
# only if that is unavailable.
if python3 -c 'import requests' 2>/dev/null; then
  echo "  requests already installed"
else
  echo "  installing the 'requests' library (needs your password on some systems)..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y -qq python3-requests
  elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --quiet requests || pip3 install --quiet --break-system-packages requests
  else
    fail "Could not install 'requests'. Install pip, then run: pip3 install requests"
  fi
  python3 -c 'import requests' 2>/dev/null || fail "'requests' still will not import."
  echo "  requests installed"
fi

# ------------------------------------------------------------------- api key
# Report what landed without putting the whole key in the scrollback.
describe_key() {
  local k="$1" n=${#1}
  if [ "$n" -le 12 ]; then
    echo "$n characters"
  else
    echo "$n characters, ${k:0:6}…${k: -4}"
  fi
}

check_key_shape() {
  # Google API keys are 39 characters starting with AIza. Warn rather than
  # refuse, in case the format ever changes.
  case "$1" in
    AIza*) [ ${#1} -eq 39 ] || warn "  note: usually 39 characters, this is ${#1}." ;;
    *) warn "  note: Google keys normally start with 'AIza' — double-check this one." ;;
  esac
}

if [ -f "$KEY_FILE" ]; then
  GOOGLE_PLACES_API_KEY="$(tr -d '[:space:]' < "$KEY_FILE")"
  echo "  API key loaded from .places-api-key ($(describe_key "$GOOGLE_PLACES_API_KEY"))"
else
  echo
  bold "Paste your Google Places API key, then press Enter."
  echo
  echo "  To paste in this terminal:  Ctrl+Shift+V   (or right-click -> Paste)"
  echo "  Plain Ctrl+V does not work here."
  echo
  echo "  The key is hidden as you paste, so the screen will not change."
  echo "  That is normal. Paste, then press Enter anyway."
  echo
  printf '  Key: '
  read -rs GOOGLE_PLACES_API_KEY || true
  echo

  GOOGLE_PLACES_API_KEY="$(printf '%s' "$GOOGLE_PLACES_API_KEY" | tr -d '[:space:]')"

  if [ -z "$GOOGLE_PLACES_API_KEY" ]; then
    echo
    fail "Nothing was entered.

If pasting will not work at all, put the key in a file instead:
  1. Open the Files app, go to Linux files -> prospector
  2. Right-click -> New -> Text file, name it  .places-api-key
  3. Paste the key in, save, close
  4. Run this again:  bash tools/start.sh"
  fi

  printf '%s' "$GOOGLE_PLACES_API_KEY" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  echo "  Got it: $(describe_key "$GOOGLE_PLACES_API_KEY")"
  check_key_shape "$GOOGLE_PLACES_API_KEY"
  echo "  Saved, so you will not be asked again."
fi
export GOOGLE_PLACES_API_KEY

# --------------------------------------------------------------------- launch
echo
bold "Starting the UI."
echo
bold "  Open this in your browser:  $OPEN_URL"
echo
if [ "$IS_CROSTINI" = "1" ]; then
  echo "  (On a Chromebook use that address, not localhost — the browser and"
  echo "   the Linux container are separate.)"
  echo
fi
echo "  Leave this window open while a run is going. Press Ctrl+C to stop."
echo

exec python3 "$REPO_ROOT/tools/serve.py" \
  --host "$BIND_HOST" --port "$PORT" --no-browser --display-url "$OPEN_URL"
