#!/bin/bash
# Sync the portfolio's public files from Portfolio_2026 into this deploy repo
# and push them live to Railway. Safe to run repeatedly (no-op when nothing
# changed). Called by "Publish to Live.command" and by the optional watcher.
set -euo pipefail

SRC="/Users/natalycetrenatalycetre/Documents/CLAUDE/Portfolio_2026"
DST="/Users/natalycetrenatalycetre/Documents/CLAUDE/Nate-Portfolio"
RAILWAY="/Users/natalycetrenatalycetre/.local/bin/railway"
GIT="/usr/bin/git"
RSYNC="/usr/bin/rsync"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# Railway CLI refuses to run when these agent env vars are set; strip them.
run_railway() { env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT "$RAILWAY" "$@"; }

log "Syncing public files from Portfolio_2026 ..."
# Published case-study JSONs (what changes when you publish/update a case study).
"$RSYNC" -a --delete \
  "$SRC/case-studies/published/" "$DST/case-studies/published/"
# Public assets (fonts, CV, case-study images). No --delete: keep the deploy
# copy even if a source image is temporarily missing.
"$RSYNC" -a "$SRC/assets/" "$DST/assets/"
# portfolio-config.json (identity/nav/about/contact) in case it was edited.
"$RSYNC" -a "$SRC/portfolio-config.json" "$DST/portfolio-config.json"
# NOTE: index.html is intentionally NOT synced here — the deploy copy keeps the
# one delta (Lab card links to the live framework). Re-sync it by hand on a
# portfolio design change, preserving that link.

cd "$DST"

if [ -z "$("$GIT" status --porcelain)" ]; then
  log "No changes to publish — site is already up to date. Nothing to do."
  exit 0
fi

log "Committing changes ..."
"$GIT" add -A
"$GIT" -c user.name="cenatdesign-bot" \
       -c user.email="cenatdesign-bot@users.noreply.github.com" \
       commit -q -m "Publish: sync case studies $(date '+%Y-%m-%d %H:%M')"

# Primary deploy path: push to GitHub, which auto-deploys on Railway.
# Fallback (no remote or push fails): upload directly with `railway up`.
if "$GIT" remote get-url origin >/dev/null 2>&1 && \
   GIT_TERMINAL_PROMPT=0 "$GIT" push -q origin main; then
  log "Pushed to GitHub — Railway is auto-deploying."
else
  log "GitHub push unavailable — deploying directly via Railway ..."
  run_railway up --detach --service nate-portfolio
fi

log "Done. Live shortly at https://nate-portfolio-production.up.railway.app"
