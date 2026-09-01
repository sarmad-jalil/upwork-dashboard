# Upwork Dashboard

Scrapes fresh Upwork jobs for a niche you define, filters them, and lets you evaluate each
one or generate a tailored proposal. Runs as **one app on one port**.

- **Profiles tab** — create/select/delete profiles. Each profile is a niche (keywords,
  exclusions, model, min score). The active one drives what gets scraped.
- **Jobs tab** — scrape Upwork for the active profile's niche, then evaluate or write a
  proposal per job.
- **Storage** — Supabase Postgres holds profiles and scraped jobs (latest 50 per profile).

The React build is served by FastAPI, so a single process serves both UI and API.

## Quick start

```bash
cp backend/.env.example backend/.env   # fill in your keys (see table below)
./run.sh                               # http://localhost:8000
```

`run.sh` creates the virtualenv, installs deps, builds the frontend, and starts the server.

| Command | What it does |
|---|---|
| `./run.sh` | Build UI (if needed) + serve everything on `:8000` |
| `./run.sh --fresh` | Force a frontend rebuild first |
| `./run.sh --dev` | API on `:8000` + Vite dev server on `:5173` with hot reload |

## Configuration

Required in `backend/.env`:

| Variable | Needed for |
|---|---|
| `DATABASE_URL` | Supabase Postgres — profiles + saved jobs |
| `APIFY_TOKEN` | Job scraping (paid — the actor bills per run) |
| `GROQ_API_KEY` | Evaluate / Generate Proposal via Groq (free tier) |
| `MISTRAL_API_KEY` | Only if you pick the Mistral model |
| `ANTHROPIC_API_KEY` | Only if you pick the Claude model |

**Supabase setup** — create a project, then Project Settings → **Connect** → Connection
string → URI (use the **Session pooler** string; the direct one is IPv6-only). Put it in
`backend/.env` as `DATABASE_URL`, then run [`backend/supabase/schema.sql`](backend/supabase/schema.sql)
once in the Supabase SQL editor to create the `profiles` and `jobs` tables.

## How it works

1. **Scrape** — `GET /jobs/scrape?profile_id=` runs the
   [`hyperbach/upwork-scraper-ai`](https://apify.com/hyperbach/upwork-scraper-ai) Apify actor
   using the profile's keywords/exclusions/min score, applies hard filters
   (payment-verified, max age, country exclusions), then upserts results into Supabase —
   trimming to the 50 most recent per profile.
2. **Evaluate** — a job card's *Evaluate* button posts that job's real scraped data to
   `POST /job/evaluate` for an Apply/Skip call with green/red flags.
3. **Generate Proposal** — posts the job plus the active profile's niche and experience to
   `POST /proposal/generate`.

Opening the Jobs tab loads a profile's already-saved jobs from Supabase, so you only pay
for a scrape when you actually want fresh results.

## Tuning the job filter

Most filtering now comes from the **active profile** (keywords, exclude keywords, min job
score) — edit those in the Profiles tab, not here.

The values below are the *fallback* stack filter, used only for a scrape with no
`profile_id` (the legacy whole-stack sweep). Hard filters — payment-verified, max age, and
country exclusions — always apply, profile or not. They live in
`backend/api/core/jobs_config.py` and each can be overridden by an env var:

| Env var | Default |
|---|---|
| `JOBS_STACK_KEYWORDS` | react, next.js, node, express, typescript, … (comma-separated) |
| `JOBS_EXCLUDE_ROLE_HINTS` | wix, shopify, squarespace, webflow, … |
| `JOBS_EXCLUDE_COUNTRIES` | israel,isr |
| `JOBS_MAX_AGE_HOURS` | 24 |
| `JOBS_REQUIRE_PAYMENT_VERIFIED` | true |
| `JOBS_CATEGORY_NAME` | Web, Mobile & Software Dev |
| `JOBS_MIN_SCORE` | >=40 |
| `JOBS_DEFAULT_LIMIT` | 50 |

In the no-profile path a job is kept only if it also matches a stack keyword, and
platform-locked roles (Wix/Shopify/etc.) are dropped unless there's a strong React/Node
signal. Those stack-specific rules are skipped for profile-driven scrapes, since the
profile's own keywords already scope the search.

## API

| Endpoint | Purpose |
|---|---|
| `GET /profiles` | List profiles |
| `POST /profiles` | Create a profile |
| `PATCH /profiles/{id}` | Update a profile (partial — omitted fields keep their value) |
| `DELETE /profiles/{id}` | Delete a profile |
| `POST /profiles/{id}/activate` | Make a profile active |
| `GET /profiles/{id}/jobs` | Jobs saved for that profile (newest first) |
| `GET /jobs/scrape?profile_id=&since=&limit=` | Scrape + filter + save. Returns `{ jobs, total_scraped, total_after_filter }` |
| `POST /job/evaluate` | Apply/Skip recommendation with flags and tips |
| `POST /proposal/generate` | Full proposal + opening question + micro-win |
| `POST /profile/analyze` | (unused by the UI) profile scoring |
| `POST /tools/generate-titles` | (unused by the UI) title suggestions |
| `POST /tools/conversion-coach` | (unused by the UI) client-reply coaching |
| `GET /health` | Health check |

Interactive docs at http://localhost:8000/docs.

## Notes

- Scraping costs money per Apify run — use the **Limit** field to keep runs small while testing.
- The Apify actor handles Upwork login/anti-bot internally; no Upwork credentials are stored here.
- `backend/.env` is gitignored. Don't commit it.
