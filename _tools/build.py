#!/usr/bin/env python3
"""Build the API Evangelist Network index from the inputs collect.sh gathered.

The GitHub org is the membership authority: every public repo named for a provider is
in the index. Each entry links the provider's APIs.io page (by aid, which is the page
slug), its GitHub repo, and its apis.yml in the profile store (artifacts.apis.io).

Writes, in the repo root:
  apis.yml              the APIs.json network index: `include` -> one shard per letter
  network/<shard>.yml   each shard `include`s every provider's apis.yml in that range
  providers/<shard>.md  the same providers as a readable table, linked to APIs.io
  README.md             the index of shards plus the org-wide counts
  unlisted.md           repos in the org that have no live APIs.io page (the gap)

Deterministic: same inputs, same bytes. Dry run prints the counts; --write writes.
"""
import collections
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IN = os.path.join(HERE, "inputs")

ORG = "api-evangelist"
RAW = f"https://raw.githubusercontent.com/{ORG}/api-evangelist-network/refs/heads/main"
STORE = "https://artifacts.apis.io"
APISIO = "https://apis.io/providers"
SPEC_VERSION = "0.23"
CREATED = "2026-02-27"
MAX_SHARD = 2200          # rows per shard; keeps every generated file well under GitHub's 512 KB render limit

# Repos in the org that are NOT providers: the tools, sites and data that run the network.
# profiles-audit-org.py in the engine carries the same rule; keep the two in step.
CORE_HINTS = {
    "0-working", "harvest-backlog", "claude-skills", "claude-memory", "admin",
    "kin-score", "api-evangelist-branding", "papers", "providers", "apis",
    "api-commons", "apis-io", "research", "email", "roadmap", "network",
    # the api-evangelist/* working checkouts (2026-11-06)
    "api-evangelist-chat", "api-evangelist-mcp", "api-evangelist-network", "apievangelist-aws",
    "blogs", "books", "chats", "checklists", "cloudflare-worker", "conversations", "developer",
    "drafts-held", "enrichment-run-history", "experiences", "extensions", "faq", "goal-hypermedia",
    "guidance", "headers", "info", "lifecycle", "me", "media-card", "model", "newsletter-mining",
    "newsletters", "overlays", "policies", "posts", "properties", "questions", "regulations",
    "reports", "rules", "run-history-kin-working", "run-history-kin-working-claude", "schema",
    "scripts", "shorts", "solutions", "standards", "store", "strategies", "tools",
    "unpublished-provider-bundles", "videos", "vocabularies", "working",
    # gateway demos built on the Open-Meteo API; open-meteo itself is a provider
    "open-meteo-tyk-demo", "open-meteo-krakend", "open-meteo-agentgateway", "open-meteo-gateways-deploy",
    # playbooks, city guides and site indexes, not providers
    "academic-research", "nyc",
}


# First-party properties are not providers either (Kin, 2026-07): API Evangelist's own sites and
# tools, APIs.json, the API Pulse, Naftiko. apievangelist.com fronts those.
FIRST_PARTY_PREFIXES = ("api-evangelist", "apis-io", "apis-json", "apisjson", "api-pulse", "naftiko", "info-", "agent-sites", "_", ".")


def core_repo(name, aid=None):
    if name in CORE_HINTS:
        return True
    if aid and aid.startswith("api-evangelist"):
        return True
    return name.startswith(FIRST_PARTY_PREFIXES) or name.endswith(
        ("-site", "-aws", ".github", ".github.io"))


def read_lines(fn):
    with open(os.path.join(IN, fn), encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f if l.strip()]


def read_tsv(fn):
    out = {}
    for l in read_lines(fn):
        k, _, v = l.partition("\t")
        if k and v:
            out[k] = v.strip()
    return out


def yq(s):
    """Quote a YAML scalar unless it is plainly safe."""
    plain = re.fullmatch(r"[A-Za-z][A-Za-z0-9 ._()&+/-]*", s) and s.lower() not in (
        "yes", "no", "true", "false", "null", "on", "off", "y", "n")
    return s if plain else "'" + s.replace("'", "''") + "'"


def shard_key(name):
    c = name[0].lower()
    if c.isdigit():
        return "0-9"
    if "a" <= c <= "z":
        return c
    return "other"


def split_shards(groups):
    """groups: key -> sorted entries. Splits any group over MAX_SHARD by second character
    into contiguous runs, named like `s-a-m`. Returns ordered list of (shard_id, entries)."""
    out = []
    for key in sorted(groups):
        ents = groups[key]
        if len(ents) <= MAX_SHARD or len(key) > 1:
            out.append((key, ents))
            continue
        by2 = collections.OrderedDict()
        for e in ents:
            c2 = e["repo"][1:2].lower()
            if not ("a" <= c2 <= "z"):
                c2 = "0"
            by2.setdefault(c2, []).append(e)
        run, run_start = [], None
        for c2, es in by2.items():
            if run and len(run) + len(es) > MAX_SHARD:
                out.append((f"{key}-{run_start}-{prev}", run))
                run, run_start = [], None
            if run_start is None:
                run_start = c2
            run.extend(es)
            prev = c2
        if run:
            out.append((f"{key}-{run_start}-{prev}", run))
    return out


def shard_label(sid):
    if sid == "0-9":
        return "0-9"
    if sid == "other":
        return "Other"
    parts = sid.split("-")
    if len(parts) == 1:
        return sid.upper()
    a, b, c = parts
    return f"{a.upper()}{b}-{a.upper()}{c}"


def main():
    write = "--write" in sys.argv
    today = datetime.date.today().isoformat()

    repos = [json.loads(l) for l in read_lines("org-repos.jsonl")]
    store = set(read_lines("store-slugs.txt"))
    built = set(read_lines("built-slugs.txt"))
    tomb_title = read_tsv("built-tombstones.tsv")
    tomb = set(tomb_title)
    live = built - tomb
    built_names = read_tsv("built-names.tsv")
    local_names = read_tsv("local-names.tsv")
    skip = set(read_lines("skip-slugs.txt"))
    aid = {}
    for l in read_lines("aid-map.txt"):
        k, _, v = l.partition(" ")
        if k and v:
            aid[k] = v.strip()

    entries, core, retired, forks = [], [], [], []
    no_page, unprofiled = [], []
    for r in repos:
        name = r["name"]
        if core_repo(name, aid.get(name)):
            core.append(name)
            continue
        if name in skip:
            retired.append(name)
            continue
        if r.get("fork"):
            forks.append(name)
        a = aid.get(name, name)
        page = None
        if a in live:
            page = a
        elif name in live:
            page = name
        display = built_names.get(page or "", "") or local_names.get(name, "") or name
        display = display.replace("|", "/").strip()
        e = {"repo": name, "aid": a, "page": page, "name": display,
             "in_store": name in store, "archived": bool(r.get("archived")),
             "description": (r.get("description") or "").strip()}
        if page:
            entries.append(e)
        elif name in store or name in built:
            no_page.append(e)
        else:
            unprofiled.append(e)

    entries.sort(key=lambda e: (e["repo"].lower(), e["repo"]))
    groups = collections.defaultdict(list)
    for e in entries:
        groups[shard_key(e["repo"])].append(e)
    shards = split_shards(groups)

    counts = {
        "org_public_repos": len(repos),
        "providers_listed": len(entries),
        "listed_in_store": sum(1 for e in entries if e["in_store"]),
        "listed_not_in_store": sum(1 for e in entries if not e["in_store"]),
        "listed_archived": sum(1 for e in entries if e["archived"]),
        "aid_differs_from_repo": sum(1 for e in entries if e["aid"] != e["repo"]),
        "page_is_repo_not_aid": sum(1 for e in entries if e["page"] == e["repo"] != e["aid"]),
        "profiled_no_live_page": len(no_page),
        "unprofiled": len(unprofiled),
        "retired_or_delisted": len(retired),
        "core_repos": len(core),
        "forks_listed": len(forks),
        "shards": len(shards),
    }
    print(json.dumps(counts, indent=2))
    print("shards:", ", ".join(f"{sid}={len(es)}" for sid, es in shards))
    if not write:
        print("(dry run -- pass --write)")
        return

    os.makedirs(os.path.join(ROOT, "network"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "providers"), exist_ok=True)
    for d in ("network", "providers"):
        for f in os.listdir(os.path.join(ROOT, d)):
            os.remove(os.path.join(ROOT, d, f))

    # --- shards -----------------------------------------------------------------
    for sid, es in shards:
        label = shard_label(sid)
        y = [
            f"name: API Evangelist Network — providers {label}",
            f"description: {yq(f'The {len(es)} API providers in the API Evangelist network whose repository name begins with {label}. Each include points at the provider apis.yml in the profile store; x-apis-io is the provider page on APIs.io and x-github the repository.')}",
            f"url: {RAW}/network/{sid}.yml",
            f"created: '{CREATED}'",
            f"modified: '{today}'",
            f"specificationVersion: '{SPEC_VERSION}'",
            "tags:",
            "- Directory",
            "- Index",
            "- Network",
            "include:",
        ]
        for e in es:
            y.append(f"- name: {yq(e['name'])}")
            y.append(f"  url: {STORE}/{e['repo']}/apis.yml")
            y.append(f"  x-apis-io: {APISIO}/{e['page']}/")
            y.append(f"  x-github: https://github.com/{ORG}/{e['repo']}")
            if not e["in_store"]:
                y.append("  x-store: pending  # page is live; the apis.yml has not reached the profile store yet")
        with open(os.path.join(ROOT, "network", f"{sid}.yml"), "w", encoding="utf-8") as f:
            f.write("\n".join(y) + "\n")

        m = [
            f"# API Evangelist Network — providers {label}",
            "",
            f"{len(es):,} providers whose repository name begins with **{label}**. Each links to the provider's page on APIs.io, "
            f"where the profile, the rating and every artifact are published, and to the GitHub repository that is the public "
            f"record for corrections. Machine-readable: [network/{sid}.yml](../network/{sid}.yml).",
            "",
            "[← All providers](../README.md)",
            "",
            "| Provider | APIs.io | GitHub |",
            "|---|---|---|",
        ]
        for e in es:
            m.append(f"| {e['name']} | [{e['page']}]({APISIO}/{e['page']}/) | [{e['repo']}](https://github.com/{ORG}/{e['repo']}) |")
        with open(os.path.join(ROOT, "providers", f"{sid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(m) + "\n")

    # --- root apis.yml ------------------------------------------------------------
    y = [
        "name: API Evangelist Network",
        f"description: {yq(f'The network index of every API provider profiled by API Evangelist: {len(entries)} providers, one GitHub repository each in the api-evangelist organization, published on APIs.io. The index is sharded by the first letter of the repository name; each include below is an apis.yml that in turn includes every provider apis.yml in its range.')}",
        "image: https://kinlane-images.s3.amazonaws.com/shared/apis-json/apis-json-logo.jpg",
        f"url: {RAW}/apis.yml",
        f"created: '{CREATED}'",
        f"modified: '{today}'",
        f"specificationVersion: '{SPEC_VERSION}'",
        "tags:",
        "- Directory",
        "- Index",
        "- Network",
        "maintainers:",
        "- FN: API Evangelist",
        "  email: info@apievangelist.com",
        "  url: https://apievangelist.com",
        "include:",
    ]
    for sid, es in shards:
        y.append(f"- name: {yq('Providers ' + shard_label(sid))}")
        y.append(f"  url: {RAW}/network/{sid}.yml")
    with open(os.path.join(ROOT, "apis.yml"), "w", encoding="utf-8") as f:
        f.write("\n".join(y) + "\n")

    # --- unlisted.md ----------------------------------------------------------------
    u = [
        "# In the organization, not on APIs.io",
        "",
        f"Repositories in the `{ORG}` GitHub organization that are named for a provider but have no live provider page on APIs.io "
        f"as of {today}. They are not in the index until a page exists. Infrastructure repositories (the sites, tools and data "
        f"that run the network) and retired or delisted companies are excluded here and from the index.",
        "",
        f"## Profiled, but no live page ({len(no_page):,})",
        "",
        "Artifacts exist in the profile store or a page was built once, but the page is missing or now redirects.",
        "",
        "| Repository | aid | Page | In store | Archived |",
        "|---|---|---|---|---|",
    ]
    for e in sorted(no_page, key=lambda e: e["repo"]):
        why = tomb_title.get(e["aid"]) or tomb_title.get(e["repo"]) or "not built"
        u.append(f"| [{e['repo']}](https://github.com/{ORG}/{e['repo']}) | {e['aid']} | {why} | {'yes' if e['in_store'] else 'no'} | {'yes' if e['archived'] else ''} |")
    u += ["", f"## Never profiled ({len(unprofiled):,})", "", "A repository exists but nothing has been published for it.", "",
          "| Repository | Description | Archived |", "|---|---|---|"]
    for e in sorted(unprofiled, key=lambda e: e["repo"]):
        u.append(f"| [{e['repo']}](https://github.com/{ORG}/{e['repo']}) | {e['description'][:120].replace('|', '/')} | {'yes' if e['archived'] else ''} |")
    with open(os.path.join(ROOT, "unlisted.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(u) + "\n")

    # --- README.md ------------------------------------------------------------------
    r = [
        "# API Evangelist Network",
        "",
        f"The index of every API provider in the [`{ORG}`](https://github.com/{ORG}) GitHub organization. Each provider has one "
        "repository here, named for its slug, and one page on [APIs.io](https://apis.io) where the profile, the Kin Score and every "
        "artifact are published. This repository is the directory that ties the two together, as an "
        "[APIs.json](https://apisjson.org) network index and as a readable listing.",
        "",
        "## The numbers",
        "",
        "| | |",
        "|---|---:|",
        f"| Public repositories in the organization | {counts['org_public_repos']:,} |",
        f"| Providers in this index (live APIs.io page) | **{counts['providers_listed']:,}** |",
        f"| … of which the store copy of apis.yml is still syncing (`x-store: pending`) | {counts['listed_not_in_store']:,} |",
        f"| Profiled, but no live APIs.io page | {counts['profiled_no_live_page']:,} |",
        f"| Never profiled | {counts['unprofiled']:,} |",
        f"| Retired into another provider, or delisted on request | {counts['retired_or_delisted']:,} |",
        f"| Infrastructure repositories (not providers) | {counts['core_repos']:,} |",
        f"| Last built | {today} |",
        "",
        "The two gap rows are itemized in [unlisted.md](unlisted.md).",
        "",
        "## Machine-readable index",
        "",
        "[`apis.yml`](apis.yml) is an APIs.json index whose `include` list points at one shard per letter under "
        "[`network/`](network/). Each shard `include`s every provider's own `apis.yml` in the profile store at "
        "`https://artifacts.apis.io/<slug>/apis.yml`, with `x-apis-io` (the provider page) and `x-github` (the repository) "
        "on every entry. Resolve the root, then the shards, and you have every provider's APIs.json.",
        "",
        "```",
        f"{RAW}/apis.yml",
        "```",
        "",
        "## Every provider",
        "",
        f"{counts['providers_listed']:,} providers, listed by the first letter of the repository name. GitHub will not render a "
        "single file that long, so the listing is one page per letter; together they are the complete list.",
        "",
        "| Letter | Providers | Listing | APIs.json |",
        "|---|---:|---|---|",
    ]
    for sid, es in shards:
        r.append(f"| {shard_label(sid)} | {len(es):,} | [providers/{sid}.md](providers/{sid}.md) | [network/{sid}.yml](network/{sid}.yml) |")
    r += [
        "",
        "## How this is built",
        "",
        "Three sources, each the authority for one thing, and nothing is listed unless all three agree:",
        "",
        "- **GitHub** says which repositories exist. The organization listing is the membership.",
        "- **The profile store** (`artifacts.apis.io`) holds each provider's artifacts; the entry's `url` points there.",
        "- **APIs.io** publishes the page. A provider is listed only when its page exists in the APIs.io build, under its `aid`, "
        "which is the page slug. The build runs ahead of the deploy, so about one page in a hundred may return 404 until the next site push.",
        "",
        "Retired slugs (merged into a survivor) and companies delisted at their own request are never listed. "
        "Infrastructure repositories in the organization are excluded by name.",
        "",
        "```",
        "_tools/collect.sh          # gather the inputs (gh, aws s3api, the local apis.io build)",
        "_tools/build.py --write    # regenerate apis.yml, network/, providers/, unlisted.md, README.md",
        "```",
        "",
        "## Corrections",
        "",
        "A provider missing here, listed wrongly, or pointing at the wrong page: "
        f"[open an issue](https://github.com/{ORG}/api-evangelist-network/issues/new). Anything about a single provider's "
        "profile or rating belongs on that provider's own repository, which every row links. Removal requests are honored; "
        "see [where our data comes from](https://apievangelist.com/about/where-our-data-comes-from).",
    ]
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(r) + "\n")

    with open(os.path.join(HERE, "last-build.json"), "w", encoding="utf-8") as f:
        json.dump({"built": today, **counts}, f, indent=2)
    print("written")


if __name__ == "__main__":
    main()
