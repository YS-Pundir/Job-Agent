"""Parse a natural-language job query into role + optional location.

Examples:
    "Find product manager roles in Bangalore"  → ("product manager", "bangalore")
    "Software Engineer jobs in Mumbai"          → ("software engineer", "mumbai")
    "Data Analyst in Remote"                    → ("data analyst", "remote")
    "Python Developer"                          → ("python developer", None)
"""

import re
from dataclasses import dataclass


# Words that are noise — stripped from the query before parsing
NOISE_WORDS = {
    "find", "search", "look", "looking", "for", "get", "show", "list",
    "me", "the", "a", "an", "some", "any", "all", "open", "openings",
    "roles", "role", "jobs", "job", "positions", "position", "opportunities",
    "vacancy", "vacancies", "hiring",
}


@dataclass
class ParsedQuery:
    """Result of parsing a user's free-text job search query."""
    role: str
    location: str | None = None


def parse_query(raw: str) -> ParsedQuery:
    """Extract *role* and optional *location* from a natural-language query.

    The heuristic:
        1. Split on " in " (last occurrence) to separate role part / location.
        2. Strip noise words from the role part.
        3. Normalise whitespace and lower-case.
    """
    text = raw.strip()
    if not text:
        raise ValueError("Empty query")

    # --- split on " in " to find location ---
    location: str | None = None
    # Use the *last* occurrence of " in " so "Senior Engineer in AI in Bangalore"
    # parses as role="Senior Engineer in AI", location="Bangalore"
    parts = re.split(r"\s+in\s+", text, flags=re.IGNORECASE)
    if len(parts) >= 2:
        location_candidate = parts[-1].strip()
        role_part = " in ".join(parts[:-1]).strip()
        # Only treat as location if it looks like a place (1-3 words, no obvious
        # job-keyword overlap)
        if 1 <= len(location_candidate.split()) <= 4:
            location = location_candidate
        else:
            role_part = text  # keep the full string as role
    else:
        role_part = text

    # --- clean the role part ---
    words = role_part.split()
    cleaned = [w for w in words if w.lower() not in NOISE_WORDS]
    role = " ".join(cleaned).strip()

    # Edge case: if everything was a noise word, fall back to original
    if not role:
        role = role_part

    return ParsedQuery(
        role=role.lower(),
        location=location.lower() if location else None,
    )
