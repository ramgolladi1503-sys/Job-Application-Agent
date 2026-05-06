from __future__ import annotations

from app.models import CandidateProfile, JobDescription, Project


def analyze_missing_skills(job: JobDescription, profile: CandidateProfile, projects: list[Project]) -> dict[str, list[str]]:
    profile_skills = profile.all_skills()
    project_text = " ".join(project.searchable_text() for project in projects)

    strong_matches: list[str] = []
    weak_matches: list[str] = []
    missing: list[str] = []

    for skill in job.must_have_skills + job.nice_to_have_skills:
        key = skill.lower()
        if key in profile_skills:
            strong_matches.append(skill)
        elif key in project_text:
            weak_matches.append(skill)
        else:
            missing.append(skill)

    return {
        "strong_matches": _unique(strong_matches),
        "project_evidence_matches": _unique(weak_matches),
        "missing_or_weak": _unique(missing),
    }


def render_missing_skills_report(analysis: dict[str, list[str]]) -> str:
    lines = ["# Missing Skills Report", ""]
    sections = [
        ("Strong profile matches", analysis.get("strong_matches", [])),
        ("Project evidence matches", analysis.get("project_evidence_matches", [])),
        ("Missing or weak", analysis.get("missing_or_weak", [])),
    ]
    for title, items in sections:
        lines += [f"## {title}", ""]
        lines += [f"- {item}" for item in items] if items else ["- None detected."]
        lines.append("")
    lines += ["## Usage", "", "Missing skills should not be added as strong resume claims. Use them for learning plans, interview preparation, or honest risk notes."]
    return "\n".join(lines)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
