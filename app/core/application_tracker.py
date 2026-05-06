from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from app.models import FitScore, JobDescription

TRACKER_COLUMNS = [
    "date_created",
    "company",
    "role_title",
    "fit_score",
    "decision",
    "status",
    "pack_path",
    "follow_up_date",
    "notes",
]


def append_application_record(
    tracker_path: str | Path,
    job: JobDescription,
    fit: FitScore,
    pack_path: str | Path,
    status: str = "prepared",
    follow_up_date: str = "",
    notes: str = "Manual submission required.",
) -> None:
    path = Path(tracker_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "date_created": date.today().isoformat(),
                "company": job.company,
                "role_title": job.role_title,
                "fit_score": fit.final_score,
                "decision": fit.decision,
                "status": status,
                "pack_path": str(pack_path),
                "follow_up_date": follow_up_date,
                "notes": notes,
            }
        )


def render_tracker_summary(tracker_path: str | Path) -> str:
    path = Path(tracker_path)
    if not path.exists():
        return "# Application Tracker\n\nNo application records found.\n"
    rows = list(csv.DictReader(path.open("r", encoding="utf-8")))
    lines = ["# Application Tracker", "", f"Total records: {len(rows)}", "", "| Date | Company | Role | Score | Decision | Status |", "|---|---|---|---:|---|---|"]
    for row in rows:
        lines.append(
            f"| {row['date_created']} | {row['company']} | {row['role_title']} | {row['fit_score']} | {row['decision']} | {row['status']} |"
        )
    return "\n".join(lines) + "\n"
