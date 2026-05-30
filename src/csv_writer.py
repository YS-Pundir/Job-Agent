import csv
import os
from datetime import datetime

from src.models import Job

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def write_jobs_to_csv(jobs: list[Job]) -> str:
    """Write a list of Job objects to a timestamped CSV file.

    Returns the absolute path to the generated CSV file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"jobs_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=Job.field_names())
        writer.writeheader()
        for job in jobs:
            writer.writerow(job.to_dict())

    return filepath
