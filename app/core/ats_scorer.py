from __future__ import annotations

from collections import Counter
from typing import Any

from app.models import EvidenceMatch, JobDescription

ATS_SECTION_HINTS = ["professional summary", "core skills", "experience", "projects", "education"]
ACTION_VERBS = ["built", "designed", "validated", "created", "implemented", "automated", "tested", "improved", "documented"]
RISKY_TERMS = ["expert", "guru", "world-class", "guaranteed", "rockstar"]


def score_resume_ats(resume_text: str, job: JobDescription, evidence: list[EvidenceMatch]) -> dict[str, Any]:
    text = resume_text.lower()
    required = _unique(job.must_have_skills + job.nice_to_have_skills + job.keywords)
    matched_keywords = [skill for skill in required if skill.lower() in text]
    missing_keywords = [skill for skill in required if skill.lower() not in text]
    keyword_score = round((len(matched_keywords) / max(len(required), 1)) * 45)
    structure_score = _structure_score(text)
    evidence_score = _evidence_score(evidence)
    clarity_score = _clarity_score(resume_text)
    risk_penalty = _risk_penalty(text)
    final_score = max(0, min(100, keyword_score + structure_score + evidence_score + clarity_score - risk_penalty))
    return {
        "final_score": final_score,
        "grade": _grade(final_score),
        "keyword_score": keyword_score,
        "structure_score": structure_score,
        "evidence_score": evidence_score,
        "clarity_score": clarity_score,
        "risk_penalty": risk_penalty,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "recommendations": _recommendations(missing_keywords, risk_penalty, structure_score),
    }


def render_ats_report(ats: dict[str, Any]) -> str:
    lines = ["# ATS Resume Quality Report", "", f"Final Score: {ats['final_score']}/100", f"Grade: {ats['grade']}", "", "## Breakdown", "", f"- Keyword score: {ats['keyword_score']}/45", f"- Structure score: {ats['structure_score']}/20", f"- Evidence score: {ats['evidence_score']}/20", f"- Clarity score: {ats['clarity_score']}/15", f"- Risk penalty: -{ats['risk_penalty']}", "", "## Matched Keywords", ""]
    lines += [f"- {item}" for item in ats.get("matched_keywords", [])] or ["- None"]
    lines += ["", "## Missing Keywords", ""]
    lines += [f"- {item}" for item in ats.get("missing_keywords", [])] or ["- None"]
    lines += ["", "## Recommendations", ""]
    lines += [f"- {item}" for item in ats.get("recommendations", [])] or ["- No major improvements suggested."]
    return "\n".join(lines) + "\n"


def _structure_score(text: str) -> int:
    hits = sum(1 for hint in ATS_SECTION_HINTS if hint in text)
    return min(20, hits * 4 + 4)


def _evidence_score(evidence: list[EvidenceMatch]) -> int:
    if not evidence:
        return 0
    strong = sum(1 for item in evidence if item.evidence_strength == "Strong")
    medium = sum(1 for item in evidence if item.evidence_strength == "Medium")
    return min(20, strong * 4 + medium * 2)


def _clarity_score(resume_text: str) -> int:
    bullets = [line for line in resume_text.splitlines() if line.strip().startswith("-")]
    verb_hits = sum(1 for line in bullets if any(line.lower().lstrip("- ").startswith(verb) for verb in ACTION_VERBS))
    long_lines = sum(1 for line in bullets if len(line) > 220)
    score = 8 + min(7, verb_hits)
    return max(0, score - long_lines)


def _risk_penalty(text: str) -> int:
    return min(20, sum(5 for term in RISKY_TERMS if term in text))


def _recommendations(missing_keywords: list[str], risk_penalty: int, structure_score: int) -> list[str]:
    recs = []
    if missing_keywords:
        recs.append("Add missing JD keywords only where real evidence exists: " + ", ".join(missing_keywords[:8]))
    if risk_penalty:
        recs.append("Remove inflated language such as expert, guru, guaranteed, or world-class unless directly provable.")
    if structure_score < 16:
        recs.append("Use ATS-friendly section headings: Professional Summary, Core Skills, Experience, Projects, Education.")
    return recs


def _grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    if score >= 55:
        return "D"
    return "Needs Work"


def _unique(items: list[str]) -> list[str]:
    counts = Counter(item.lower() for item in items)
    result = []
    seen = set()
    for item in items:
        key = item.lower()
        if key not in seen and counts[key] >= 1:
            result.append(item)
            seen.add(key)
    return result
