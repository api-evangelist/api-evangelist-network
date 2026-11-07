# API Evangelist Network

The index of every API provider in the [`api-evangelist`](https://github.com/api-evangelist) GitHub organization. Each provider has one repository here, named for its slug, and one page on [APIs.io](https://apis.io) where the profile, the Kin Score and every artifact are published. This repository is the directory that ties the two together, as an [APIs.json](https://apisjson.org) network index and as a readable listing.

## The numbers

| | |
|---|---:|
| Public repositories in the organization | 41,249 |
| Providers in this index (live APIs.io page) | **38,087** |
| … of which the store copy of apis.yml is still syncing (`x-store: pending`) | 185 |
| Profiled, but no live APIs.io page | 1,535 |
| Never profiled | 0 |
| Retired into another provider, or delisted on request | 1,589 |
| Infrastructure repositories (not providers) | 38 |
| Last built | 2026-11-06 |

The two gap rows are itemized in [unlisted.md](unlisted.md).

## Machine-readable index

[`apis.yml`](apis.yml) is an APIs.json index whose `include` list points at one shard per letter under [`network/`](network/). Each shard `include`s every provider's own `apis.yml` in the profile store at `https://artifacts.apis.io/<slug>/apis.yml`, with `x-apis-io` (the provider page) and `x-github` (the repository) on every entry. Resolve the root, then the shards, and you have every provider's APIs.json.

```
https://raw.githubusercontent.com/api-evangelist/api-evangelist-network/refs/heads/main/apis.yml
```

## Every provider

38,087 providers, listed by the first letter of the repository name. GitHub will not render a single file that long, so the listing is one page per letter; together they are the complete list.

| Letter | Providers | Listing | APIs.json |
|---|---:|---|---|
| 0-9 | 346 | [providers/0-9.md](providers/0-9.md) | [network/0-9.yml](network/0-9.yml) |
| A0-Al | 2,200 | [providers/a-0-l.md](providers/a-0-l.md) | [network/a-0-l.yml](network/a-0-l.yml) |
| Am-As | 2,076 | [providers/a-m-s.md](providers/a-m-s.md) | [network/a-m-s.yml](network/a-m-s.yml) |
| At-Az | 920 | [providers/a-t-z.md](providers/a-t-z.md) | [network/a-t-z.yml](network/a-t-z.yml) |
| B0-Bp | 2,063 | [providers/b-0-p.md](providers/b-0-p.md) | [network/b-0-p.yml](network/b-0-p.yml) |
| Br-Bz | 648 | [providers/b-r-z.md](providers/b-r-z.md) | [network/b-r-z.yml](network/b-r-z.yml) |
| C0-Ck | 1,823 | [providers/c-0-k.md](providers/c-0-k.md) | [network/c-0-k.yml](network/c-0-k.yml) |
| Cl-Ct | 2,156 | [providers/c-l-t.md](providers/c-l-t.md) | [network/c-l-t.yml](network/c-l-t.yml) |
| Cu-Cz | 298 | [providers/c-u-z.md](providers/c-u-z.md) | [network/c-u-z.yml](network/c-u-z.yml) |
| D | 1,584 | [providers/d.md](providers/d.md) | [network/d.yml](network/d.yml) |
| E | 1,208 | [providers/e.md](providers/e.md) | [network/e.yml](network/e.yml) |
| F | 1,288 | [providers/f.md](providers/f.md) | [network/f.yml](network/f.yml) |
| G | 1,299 | [providers/g.md](providers/g.md) | [network/g.yml](network/g.yml) |
| H | 1,042 | [providers/h.md](providers/h.md) | [network/h.yml](network/h.yml) |
| I | 1,031 | [providers/i.md](providers/i.md) | [network/i.yml](network/i.yml) |
| J | 407 | [providers/j.md](providers/j.md) | [network/j.yml](network/j.yml) |
| K | 760 | [providers/k.md](providers/k.md) | [network/k.yml](network/k.yml) |
| L | 1,168 | [providers/l.md](providers/l.md) | [network/l.yml](network/l.yml) |
| M | 1,897 | [providers/m.md](providers/m.md) | [network/m.yml](network/m.yml) |
| N | 1,031 | [providers/n.md](providers/n.md) | [network/n.yml](network/n.yml) |
| O | 1,148 | [providers/o.md](providers/o.md) | [network/o.yml](network/o.yml) |
| P | 2,036 | [providers/p.md](providers/p.md) | [network/p.yml](network/p.yml) |
| Q | 295 | [providers/q.md](providers/q.md) | [network/q.yml](network/q.yml) |
| R | 1,312 | [providers/r.md](providers/r.md) | [network/r.yml](network/r.yml) |
| S0-So | 1,965 | [providers/s-0-o.md](providers/s-0-o.md) | [network/s-0-o.yml](network/s-0-o.yml) |
| Sp-Sy | 1,225 | [providers/s-p-y.md](providers/s-p-y.md) | [network/s-p-y.yml](network/s-p-y.yml) |
| T | 1,867 | [providers/t.md](providers/t.md) | [network/t.yml](network/t.yml) |
| U | 672 | [providers/u.md](providers/u.md) | [network/u.yml](network/u.yml) |
| V | 821 | [providers/v.md](providers/v.md) | [network/v.yml](network/v.yml) |
| W | 787 | [providers/w.md](providers/w.md) | [network/w.yml](network/w.yml) |
| X | 142 | [providers/x.md](providers/x.md) | [network/x.yml](network/x.yml) |
| Y | 182 | [providers/y.md](providers/y.md) | [network/y.yml](network/y.yml) |
| Z | 390 | [providers/z.md](providers/z.md) | [network/z.yml](network/z.yml) |

## How this is built

Three sources, each the authority for one thing, and nothing is listed unless all three agree:

- **GitHub** says which repositories exist. The organization listing is the membership.
- **The profile store** (`artifacts.apis.io`) holds each provider's artifacts; the entry's `url` points there.
- **APIs.io** publishes the page. A provider is listed only when its page exists in the APIs.io build, under its `aid`, which is the page slug. The build runs ahead of the deploy, so about one page in a hundred may return 404 until the next site push.

Retired slugs (merged into a survivor) and companies delisted at their own request are never listed. Infrastructure repositories in the organization are excluded by name.

```
_tools/collect.sh          # gather the inputs (gh, aws s3api, the local apis.io build)
_tools/build.py --write    # regenerate apis.yml, network/, providers/, unlisted.md, README.md
```

## Corrections

A provider missing here, listed wrongly, or pointing at the wrong page: [open an issue](https://github.com/api-evangelist/api-evangelist-network/issues/new). Anything about a single provider's profile or rating belongs on that provider's own repository, which every row links. Removal requests are honored; see [where our data comes from](https://apievangelist.com/about/where-our-data-comes-from).
