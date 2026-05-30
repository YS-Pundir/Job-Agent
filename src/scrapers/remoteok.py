"""RemoteOK scraper — uses the public JSON API at remoteok.com/api.

No pagination needed; the API returns all recent listings in one call.
We filter results client-side by matching the role keyword against the
``position`` and ``tags`` fields.
"""

import logging
from typing import Optional

import requests

from src.models import Job
from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

API_URL = "https://remoteok.com/api"
USER_AGENT = "JobAgent/1.0 (https://github.com/job-agent)"


class RemoteOKScraper(BaseScraper):
    """Scrape remote job listings from RemoteOK's public API."""

    @property
    def source_name(self) -> str:
        return "remoteok"

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    @staticmethod
    def _matches(item: dict, role: str, location: Optional[str] = None) -> bool:
        """Return True if the job item matches the search criteria."""
        role_lower = role.lower()

        # Match against position title and tags
        position = item.get("position", "").lower()
        tags = [t.lower() for t in item.get("tags", [])]

        role_words = role_lower.split()
        searchable = position + " " + " ".join(tags)

        role_match = (
            role_lower in position
            or any(role_lower in tag for tag in tags)
            # Broad match: all individual words appear in position+tags
            or all(word in searchable for word in role_words)
        )

        if not role_match:
            return False

        # RemoteOK is a remote-jobs board — all listings are remote by
        # nature, so we intentionally skip location filtering here.
        # The role match alone is sufficient.

        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, role: str, location: Optional[str] = None) -> list[Job]:
        """Fetch jobs from RemoteOK API and filter by role / location."""
        try:
            resp = requests.get(
                API_URL,
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("RemoteOK API request failed: %s", exc)
            return []

        data = resp.json()

        # First element is metadata (legal notice), skip it
        listings = data[1:] if len(data) > 1 else []
        logger.info("RemoteOK returned %d total listings.", len(listings))

        jobs: list[Job] = []
        for item in listings:
            if not self._matches(item, role, location):
                continue

            position = item.get("position", "").strip()
            if not position:
                continue

            company = item.get("company", "N/A").strip()
            job_location = item.get("location", "").strip() or "Remote"
            url = item.get("url", "")
            date_posted = item.get("date", "")

            # Trim the ISO timestamp to just the date part
            if date_posted and "T" in date_posted:
                date_posted = date_posted.split("T")[0]

            jobs.append(
                Job(
                    title=position,
                    company=company,
                    location=job_location,
                    url=url,
                    source="remoteok",
                    date_posted=date_posted,
                )
            )

        return jobs
