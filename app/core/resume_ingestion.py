from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.core.jd_parser import KNOWN_SKILLS

SECTION_HEADERS = {
    "summary": ["summary", "professional summary", "profile"],
    "skills": ["skills", "technical skills", "core skills"],
    "experience": ["experience", "work experience", "professional experience"],
    "projects": ["projects", "selected projects", "portfolio"],
}


def ingest_resume_text(resume_text: str, candidate_name: str = "Candidate") -> dict[str, object]:
    text = resume_text.strip()
    sections = _split_sections(text)
    skills = _extract_skills(text)
    summary = _first_non_empty(sections.get("summary", ""), fallback=_guess_summary(text))
    experience_bullets = _extract_bullets(sections.get("experience", text))[:8]
    return {
        "candidate": {
            "name": candidate_name,
            "headline": _guess_headline(skills),
            "target_roles": _guess_target_roles(skills, text),
        },
        "summary": {
            "default": summary,
            "sdet_fullstack": summary,
            "genai_qa": summary,
        },
        "skills": _group_skills(skills),
        "experience": [
            {
                "title": "Imported Experience",
                "company": "Imported Resume",
                "start": "",
                "end": "",
                "bullets": experience_bullets or ["Imported resume content requires manual review."],
            }
        ],
    }


def ingest_resume_file(input_path: str | Path, output_path: str | Path, candidate_name: str = "Candidate") -> None:
    text = Path(input_path).read_text(encoding="utf-8")
    profile = ingest_resume_text(text, candidate_name=candidate_name)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _split_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {key: [] for key in SECTION_HEADERS}
    current = "summary"
    for line in lines:
        normalized = re.sub(r"[^a-z ]", "", line.strip().lower())
        matched = next((key for key, names in SECTION_HEADERS.items() if normalized in names), None)
        if matched:
            current = matched
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in lower and skill not in found:
            found.append(skill)
    return found


def _group_skills(skills: list[str]) -> dict[str, list[str]]:
    groups = {"testing": [], "automation": [], "development": [], "ai_testing": [], "devops": []}
    for skill in skills:
        key = skill.lower()
        if any(token in key for token in ["llm", "genai", "prompt", "model", "hallucination", "mcp", "ai testing"]):
            groups["ai_testing"].append(skill)
        elif any(token in key for token in ["selenium", "playwright", "cypress", "appium", "pytest", "automation"]):
            groups["automation"].append(skill)
        elif any(token in key for token in ["docker", "kubernetes", "github actions", "azure devops", "ci/cd"]):
            groups["devops"].append(skill)
        elif any(token in key for token in [".net", "react", "mvc", "python"]):
            groups["development"].append(skill)
        else:
            groups["testing"].append(skill)
    return {key: value for key, value in groups.items() if value}


def _extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[-*•]\s*", "", line.strip())
        if len(cleaned) > 20:
            bullets.append(cleaned)
    return bullets


def _guess_summary(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if 60 <= len(cleaned) <= 280:
            return cleaned
    return "Imported resume profile. Review and refine before use."


def _guess_headline(skills: list[str]) -> str:
    skill_text = " ".join(skills).lower()
    if any(token in skill_text for token in ["llm", "genai", "mcp", "hallucination"]):
        return "AI Testing / GenAI QA candidate with automation experience"
    if any(token in skill_text for token in ["selenium", "playwright", "api testing", "react", ".net"]):
        return "QA Automation / SDET candidate with full-stack exposure"
    return "QA candidate"


def _guess_target_roles(skills: list[str], text: str) -> list[str]:
    lower = " ".join(skills).lower() + " " + text.lower()
    roles = ["QA Automation Engineer", "SDET"]
    if any(token in lower for token in ["genai", "llm", "mcp", "hallucination", "prompt"]):
        roles += ["GenAI QA Engineer", "AI Testing Engineer"]
    if any(token in lower for token in ["react", ".net", "mvc"]):
        roles.append("Full Stack QA Engineer")
    return roles


def _first_non_empty(value: str, fallback: str) -> str:
    cleaned = " ".join(line.strip() for line in value.splitlines() if line.strip())
    return cleaned[:600] if cleaned else fallback
