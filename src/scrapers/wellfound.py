"""Wellfound scraper — uses Firecrawl to render the JS-heavy page and
return structured markdown, which we then parse for job listings.

Requires ``FIRECRAWL_API_KEY`` in the environment (or ``.env`` file).
"""

import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv

from src.models import Job
from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://wellfound.com"


class WellfoundScraper(BaseScraper):
    """Scrape job listings from Wellfound via Firecrawl."""

    @property
    def source_name(self) -> str:
        return "wellfound"

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_search_url(role: str, location: Optional[str] = None) -> str:
        """Build Wellfound search URL.

        Examples:
            ("software engineer", "bangalore")
                → wellfound.com/role/l/software-engineer/bangalore
            ("product manager", None)
                → wellfound.com/role/r/product-manager
        """
        slug = role.strip().lower().replace(" ", "-")
        if location:
            loc_slug = location.strip().lower().replace(" ", "-")
            url = f"{BASE_URL}/role/l/{slug}/{loc_slug}"
        else:
            url = f"{BASE_URL}/role/r/{slug}"
        return url

    # ------------------------------------------------------------------
    # Markdown parsing
    # ------------------------------------------------------------------

    # Patterns for classifying links
    _NAV_URL_RE = re.compile(r"/role/[lr]/", re.IGNORECASE)
    _COMPANY_URL_RE = re.compile(r"/company/", re.IGNORECASE)
    _JOB_URL_RE = re.compile(r"/jobs/", re.IGNORECASE)

    @staticmethod
    def _parse_jobs_from_markdown(
        md: str, search_location: Optional[str] = None
    ) -> list[Job]:
        """Extract job listings from Firecrawl markdown.

        Wellfound pages are structured as company blocks followed by their
        job listings.  We track the current company and only emit actual
        ``/jobs/`` entries.  The searched location is applied to every job
        since Wellfound already filters server-side.
        """
        jobs: list[Job] = []
        current_company: str = "N/A"

        link_re = re.compile(
            r"\[([^\]]+)\]\((https?://[^\)]*wellfound\.com/[^\)]*)\)",
            re.IGNORECASE,
        )

        # Walk every line so we can maintain company context across blocks
        for line in md.splitlines():
            for text, href in link_re.findall(line):
                text_clean = text.strip().strip("*")  # strip bold markers

                # Skip navigation / search links
                if WellfoundScraper._NAV_URL_RE.search(href):
                    continue

                # Company link → remember as current company
                if WellfoundScraper._COMPANY_URL_RE.search(href):
                    current_company = text_clean
                    continue

                # Job link → emit as a job entry
                if WellfoundScraper._JOB_URL_RE.search(href):
                    # Use the searched location; fall back to "N/A"
                    location = search_location.title() if search_location else "N/A"

                    jobs.append(
                        Job(
                            title=text_clean,
                            company=current_company,
                            location=location,
                            url=href,
                            source="wellfound",
                        )
                    )

        return jobs

    # ------------------------------------------------------------------
    # HTML fallback parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_jobs_from_html(html: str) -> list[Job]:
        """Fallback: parse raw HTML if markdown parsing yields nothing."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        jobs: list[Job] = []

        # Wellfound job cards are typically in a list with startup-link class
        cards = soup.select(
            "div[class*='jobCard'], div[class*='job-listing'], "
            "div[class*='styles_result'], a[class*='job']"
        )

        for card in cards:
            try:
                title_el = card.select_one(
                    "h2, h3, a[class*='title'], span[class*='title']"
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                link = ""
                a_tag = card.find("a", href=True)
                if a_tag:
                    link = a_tag["href"]
                    if link.startswith("/"):
                        link = f"{BASE_URL}{link}"

                comp_el = card.select_one(
                    "a[class*='company'], span[class*='company'], "
                    "h4, span[class*='startup']"
                )
                company = comp_el.get_text(strip=True) if comp_el else "N/A"

                loc_el = card.select_one(
                    "span[class*='location'], span[class*='loc']"
                )
                location = loc_el.get_text(strip=True) if loc_el else "N/A"

                jobs.append(
                    Job(
                        title=title,
                        company=company,
                        location=location,
                        url=link,
                        source="wellfound",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Failed to parse Wellfound card: %s", exc)

        return jobs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, role: str, location: Optional[str] = None) -> list[Job]:
        """Scrape Wellfound via Firecrawl."""
        load_dotenv()

        api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
        if not api_key:
            logger.error(
                "FIRECRAWL_API_KEY not set. "
                "Add it to your .env file or export it as an environment variable."
            )
            return []

        try:
            from firecrawl import V1FirecrawlApp
        except ImportError:
            logger.error(
                "firecrawl-py is required for the Wellfound scraper. "
                "Install with: pip install firecrawl-py"
            )
            return []

        url = self._build_search_url(role, location)
        logger.info("Wellfound URL → %s", url)

        try:
            app = V1FirecrawlApp(api_key=api_key)
            result = app.scrape_url(
                url,
                formats=["markdown", "html"],
                timeout=30_000,
            )
        except Exception as exc:
            logger.error("Firecrawl scrape failed: %s", exc)
            return []

        # Try markdown first (cleaner), fall back to HTML
        markdown = getattr(result, "markdown", "") or ""
        html = getattr(result, "html", "") or ""

        logger.info(
            "Firecrawl returned %d chars markdown, %d chars HTML.",
            len(markdown), len(html),
        )

        jobs = self._parse_jobs_from_markdown(markdown, search_location=location)
        if not jobs and html:
            logger.info("Markdown parsing found 0 jobs, trying HTML fallback.")
            jobs = self._parse_jobs_from_html(html)

        return jobs
