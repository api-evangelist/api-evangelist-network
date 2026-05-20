# API Evangelist Service Provider Index

Generated 2026-05-11 from the [api-evangelist network](https://github.com/api-evangelist/network).

**4,409** API service providers with at least one API defined in their `apis.yml`.
**16,332** total APIs indexed across all providers.

## Files

| File | Format | Use Case |
|---|---|---|
| `service-providers.csv` | CSV | Spreadsheet, BI tools, easy filtering |
| `service-providers.json` | JSON | Programmatic consumption |
| `service-providers.yml` | YAML | Human-readable, apis.json-compatible |

## Schema

Each record has the following fields:

| Field | Description |
|---|---|
| `slug` | URL-safe identifier (matches the github.com/api-evangelist/{slug} repo name) |
| `name` | Provider display name from their apis.yml |
| `description` | One-line description, whitespace-normalized |
| `tags` | Array of tags from apis.yml |
| `repo_url` | GitHub repo URL where the full provider profile lives |
| `api_count` | Number of APIs the provider has indexed in their apis.yml |

## Top 30 tags

| Tag | Provider Count |
|---|---:|
| Open Source | 471 |
| Analytics | 201 |
| Security | 195 |
| AWS | 195 |
| AI | 182 |
| Federal Government | 178 |
| Kubernetes | 150 |
| Enterprise | 137 |
| Automation | 129 |
| Machine Learning | 127 |
| Cloud | 124 |
| Payments | 122 |
| DevOps | 120 |
| Cloud Native | 106 |
| Messaging | 104 |
| Observability | 102 |
| Compliance | 98 |
| Containers | 94 |
| Database | 90 |
| Microservices | 90 |
| Financial Services | 89 |
| Collaboration | 88 |
| Java | 85 |
| Infrastructure | 84 |
| Media | 79 |
| Microsoft | 77 |
| Networking | 77 |
| Developer Tools | 75 |
| Banking | 75 |
| CRM | 72 |

## Notes

- A "service provider" here means an entry whose `apis.yml` lists at least one API. Providers with empty `apis: []` are excluded — they represent companies or topics that have not yet been profiled with concrete APIs.
- Each provider has a full profile at `https://github.com/api-evangelist/{slug}` including OpenAPI specs (where available), capabilities, plans, rate-limits, finops, JSON-LD, vocabulary, and blog feed.
- This index is regenerated weekly. Source of truth: provider apis.yml files.