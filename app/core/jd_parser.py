from __future__ import annotations

import re
from pathlib import Path

from app.models import JobDescription

KNOWN_SKILLS = [
    ".NET Core", "React", "MVC", "Docker", "Kubernetes", "GitHub Actions", "Azure DevOps", "CI/CD",
    "Selenium", "Playwright", "Appium", "Pytest", "API Testing", "Regression Testing",
    "Functional Testing", "Manual Testing", "Automation Testing", "Python", "GenAI", "AI Testing",
    "LLM Evaluation", "LLM", "Prompt Testing", "Model Validation", "Hallucination Testing", "MCP",
    "Security Testing", "Risk Analysis", "Test Strategy",
]

DOMAIN_KEYWORDS = {
    "FinTech": ["fintech", "financial", "trading", "banking", "payments"],
    "AI": ["genai", "llm", "ai", "model", "prompt", "mcp"],
    "Healthcare": ["healthcare", "medical", "patient"],
    "E-commerce": ["commerce", "retail", "shopping"],
}


def parse_job_file(path: str | Path) -> JobDescription:
    return parse_job_description(Path(path).read_text(encoding="utf-8"))


def parse_job_description(raw_text: str) -> JobDescription:
    text = raw_text.strip()
    lower = text.lower()
    role_title = _extract_field(text, ["Role", "Job Title", "Title"]) or _guess_role_title(text)
    company = _extract_field(text, ["Company", "Organization"]) or "Unknown Company"
    location = _extract_field(text, ["Location"]) or "Unknown"
    seniority = _extract_field(text, ["Seniority", "Level"]) or _guess_seniority(lower)
    must_section = _extract_section(text, ["must have", "required", "requirements"])
    nice_section = _extract_section(text, ["good to have", "nice to have", "preferred"])
    responsibilities_section = _extract_section(text, ["responsibilities", "what you will do"])
    must_have = _skills_in_text(must_section or text)
    nice_to_have = [s for s in _skills_in_text(nice_section) if s not in must_have]
    if not must_have:
        must_have = _skills_in_text(text)[:8]
    return JobDescription(
        role_title=role_title,
        company=company,
        location=location,
        seniority=seniority,
        must_have_skills=must_have,
        nice_to_have_skills=nice_to_have,
        responsibilities=_extract_bullets(responsibilities_section),
        domain=_guess_domain(lower),
        keywords=sorted(set(_skills_in_text(text))),
        red_flags=_red_flags(lower),
        raw_text=text,
    )


def _extract_field(text: str, names: list[str]) -> str | None:
    for name in names:
        match = re.search(rf"^{re.escape(name)}\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _guess_role_title(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first_line if len(first_line) < 90 else "Unknown Role"


def _guess_seniority(lower: str) -> str:
    if "senior" in lower or "lead" in lower:
        return "Senior"
    if "junior" in lower or "entry" in lower:
        return "Junior"
    if "mid" in lower or "3+" in lower or "5+" in lower:
        return "Mid-Level"
    return "Unknown"


def _extract_section(text: str, headers: list[str]) -> str:
    pattern = "|".join(re.escape(header) for header in headers)
    match = re.search(rf"({pattern})\s*:?\s*(.*?)(\n\s*\n|\n[A-Z][A-Za-z /]+:|\Z)", text, re.IGNORECASE | re.DOTALL)
    return match.group(2).strip() if match else ""


def _skills_in_text(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in lower and skill not in found:
            found.append(skill)
    return found


def _extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[-*•]\s*", "", line.strip())
        if cleaned:
            bullets.append(cleaned)
    return bullets


def _guess_domain(lower: str) -> str:
    scores = {domain: sum(1 for keyword in keywords if keyword in lower) for domain, keywords in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


def _red_flags(lower: str) -> list[str]:
    flags = []
    if "phd" in lower:
        flags.append("Role may expect research-level background.")
    if "production kubernetes ownership" in lower:
        flags.append("Kubernetes ownership may be deeper than current evidence.")
    if "auto apply" in lower:
        flags.append("Auto-apply behavior is outside this project's ethical boundary.")
    return flags
