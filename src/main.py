"""CLI entry-point for the Job Agent."""

import argparse
import sys

from src.csv_writer import write_jobs_to_csv
from src.models import Job
from src.scrapers.naukri import NaukriScraper
from src.scrapers.remoteok import RemoteOKScraper
from src.scrapers.wellfound import WellfoundScraper

# Registry of available scrapers
SCRAPER_REGISTRY: dict[str, type] = {
    "naukri": NaukriScraper,
    "remoteok": RemoteOKScraper,
    "wellfound": WellfoundScraper,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Job Agent — scrape jobs from Naukri, RemoteOK & Wellfound"
    )
    parser.add_argument(
        "--role",
        required=True,
        help="Job role to search for (e.g. 'Product Manager', 'Software Engineer')",
    )
    parser.add_argument(
        "--location",
        default=None,
        help="Job location (e.g. 'Bangalore', 'Mumbai', 'Remote'). Optional.",
    )
    parser.add_argument(
        "--sources",
        default=None,
        help="Comma-separated list of sources to scrape (default: all). "
             "Options: naukri, remoteok, wellfound",
    )
    parser.add_argument(
        "--naukri-html",
        default=None,
        help="Path to a saved Naukri HTML file (offline fallback).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: visible Chrome window).",
    )
    args = parser.parse_args()

    role = args.role.strip()
    location = args.location.strip() if args.location else None

    print(f"[*] Role: '{role}'"
          + (f", Location: '{location}'" if location else ""))

    # Determine which scrapers to run
    if args.sources:
        requested = [s.strip().lower() for s in args.sources.split(",")]
    else:
        requested = list(SCRAPER_REGISTRY.keys())

    if not requested:
        print("No scrapers registered yet. Implement Phase 2–4 first.")
        sys.exit(1)

    all_jobs: list[Job] = []

    for name in requested:
        scraper_cls = SCRAPER_REGISTRY.get(name)
        if scraper_cls is None:
            print(f"[WARN] Unknown source '{name}', skipping.")
            continue

        print(f"[*] Scraping {name} for '{role}'"
              + (f" in '{location}'" if location else "")
              + " ...")
        # Pass extra options to scrapers that support them
        if name == "naukri":
            scraper = scraper_cls(
                html_file=args.naukri_html,
                headless=args.headless,
            )
        else:
            scraper = scraper_cls()
        jobs = scraper.scrape(role, location)
        print(f"    Found {len(jobs)} job(s) from {name}.")
        all_jobs.extend(jobs)

    if not all_jobs:
        print("No jobs found across the requested sources.")
        sys.exit(0)

    filepath = write_jobs_to_csv(all_jobs)

    # Summary
    print(f"\n{'=' * 40}")
    print(f"Role: {role}" + (f" | Location: {location}" if location else ""))
    source_counts = {}
    for j in all_jobs:
        source_counts[j.source] = source_counts.get(j.source, 0) + 1
    for src, count in source_counts.items():
        print(f"  {src}: {count} job(s)")
    print(f"  Total: {len(all_jobs)} job(s)")
    print(f"Saved to: {filepath}")
    print(f"{'=' * 40}")


if __name__ == "__main__":
    main()
