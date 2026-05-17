#!/usr/bin/env bash
# Interactive setup for the Instagram → Notion sync system.
# Run once from the instagram-notion-sync directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/launchd/com.wintermute.instagram-sync.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.wintermute.instagram-sync.plist"
VENV_DIR="$SCRIPT_DIR/.venv"

print_step() { echo -e "\n\033[1;34m▶ $1\033[0m"; }
print_ok()   { echo -e "  \033[1;32m✓\033[0m $1"; }
print_warn() { echo -e "  \033[1;33m!\033[0m $1"; }

# ── 1. Python virtualenv ──────────────────────────────────────────────────────

print_step "Creating Python virtualenv at .venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
print_ok "Dependencies installed"

# ── 2. config.env ─────────────────────────────────────────────────────────────

if [ ! -f "$SCRIPT_DIR/config.env" ]; then
  print_step "Creating config.env from template"
  cp "$SCRIPT_DIR/config.example.env" "$SCRIPT_DIR/config.env"
  print_warn "Edit $SCRIPT_DIR/config.env and fill in your credentials before continuing."
  print_warn "Re-run this script after editing."
  exit 0
fi

# Source the config to validate required keys
print_step "Validating config.env"
set -a; source "$SCRIPT_DIR/config.env"; set +a

MISSING=0
for VAR in IG_SESSION_ID IG_CSRF_TOKEN IG_DS_USER_ID NOTION_TOKEN NOTION_SAVES_DB_ID; do
  if [ -z "${!VAR:-}" ] || [[ "${!VAR}" == *REPLACE_ME* ]] || [[ "${!VAR}" == your_* ]]; then
    print_warn "Not set: $VAR"
    MISSING=$((MISSING + 1))
  else
    print_ok "$VAR is set"
  fi
done

if [ "$MISSING" -gt 0 ]; then
  print_warn "$MISSING required variable(s) not configured. Edit config.env and re-run."
  exit 1
fi

# ── 3. Install launchd plist ──────────────────────────────────────────────────

print_step "Installing launchd plist"

PYTHON_BIN="$VENV_DIR/bin/python3"
SYNC_SCRIPT="$SCRIPT_DIR/sync.py"

# Write final plist, substituting real values
sed \
  -e "s|/Users/YOU/Projects/wintermute/instagram-notion-sync/.venv/bin/python3|$PYTHON_BIN|g" \
  -e "s|/Users/YOU/Projects/wintermute/instagram-notion-sync/sync.py|$SYNC_SCRIPT|g" \
  -e "s|<key>IG_SESSION_ID</key>.*$|<key>IG_SESSION_ID</key>|" \
  "$PLIST_SRC" > /tmp/instagram-sync-rendered.plist

# Use Python to inject env vars cleanly (avoids quoting issues with sed)
"$PYTHON_BIN" - <<PYEOF
import plistlib, os

with open('/tmp/instagram-sync-rendered.plist', 'rb') as f:
    plist = plistlib.load(f)

env = plist.setdefault('EnvironmentVariables', {})
for key in ['IG_SESSION_ID', 'IG_CSRF_TOKEN', 'IG_DS_USER_ID', 'NOTION_TOKEN', 'NOTION_SAVES_DB_ID']:
    env[key] = os.environ[key]

log_dir = os.path.expanduser('~/Library/Logs')
os.makedirs(log_dir, exist_ok=True)
plist['StandardOutPath'] = f'{log_dir}/wintermute-instagram-sync.log'
plist['StandardErrorPath'] = f'{log_dir}/wintermute-instagram-sync-error.log'

with open('$PLIST_DST', 'wb') as f:
    plistlib.dump(plist, f)

print('  Plist written to $PLIST_DST')
PYEOF

# Unload first if already loaded (ignore errors)
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
print_ok "launchd agent loaded (runs at 09:00 and 21:00)"

# ── 4. Smoke test ─────────────────────────────────────────────────────────────

print_step "Smoke test — running sync.py once now"
set -a; source "$SCRIPT_DIR/config.env"; set +a
"$PYTHON_BIN" "$SYNC_SCRIPT" && print_ok "Sync completed successfully." \
  || print_warn "Sync exited with errors — check sync.log for details."

echo -e "\n\033[1;32mSetup complete.\033[0m"
echo "  Sync log:   $SCRIPT_DIR/sync.log"
echo "  State file: $SCRIPT_DIR/state.json"
echo "  Ideation:   python $SCRIPT_DIR/ideate.py [--limit N] [--dry-run]"
