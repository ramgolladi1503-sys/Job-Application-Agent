from __future__ import annotations

from app.models import CandidateProfile, EvidenceMatch, JobDescription, Project


def map_evidence(job: JobDescription, profile: CandidateProfile, projects: list[Project]) -> list[EvidenceMatch]:
    skills = profile.all_skills()
    output: list[EvidenceMatch] = []
    for req in _unique(job.must_have_skills + job.nice_to_have_skills):
        project = _select_project(req, projects)
        if project is not None:
            output.append(EvidenceMatch(requirement=req, candidate_evidence=f"{project.name}: " + "; ".join(project.evidence[:3]), resume_bullet=(project.safe_resume_bullets[0] if project.safe_resume_bullets else f"Used {req} in {project.name}."), evidence_strength="Strong", source_project=project.name))
        elif req.lower() in skills:
            output.append(EvidenceMatch(requirement=req, candidate_evidence=f"{req} appears in the skill inventory.", resume_bullet=f"Applied {req} in QA and validation workflows.", evidence_strength="Medium"))
        else:
            output.append(EvidenceMatch(requirement=req, candidate_evidence="No matching project entry found.", resume_bullet="", evidence_strength="Missing"))
    return output


def _select_project(req: str, projects: list[Project]) -> Project | None:
    key = req.lower()
    ranked: list[tuple[int, Project]] = []
    for p in projects:
        text = p.searchable_text()
        score = 5 if key in text else 0
        if any(x in key for x in ["llm", "genai", "hallucination", "mcp", "model"]) and "mcp shield" in p.name.lower():
            score += 8
        if any(x in key for x in ["react", "api", "docker", "selenium"]) and "tradebot" in p.name.lower():
            score += 4
        if score:
            ranked.append((score, p))
    return sorted(ranked, key=lambda x: x[0], reverse=True)[0][1] if ranked else None


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
