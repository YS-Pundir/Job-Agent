# Job Agent — Project Context

## Problem Statement

Manually searching for relevant job listings across multiple platforms is time-consuming and repetitive. Job seekers need to visit Naukri, RemoteOK, and Wellfound individually, apply filters, and sift through results — often missing opportunities due to the overhead.

## Solution

Build a **Job Agent** that automates job discovery across three platforms:

| # | Platform | URL | Scraping Strategy |
|---|----------|-----|-------------------|
| 1 | **Naukri** | https://www.naukri.com | Playwright (headless Chromium) + BeautifulSoup |
| 2 | **RemoteOK** | https://remoteok.com | Public JSON API (`/api` endpoint) |
| 3 | **Wellfound** | https://wellfound.com | Firecrawl (JS-rendered page extraction) |

The agent will:

1. **Accept a job role and location** as explicit CLI arguments.
2. **Fetch listings** from each platform using its designated strategy (see table above).
3. **Normalise** the results into a common schema.
4. **Store** all collected jobs in a single **CSV file** for easy review and filtering.

### CLI Usage

```bash
python -m src.main --role "Product Manager" --location "Bangalore"
python -m src.main --role "Software Engineer" --location "Mumbai"
python -m src.main --role "Data Analyst"   # location is optional
```

### Platform URL Construction

Each scraper uses the role + location to build the correct search URL:

| Platform | URL pattern |
| --- | --- |
| **Naukri** | `naukri.com/<role>-jobs-in-<location>` or `naukri.com/<role>-jobs` |
| **RemoteOK** | `remoteok.com/api` filtered by role keyword |
| **Wellfound** | `wellfound.com/role/l/<role>/<location>` |

## Output Schema (CSV columns)

| Column | Description |
|--------|-------------|
| `title` | Job title |
| `company` | Company name |
| `location` | Job location or "Remote" |
| `url` | Direct link to the listing |
| `source` | Platform name (naukri / remoteok / wellfound) |
| `date_posted` | Posting date (if available) |
| `scraped_at` | Timestamp when the agent collected the listing |

## Key Constraints & Decisions

- **Language**: Python 3.10+
- **Output format**: CSV (one file per run, e.g. `jobs_<timestamp>.csv`)
- **No database** required — CSV is the single source of truth for each run.
- **Rate-limiting / politeness**: respect `robots.txt` and add reasonable delays between requests.
- **Extensibility**: design scrapers behind a common interface so new platforms can be added easily.

## Implementation Phases

### Phase 1 — Project Scaffolding & Core Models

Set up the repository structure, dependencies, and shared data models.

```
job-agent/
├── docs/
│   └── context.md
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry-point
│   ├── models.py            # Job dataclass / schema
│   ├── csv_writer.py        # CSV output logic
│   └── scrapers/
│       ├── __init__.py
│       ├── base.py           # Abstract BaseScraper interface
│       ├── naukri.py         # Phase 2
│       ├── remoteok.py       # Phase 3
│       └── wellfound.py      # Phase 4
├── output/                   # Generated CSV files (gitignored)
├── requirements.txt
├── .env.example              # API keys (FIRECRAWL_API_KEY)
└── README.md
```

**Deliverables:**
- `models.py` — `Job` dataclass matching the CSV schema.
- `base.py` — `BaseScraper` ABC with `scrape(title: str) -> list[Job]`.
- `csv_writer.py` — accepts `list[Job]`, writes to `output/jobs_<timestamp>.csv`.
- `requirements.txt` — initial dependencies (`requests`, `beautifulsoup4`, `firecrawl-py`, `python-dotenv`).

---

### Phase 2 — Naukri Scraper (HTML Scraping)

Implement the Naukri scraper using `requests` + `BeautifulSoup`.

**Steps:**
1. Build the search URL from the job title (e.g. `naukri.com/<title>-jobs`).
2. Send HTTP GET with appropriate headers (User-Agent, etc.).
3. Parse the HTML response — extract job cards (title, company, location, link, date).
4. Map extracted data to `Job` model and return.
5. Handle pagination if needed (first 2–3 pages).
6. Add error handling and rate-limiting (1–2 s delay between pages).

**Deliverables:**
- `scrapers/naukri.py` — working `NaukriScraper(BaseScraper)`.
- Unit test / manual verification with a sample title.

---

### Phase 3 — RemoteOK Scraper (Public API)

Implement the RemoteOK scraper using their public JSON API.

**Steps:**
1. Hit `https://remoteok.com/api` with a `User-Agent` header.
2. Filter the returned JSON array by matching the job title (case-insensitive).
3. Map fields (`position`, `company`, `location`, `url`, `date`) to `Job` model.
4. No pagination needed — the API returns all recent listings in one call.

**Deliverables:**
- `scrapers/remoteok.py` — working `RemoteOKScraper(BaseScraper)`.
- Unit test / manual verification.

---

### Phase 4 — Wellfound Scraper (Firecrawl)

Implement the Wellfound scraper using the Firecrawl SDK for JS-rendered pages.

**Steps:**
1. Load `FIRECRAWL_API_KEY` from `.env`.
2. Construct the Wellfound search URL for the given title.
3. Use Firecrawl's `scrape_url` to get rendered page content.
4. Parse the returned markdown / structured data — extract job cards.
5. Map to `Job` model and return.

**Deliverables:**
- `scrapers/wellfound.py` — working `WellfoundScraper(BaseScraper)`.
- `.env.example` updated with `FIRECRAWL_API_KEY=`.
- Unit test / manual verification.

---

### Phase 5 — CLI Integration & End-to-End Run

Wire everything together in `main.py`. The user provides **role** and
optional **location** as explicit CLI arguments; the agent triggers all
three boards with those values.

**Input:**

```bash
python -m src.main --role "Product Manager" --location "Bangalore"
python -m src.main --role "Software Engineer"  # location optional
python -m src.main --role "Data Analyst" --location "Mumbai" --sources naukri,remoteok
```

**Steps:**
1. Accept `--role` (required) and `--location` (optional) via CLI arguments.
2. Instantiate all three scrapers (Naukri, RemoteOK, Wellfound).
3. Run each scraper with `scraper.scrape(role, location)` — every board receives the same role and location.
4. Collect results into a single `list[Job]`.
5. Pass to `csv_writer` → write `output/jobs_<timestamp>.csv`.
6. Print summary to stdout (role, location, per-source counts, total jobs, output file path).
7. Support `--sources` flag to optionally run a subset (e.g. `--sources naukri,remoteok`).

**Platform behaviour with location:**

| Platform | How location is used |
| --- | --- |
| **Naukri** | Appended to URL: `naukri.com/<role>-jobs-in-<location>` |
| **RemoteOK** | Client-side filter on `location` field (all jobs are remote; "remote" matches everything) |
| **Wellfound** | Appended to URL: `wellfound.com/role/l/<role>/<location>` |

**Deliverables:**
- Fully functional CLI accepting `--role` and `--location` arguments.
- End-to-end test: all three boards produce results in a single CSV.
- Updated `README.md` with usage instructions and example commands.

---

## Out of Scope (for now)

- Automatic application / form-filling.
- Deduplication across runs.
- UI / dashboard — CLI-only for the first iteration.
