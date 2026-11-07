#!/usr/bin/env bash
# Gather the inputs build.py reads, into _tools/inputs/ (gitignored).
#
#   org-repos.jsonl      every public repo in the api-evangelist org (GitHub is the membership authority)
#   store-slugs.txt      every provider prefix in the S3 profile store (the artifact authority)
#   built-slugs.txt      every provider page the apis.io build produced (the page authority)
#   built-names.tsv      page slug -> display name, from those pages
#   built-tombstones.tsv pages that are only a "Moved to ..." redirect (slug, title)
#   aid-map.txt          repo slug -> aid, from the cached all/<slug>/apis.yml (aid is the apis.io page slug)
#   local-names.tsv      repo slug -> name, from the cached apis.yml (fallback when there is no page)
#   skip-slugs.txt       retired + delisted slugs (engine/lib_retired.py); never listed
#   vc-slugs.txt         investor pages the apis.io build renders under /vcs/ (not providers)
#
# Everything here is read-only. Run from anywhere; paths are absolute.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
IN="$HERE/inputs"; mkdir -p "$IN"
GH_ROOT="${GH_ROOT:-$HOME/Github}"
ALL="${ALL:-$GH_ROOT/all}"
BUILT="${BUILT:-$GH_ROOT/api-search/providers/_providers}"
ENGINE="${ENGINE:-$GH_ROOT/engine}"

echo "org repos (gh, ~415 pages) ..."
gh api --paginate 'orgs/api-evangelist/repos?per_page=100&type=public' \
  --jq '.[] | {name, description, pushed_at, archived, fork, private, size, html_url}' > "$IN/org-repos.jsonl"
EXPECTED=$(gh api orgs/api-evangelist --jq '.public_repos')
GOT=$(wc -l < "$IN/org-repos.jsonl" | tr -d ' ')
echo "  $GOT repos listed; org reports $EXPECTED public"
[ "$GOT" -eq "$EXPECTED" ] || { echo "  INCOMPLETE org listing -- refusing to build from it" >&2; exit 1; }

echo "store prefixes (s3) ..."
aws s3api list-objects-v2 --bucket api-evangelist-profiles --prefix providers/ --delimiter / \
  --query 'CommonPrefixes[].Prefix' --output text | tr '\t' '\n' | sed -E 's#^providers/##; s#/$##' | sort > "$IN/store-slugs.txt"
echo "  $(wc -l < "$IN/store-slugs.txt") prefixes"

echo "built pages ..."
ls "$BUILT" | sed 's/\.md$//' | sort > "$IN/built-slugs.txt"
( cd "$BUILT" && find . -maxdepth 1 -name '*.md' -print0 | xargs -0 grep -H -m1 -E '^name:' ) \
  | sed -E 's#^\./(.*)\.md:name: *#\1\t#' | sed -E "s/^([^\t]+)\t[\"']?(.*[^\"'])[\"']?$/\1\t\2/" > "$IN/built-names.tsv"
( cd "$BUILT" && find . -maxdepth 1 -name '*.md' -print0 | xargs -0 grep -H -m1 -E '^title: Moved to' ) \
  | sed -E 's#^\./(.*)\.md:title: *#\1\t#' | sort > "$IN/built-tombstones.tsv"
echo "  $(wc -l < "$IN/built-slugs.txt") pages, $(wc -l < "$IN/built-tombstones.tsv") tombstones"

echo "cached apis.yml (aid + name) ..."
( cd "$ALL" && find . -mindepth 2 -maxdepth 2 -name apis.yml -print0 | xargs -0 grep -H -m1 -E '^aid:' ) \
  | sed -E 's#^\./([^/]+)/apis\.yml:aid: *#\1 #; s/["'"'"']//g' > "$IN/aid-map.txt"
( cd "$ALL" && find . -mindepth 2 -maxdepth 2 -name apis.yml -print0 | xargs -0 grep -H -m1 -E '^name:' ) \
  | sed -E 's#^\./([^/]+)/apis\.yml:name: *#\1\t#' | sed -E "s/^([^\t]+)\t[\"']?(.*[^\"'])[\"']?$/\1\t\2/" > "$IN/local-names.tsv"

echo "investor pages (/vcs/) ..."
ls "${VCS:-$GH_ROOT/api-search/vcs/_vcs}" | sed 's/\.md$//' | sort > "$IN/vc-slugs.txt"
echo "  $(wc -l < "$IN/vc-slugs.txt") investors"

echo "retired + delisted ..."
python3 "$ENGINE/lib_retired.py" --list | sort > "$IN/skip-slugs.txt"
echo "  $(wc -l < "$IN/skip-slugs.txt") slugs never listed"
echo "done -> $IN"
