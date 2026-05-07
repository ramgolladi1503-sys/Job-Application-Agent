from __future__ import annotations

from dataclasses import dataclass

from app.models import CandidateProfile, FitScore, JobDescription, Project
from app.models.schemas import ScoreBreakdown

SKILL_ALIASES = {
    ".net core": ["dotnet", ".net", "asp.net", "c#"],
    "react": ["react js", "reactjs", "frontend"],
    "ci/cd": ["github actions", "azure devops", "pipeline", "quality gates"],
    "api testing": ["api validation", "rest", "backend validation"],
    "automation testing": ["test automation", "automated testing", "selenium", "playwright"],
    "llm evaluation": ["llm validation", "model response validation", "model validation"],
    "hallucination testing": ["hallucination risk", "unsafe responses", "model behavior"],
    "prompt testing": ["prompt validation", "prompt behavior"],
    "mcp": ["tool-use", "agent tool", "mcp security"],
}

CRITICAL_RESEARCH_TERMS = {"phd", "research publications", "distributed training", "advanced machine learning model training"}


@dataclass(frozen=True)
class MatchResult:
    skill: str
    strength: float
    source: str


def score_job(job: JobDescription, profile: CandidateProfile, projects: list[Project]) -> FitScore:
    profile_skills = profile.all_skills()
    project_text = " ".join(project.searchable_text() for project in projects)

    must_results = [_match_skill(skill, profile_skills, project_text) for skill in job.must_have_skills]
    nice_results = [_match_skill(skill, profile_skills, project_text) for skill in job.nice_to_have_skills]

    must_points = _weighted_points(must_results, 30, default_if_empty=12)
    tooling_points = _weighted_points(nice_results, 10, default_if_empty=6)
    project_points = _project_evidence_points(job, projects, must_results + nice_results)
    domain_points = _domain_points(job, projects)
    seniority_points = _seniority_points(job, must_results)
    positioning_points = _positioning_points(job, projects)
    risk_points = _risk_points(job, must_results)

    raw_score = must_points + project_points + domain_points + seniority_points + tooling_points + positioning_points + risk_points
    final = max(0, min(100, raw_score))

    missing = [result.skill for result in must_results if result.strength == 0]
    weak = [result.skill for result in must_results if 0 < result.strength < 0.7]
    risks = _risks(job, missing, weak)
    positioning = _best_positioning(job)
    explanation = _explain_score(final, must_results, project_points, domain_points, positioning, missing, weak)

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


def _match_skill(skill: str, profile_skills: set[str], project_text: str) -> MatchResult:
    normalized = skill.lower()
    aliases = SKILL_ALIASES.get(normalized, [])
    candidates = [normalized, *aliases]
    if any(candidate in profile_skills for candidate in candidates):
        return MatchResult(skill, 1.0, "profile")
    if any(candidate in project_text for candidate in candidates):
        return MatchResult(skill, 0.75, "project evidence")
    if any(_soft_token_overlap(candidate, project_text) for candidate in candidates):
        return MatchResult(skill, 0.5, "weak related evidence")
    return MatchResult(skill, 0.0, "missing")


def _soft_token_overlap(skill: str, text: str) -> bool:
    tokens = [token for token in skill.replace("/", " ").replace("-", " ").split() if len(token) > 3]
    return bool(tokens) and sum(1 for token in tokens if token in text) >= max(1, len(tokens) - 1)


def _weighted_points(results: list[MatchResult], maximum: int, default_if_empty: int) -> int:
    if not results:
        return default_if_empty
    score = sum(result.strength for result in results) / len(results)
    return round(score * maximum)


def _project_evidence_points(job: JobDescription, projects: list[Project], results: list[MatchResult]) -> int:
    direct_project_matches = sum(1 for result in results if result.source == "project evidence")
    strong_project_count = sum(1 for project in projects if _project_matches_role(job, project))
    points = direct_project_matches * 4 + strong_project_count * 5
    if job.domain == "AI" and any("mcp shield" in project.name.lower() for project in projects):
        points += 7
    if job.domain == "FinTech" and any("tradebot" in project.name.lower() for project in projects):
        points += 7
    return min(25, points)


def _project_matches_role(job: JobDescription, project: Project) -> bool:
    text = " ".join([job.role_title, job.domain, *job.keywords, *job.must_have_skills]).lower()
    project_text = project.searchable_text()
    if "genai" in text or "llm" in text or "mcp" in text:
        return "mcp" in project_text or "ai testing" in project_text
    if ".net" in text or "react" in text or "selenium" in text or "api testing" in text:
        return "automation" in project_text or "tradebot" in project_text
    return any(keyword.lower() in project_text for keyword in job.keywords)


def _domain_points(job: JobDescription, projects: list[Project]) -> int:
    if job.domain == "General":
        return 8
    domain = job.domain.lower()
    project_text = " ".join(project.searchable_text() for project in projects)
    if domain in project_text:
        return 15
    if job.domain == "AI" and any(term in project_text for term in ["mcp", "llm", "genai", "ai testing"]):
        return 15
    if job.domain == "FinTech" and any(term in project_text for term in ["trading", "financial", "fintech"]):
        return 15
    return 6


def _seniority_points(job: JobDescription, must_results: list[MatchResult]) -> int:
    text = " ".join([job.role_title, job.seniority, *job.must_have_skills]).lower()
    missing_critical = any(result.skill.lower() in CRITICAL_RESEARCH_TERMS and result.strength == 0 for result in must_results)
    if missing_critical:
        return 3
    if "senior" in text or "lead" in text:
        return 7
    if "junior" in text or "entry" in text:
        return 9
    return 8


def _positioning_points(job: JobDescription, projects: list[Project]) -> int:
    positioning = _best_positioning(job).lower()
    if "genai" in positioning and any("mcp shield" in project.name.lower() for project in projects):
        return 5
    if "sdet" in positioning and any("tradebot" in project.name.lower() or "automation" in project.name.lower() for project in projects):
        return 5
    return 3


def _risk_points(job: JobDescription, must_results: list[MatchResult]) -> int:
    points = 5
    points -= len(job.red_flags) * 2
    missing_ratio = _missing_ratio(must_results)
    if missing_ratio >= 0.5:
        points -= 3
    if any(result.skill.lower() in CRITICAL_RESEARCH_TERMS and result.strength == 0 for result in must_results):
        points -= 3
    return max(0, points)


def _missing_ratio(results: list[MatchResult]) -> float:
    if not results:
        return 0.0
    return sum(1 for result in results if result.strength == 0) / len(results)


def _risks(job: JobDescription, missing: list[str], weak: list[str]) -> list[str]:
    risks = list(job.red_flags)
    if missing:
        risks.append("Missing must-have skills should not be presented as strengths: " + ", ".join(missing))
    if weak:
        risks.append("Weak matches should be positioned carefully: " + ", ".join(weak))
    if any("kubernetes" in skill.lower() for skill in job.must_have_skills + job.nice_to_have_skills):
        risks.append("Do not overclaim deep Kubernetes production ownership unless profile evidence is added.")
    return risks


def _best_positioning(job: JobDescription) -> str:
    text = " ".join(job.keywords + job.must_have_skills + [job.role_title]).lower()
    if any(token in text for token in ["genai", "llm", "prompt", "model validation", "hallucination", "mcp"]):
        return "AI Testing / GenAI QA Engineer with automation and AI risk validation focus"
    if any(token in text for token in [".net", "react", "selenium", "playwright", "api testing", "cypress"]):
        return "QA Automation / SDET profile with full-stack engineering exposure"
    return "QA Automation profile with evidence-backed project positioning"


def _explain_score(score: int, must_results: list[MatchResult], project_points: int, domain_points: int, positioning: str, missing: list[str], weak: list[str]) -> str:
    matched = [result.skill for result in must_results if result.strength >= 0.7]
    parts = [
        f"Score {score}/100 based on weighted must-have evidence, project fit, domain relevance, seniority alignment, and risk checks.",
        f"Strong must-have matches: {', '.join(matched) if matched else 'none'}.",
        f"Project evidence contributed {project_points}/25 and domain relevance contributed {domain_points}/15.",
        f"Recommended positioning: {positioning}.",
    ]
    if missing:
        parts.append("Missing must-haves: " + ", ".join(missing) + ".")
    if weak:
        parts.append("Weak/partial matches: " + ", ".join(weak) + ".")
    return " ".join(parts)


def _decision(score: int) -> str:
    if score >= 85:
        return "Strong Apply"
    if score >= 70:
        return "Apply if interested"
    if score >= 55:
        return "Maybe / careful positioning"
    return "Skip"
