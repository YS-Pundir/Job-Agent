from dataclasses import dataclass, fields, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """Represents a single job listing normalised across all platforms."""

    title: str
    company: str
    location: str
    url: str
    source: str  # naukri | remoteok | wellfound
    date_posted: Optional[str] = None
    scraped_at: str = ""

    def __post_init__(self) -> None:
        if not self.scraped_at:
            self.scraped_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def field_names(cls) -> list[str]:
        """Return column names in declaration order (used as CSV header)."""
        return [f.name for f in fields(cls)]

    def to_dict(self) -> dict:
        """Convert to an ordered dict suitable for csv.DictWriter."""
        return asdict(self)
