from __future__ import annotations

import csv
import shutil
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
    rows = read_tracker(path)
    row = {
        "date_created": date.today().isoformat(),
        "company": job.company,
        "role_title": job.role_title,
        "fit_score": str(fit.final_score),
        "decision": fit.decision,
        "status": status,
        "pack_path": str(pack_path),
        "follow_up_date": follow_up_date,
        "notes": notes,
    }
    rows.append(row)
    write_tracker(path, rows)


def read_tracker(tracker_path: str | Path) -> list[dict[str, str]]:
    path = Path(tracker_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_tracker(tracker_path: str | Path, rows: list[dict[str, str]]) -> None:
    path = Path(tracker_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in TRACKER_COLUMNS})


def update_application_status(
    tracker_path: str | Path,
    company: str,
    role_title: str,
    status: str,
    follow_up_date: str = "",
    notes: str = "",
) -> int:
    rows = read_tracker(tracker_path)
    updated = 0
    for row in rows:
        if company.lower() in row.get("company", "").lower() and role_title.lower() in row.get("role_title", "").lower():
            row["status"] = status
            if follow_up_date:
                row["follow_up_date"] = follow_up_date
            if notes:
                row["notes"] = notes
            updated += 1
    if updated:
        write_tracker(tracker_path, rows)
    return updated


def export_tracker(tracker_path: str | Path, output_path: str | Path) -> None:
    source = Path(tracker_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        write_tracker(source, [])
    shutil.copyfile(source, target)


def render_tracker_summary(tracker_path: str | Path) -> str:
    rows = read_tracker(tracker_path)
    if not rows:
        return "# Application Tracker\n\nNo application records found.\n"
    lines = ["# Application Tracker", "", f"Total records: {len(rows)}", "", "| Date | Company | Role | Score | Decision | Status | Follow-up |", "|---|---|---|---:|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {row['date_created']} | {row['company']} | {row['role_title']} | {row['fit_score']} | {row['decision']} | {row['status']} | {row.get('follow_up_date', '')} |"
        )
    return "\n".join(lines) + "\n"
