from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import write_application_pack
from app.core.github_portfolio import write_remote_repo_summary
from app.core.jd_parser import parse_job_file
from app.core.job_discovery import discover_jobs_from_config, write_job_lead_files
from app.core.profile_loader import load_profile, load_projects, load_rules


@dataclass(frozen=True)
class PipelineResult:
    discovered_count: int
    generated_count: int
    skipped_count: int
    next_actions_path: str
    output_dir: str


def run_profile_pipeline(config_path: str | Path) -> PipelineResult:
    config = _read_yaml(config_path)
    profile_path = Path(config["profile"]["master_profile"])
    portfolio_path = Path(config["profile"]["project_portfolio"])
    rules_path = Path(config["profile"]["resume_rules"])

    _sync_github_portfolio(config)

    discovery_config = Path(config["job_discovery"]["sources_config"])
    discovery_output = Path(config["job_discovery"].get("output_dir", "outputs/job_discovery/profile_pipeline"))
    limit = int(config["job_discovery"].get("limit", 50))
    leads = discover_jobs_from_config(discovery_config, discovery_output, limit=limit)

    candidate = load_profile(profile_path)
    projects = load_projects(portfolio_path)
    rules = load_rules(rules_path)

    app_config = config.get("application_generation", {})
    app_output = Path(app_config.get("output_dir", "outputs/applications/profile_pipeline"))
    app_output.mkdir(parents=True, exist_ok=True)

    filter_config = config.get("filtering", {})
    min_score = int(filter_config.get("min_fit_score", 70))
    high_priority_score = int(filter_config.get("high_priority_score", 82))
    blocked_keywords = [str(item).lower() for item in filter_config.get("blocked_keywords", [])]

    job_files = write_job_lead_files(leads, discovery_output / "job_descriptions")
    rows: list[dict[str, Any]] = []
    generated_count = 0
    skipped_count = 0

    for job_file in job_files:
        job = parse_job_file(job_file)
        fit = score_job(job, candidate, projects)
        blocked_reason = _blocked_reason(job.raw_text, blocked_keywords)
        decision = "generate" if fit.final_score >= min_score and not blocked_reason else "skip"
        pack_dir = ""
        if decision == "generate":
            evidence = map_evidence(job, candidate, projects)
            pack_path = app_output / _safe_folder_name(f"{job.company}_{job.role_title}_{fit.final_score}")
            write_application_pack(pack_path, job, candidate, projects, rules, fit, evidence)
            pack_dir = str(pack_path)
            generated_count += 1
        else:
            skipped_count += 1
        rows.append(
            {
                "company": job.company,
                "role_title": job.role_title,
                "fit_score": fit.final_score,
                "priority": "high" if fit.final_score >= high_priority_score else "normal",
                "decision": decision,
                "blocked_reason": blocked_reason,
                "pack_dir": pack_dir,
            }
        )

    report_path = Path(config.get("next_actions", {}).get("report_path", app_output / "00_next_actions.md"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_next_actions(rows, min_score, high_priority_score), encoding="utf-8")
    _write_pipeline_csv(rows, app_output / "00_pipeline_results.csv")

    return PipelineResult(
        discovered_count=len(leads),
        generated_count=generated_count,
        skipped_count=skipped_count,
        next_actions_path=str(report_path),
        output_dir=str(app_output),
    )


def _sync_github_portfolio(config: dict[str, Any]) -> None:
    sync = config.get("portfolio_sync", {})
    if not sync.get("enabled", False):
        return
    output = sync.get("generated_output")
    repos = [repo for repo in sync.get("github_repositories", []) if repo.get("enabled", False)]
    if not output or not repos:
        return
    # Write the first enabled repo for now. Additional repos can be merged after manual review.
    repo = repos[0]
    write_remote_repo_summary(repo["owner"], repo["repo"], output, ref=repo.get("ref", "main"))


def _blocked_reason(text: str, blocked_keywords: list[str]) -> str:
    lower = text.lower()
    for keyword in blocked_keywords:
        if keyword and keyword in lower:
            return f"Blocked keyword: {keyword}"
    return ""


def _render_next_actions(rows: list[dict[str, Any]], min_score: int, high_priority_score: int) -> str:
    sorted_rows = sorted(rows, key=lambda row: int(row["fit_score"]), reverse=True)
    lines = [
        "# Profile Pipeline Next Actions",
        "",
        f"Minimum score for generated packs: {min_score}",
        f"High priority score: {high_priority_score}",
        "",
        "## High Priority Applications",
        "",
    ]
    high = [row for row in sorted_rows if row["decision"] == "generate" and row["priority"] == "high"]
    lines += _rows_to_markdown(high)
    lines += ["", "## Normal Generated Applications", ""]
    normal = [row for row in sorted_rows if row["decision"] == "generate" and row["priority"] != "high"]
    lines += _rows_to_markdown(normal)
    lines += ["", "## Skipped Roles", ""]
    skipped = [row for row in sorted_rows if row["decision"] == "skip"]
    lines += _rows_to_markdown(skipped)
    lines += [
        "",
        "## Manual Workflow",
        "",
        "1. Open the highest score pack first.",
        "2. Review `05_tailored_resume.md`, `08_cover_letter.md`, `09_recruiter_message.md`, `11_truthfulness_report.md`, and `14_ats_score_report.md`.",
        "3. Edit anything that sounds inflated or weak.",
        "4. Submit manually on the job site.",
        "5. Update the tracker status after submission.",
        "",
        "No auto-apply or auto-message action has been taken.",
    ]
    return "\n".join(lines) + "\n"


def _rows_to_markdown(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["- None"]
    lines = []
    for row in rows:
        detail = f"- {row['fit_score']}/100 — {row['company']} — {row['role_title']}"
        if row.get("pack_dir"):
            detail += f" — `{row['pack_dir']}`"
        if row.get("blocked_reason"):
            detail += f" — {row['blocked_reason']}"
        lines.append(detail)
    return lines


def _write_pipeline_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("company,role_title,fit_score,priority,decision,blocked_reason,pack_dir\n", encoding="utf-8")
        return
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Pipeline config must be a YAML mapping.")
    return data


def _safe_folder_name(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value)
    return "_".join(part for part in cleaned.split("_") if part)[:120]
