from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.ats_scorer import score_resume_ats
from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import render_resume, write_application_pack
from app.core.interview_prep import generate_interview_prep
from app.core.jd_parser import parse_job_description, parse_job_file
from app.core.profile_loader import load_profile, load_projects, load_rules


def analyze_job_text(job_text: str, profile_path: str | Path, portfolio_path: str | Path) -> dict[str, Any]:
    job = parse_job_description(job_text)
    profile = load_profile(profile_path)
    projects = load_projects(portfolio_path)
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    resume = render_resume(job, profile, projects, fit, evidence)
    ats = score_resume_ats(resume, job, evidence)
    interview = generate_interview_prep(job, fit, evidence)
    return {
        "job": job.model_dump(),
        "fit_score": fit.model_dump(),
        "evidence": [item.model_dump() for item in evidence],
        "ats_score": ats,
        "interview_prep": interview,
    }


def generate_pack_from_file(
    job_file: str | Path,
    profile_path: str | Path,
    portfolio_path: str | Path,
    rules_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    job = parse_job_file(job_file)
    profile = load_profile(profile_path)
    projects = load_projects(portfolio_path)
    rules = load_rules(rules_path)
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    files = write_application_pack(output_dir, job, profile, projects, rules, fit, evidence)
    return {
        "output_dir": str(output_dir),
        "files": files,
        "fit_score": fit.model_dump(),
        "evidence_count": len(evidence),
    }
