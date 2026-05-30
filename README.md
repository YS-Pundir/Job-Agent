# Job Agent

CLI tool that scrapes job listings from **Naukri**, **RemoteOK**, and **Wellfound** for a given job role and location, then saves them to a CSV file.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your FIRECRAWL_API_KEY
```

Naukri scraping uses your system Chrome via `undetected-chromedriver` (installed automatically).

## Usage

```bash
# Search all three boards
python -m src.main --role "Product Manager" --location "Bangalore"

# Search without location
python -m src.main --role "Software Engineer"

# Search specific sources only
python -m src.main --role "Data Analyst" --location "Mumbai" --sources naukri,remoteok

# Run Naukri browser in headless mode
python -m src.main --role "Python Developer" --location "Bangalore" --headless

# Use a saved Naukri HTML file (offline fallback)
python -m src.main --role "Backend Engineer" --naukri-html ~/saved_naukri.html
```

Results are saved to `output/jobs_<timestamp>.csv`.

## CLI Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--role` | Yes | Job role (e.g. "Product Manager", "Software Engineer") |
| `--location` | No | Location (e.g. "Bangalore", "Mumbai", "Remote") |
| `--sources` | No | Comma-separated sources: `naukri`, `remoteok`, `wellfound` (default: all) |
| `--headless` | No | Run Naukri browser in headless mode |
| `--naukri-html` | No | Path to a saved Naukri HTML file |

## Project Structure

```
src/
├── main.py          # CLI entry-point
├── models.py        # Job dataclass
├── csv_writer.py    # CSV output logic
└── scrapers/
    ├── base.py      # Abstract BaseScraper interface
    ├── naukri.py     # undetected-chromedriver + BeautifulSoup
    ├── remoteok.py   # Public JSON API
    └── wellfound.py  # Firecrawl (JS-rendered page extraction)
```
