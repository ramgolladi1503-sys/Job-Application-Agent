from __future__ import annotations

from app.models import CandidateProfile, FitScore, JobDescription, Project
from app.models.schemas import ScoreBreakdown


def score_job(job: JobDescription, profile: CandidateProfile, projects: list[Project]) -> FitScore:
    profile_skills = profile.all_skills()
    must_matches = _count_matches(job.must_have_skills, profile_skills, projects)
    nice_matches = _count_matches(job.nice_to_have_skills, profile_skills, projects)
    must_total = max(len(job.must_have_skills), 1)
    nice_total = max(len(job.nice_to_have_skills), 1)

    must_points = round((must_matches / must_total) * 30)
    project_points = _project_evidence_points(job, projects)
    domain_points = _domain_points(job, projects)
    seniority_points = 8 if job.seniority in {"Mid-Level", "Unknown"} else 6
    tooling_points = round((nice_matches / nice_total) * 10) if job.nice_to_have_skills else 6
    positioning_points = _positioning_points(job, projects)
    risk_points = max(0, 5 - len(job.red_flags) * 2)
    final = min(100, must_points + project_points + domain_points + seniority_points + tooling_points + positioning_points + risk_points)

    missing = [skill for skill in job.must_have_skills if not _has_match(skill, profile_skills, projects)]
    risks = list(job.red_flags)
    if any("kubernetes" in skill.lower() for skill in job.must_have_skills + job.nice_to_have_skills):
        risks.append("Do not overclaim deep Kubernetes production ownership unless profile evidence is added.")

    positioning = _best_positioning(job)
    explanation = (
        f"Score {final}/100 because the role matches {must_matches}/{must_total} must-have skills, "
        f"has {project_points}/25 project evidence strength, and fits the recommended positioning: {positioning}."
    )

    return FitScore(
        final_score=final,
        decision=_decision(final),
        confidence="High" if final >= 80 else "Medium" if final >= 60 else "Low",
        best_positioning=positioning,
        explanation=explanation,
        risks=risks,
        missing_skills=missing,
        breakdown=ScoreBreakdown(
            must_have_skill_match=must_points,
            project_evidence_match=project_points,
            domain_relevance=domain_points,
            seniority_match=seniority_points,
            tooling_platform_match=tooling_points,
            resume_positioning_strength=positioning_points,
            risk_check=risk_points,
        ),
    )


def _count_matches(requirements: list[str], profile_skills: set[str], projects: list[Project]) -> int:
    return sum(1 for skill in requirements if _has_match(skill, profile_skills, projects))


def _has_match(skill: str, profile_skills: set[str], projects: list[Project]) -> bool:
    normalized = skill.lower()
    return normalized in profile_skills or any(normalized in project.searchable_text() for project in projects)


def _project_evidence_points(job: JobDescription, projects: list[Project]) -> int:
    text = " ".join(job.must_have_skills + job.nice_to_have_skills + [job.domain]).lower()
    hits = 0
    for project in projects:
        project_text = project.searchable_text()
        if any(token.lower() in project_text for token in job.must_have_skills):
            hits += 2
        if job.domain.lower() != "general" and job.domain.lower() in project_text:
            hits += 2
        if "genai" in text and "mcp shield" in project.name.lower():
            hits += 4
        if any(token in text for token in ["financial", "fintech", "trading"]):
            if "tradebot" in project.name.lower():
                hits += 4
    return min(25, hits * 3)


def _domain_points(job: JobDescription, projects: list[Project]) -> int:
    if job.domain == "General":
        return 8
    domain = job.domain.lower()
    if any(domain in project.searchable_text() for project in projects):
        return 15
    if job.domain == "AI" and any("mcp" in project.searchable_text() for project in projects):
        return 15
    if job.domain == "FinTech" and any("trading" in project.searchable_text() for project in projects):
        return 15
    return 7


def _positioning_points(job: JobDescription, projects: list[Project]) -> int:
    positioning = _best_positioning(job).lower()
    if "genai" in positioning and any("mcp shield" in p.name.lower() for p in projects):
        return 5
    if "sdet" in positioning and any("tradebot" in p.name.lower() for p in projects):
        return 5
    return 3


def _best_positioning(job: JobDescription) -> str:
    text = " ".join(job.keywords + job.must_have_skills + [job.role_title]).lower()
    if any(token in text for token in ["genai", "llm", "prompt", "model validation", "hallucination", "mcp"]):
        return "AI Testing / GenAI QA Engineer with automation and AI risk validation focus"
    if any(token in text for token in [".net", "react", "selenium", "playwright", "api testing"]):
        return "QA Automation / SDET profile with full-stack engineering exposure"
    return "QA Automation profile with evidence-backed project positioning"


def _decision(score: int) -> str:
    if score >= 85:
        return "Strong Apply"
    if score >= 70:
        return "Apply if interested"
    if score >= 55:
        return "Maybe / careful positioning"
    return "Skip"
