#!/usr/bin/env bash
# Refresh the network index end to end: pull, collect, build, commit, push.
#
# Runs weekly from launchd (net.kinlane.network-index-refresh, Sunday 02:00 local; the plist is
# beside this script) and by hand. Every step is idempotent; nothing is pushed unless the
# generated files changed. The org listing is asserted complete inside collect.sh, so a partial
# GitHub answer never ships. Only the generated paths are ever staged -- never `git add -A`.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
cd "$REPO"
echo "=== $(date '+%F %T') network index refresh start"

if [ -n "$(git status --porcelain -- README.md apis.yml unlisted.md network providers _tools/last-build.json)" ]; then
  echo "generated files are dirty from an earlier run; refusing to build on top of them" >&2
  git status --short -- README.md apis.yml unlisted.md network providers _tools/last-build.json >&2
  exit 1
fi
git fetch -q origin
git checkout -q main
git pull -q --ff-only origin main

before=$(python3 -c "import json;print(json.load(open('$HERE/last-build.json'))['providers_listed'])" 2>/dev/null || echo 0)
bash "$HERE/collect.sh"
python3 "$HERE/build.py" --write
after=$(python3 -c "import json;print(json.load(open('$HERE/last-build.json'))['providers_listed'])")

git add README.md apis.yml .gitignore unlisted.md network providers _tools/last-build.json
if git diff --cached --quiet; then
  echo "no change: $after providers listed"
else
  added=$(git diff --cached -U0 -- network | grep -c '^+- name:' || true)
  removed=$(git diff --cached -U0 -- network | grep -c '^-- name:' || true)
  git commit -q -m "Index refresh $(date +%F): $after providers (+$added / -$removed, was $before)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
  git push -q origin main
  echo "pushed: $after providers (+$added / -$removed)"
fi
echo "=== $(date '+%F %T') network index refresh done"
