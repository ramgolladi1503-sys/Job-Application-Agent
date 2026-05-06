from __future__ import annotations

import re
from pathlib import Path

import yaml

TECH_HINTS = {
    "Python": [".py", "pytest", "pydantic", "typer", "fastapi"],
    "JavaScript": [".js", "package.json", "node", "react"],
    "TypeScript": [".ts", "typescript", "tsx"],
    "React": ["react", "jsx", "tsx"],
    "Docker": ["dockerfile", "docker-compose"],
    "GitHub Actions": [".github/workflows", "ci.yml"],
    "Testing": ["tests/", "pytest", "unittest", "selenium", "playwright"],
    "AI Testing": ["llm", "genai", "mcp", "prompt", "model", "hallucination"],
}


def summarize_repo_tree(repo_name: str, file_paths: list[str], readme_text: str = "") -> dict[str, object]:
    text = "\n".join(file_paths + [readme_text]).lower()
    tech_stack = []
    evidence = []
    for tech, hints in TECH_HINTS.items():
        if any(hint.lower() in text for hint in hints):
            tech_stack.append(tech)
    if any(path.startswith("tests/") or "/tests/" in path for path in file_paths):
        evidence.append("Repository includes automated test structure.")
    if any(".github/workflows" in path for path in file_paths):
        evidence.append("Repository includes GitHub Actions workflow configuration.")
    if any("docker" in path.lower() for path in file_paths):
        evidence.append("Repository includes Docker-related configuration.")
    if re.search(r"\b(mcp|llm|genai|prompt|hallucination)\b", text):
        evidence.append("Repository contains AI or GenAI validation-related signals.")
    if not evidence:
        evidence.append("Repository evidence should be reviewed manually before using in resume claims.")
    return {
        "name": repo_name,
        "type": "GitHub repository summary",
        "role": "Repository owner / contributor",
        "tech_stack": tech_stack,
        "relevant_for": _relevant_for(tech_stack, text),
        "evidence": evidence,
        "safe_resume_bullets": [
            f"Maintained {repo_name} with evidence of {', '.join(tech_stack[:4]) or 'software project structure'} and reviewable project artifacts."
        ],
    }


def write_portfolio_summary(repo_name: str, file_paths: list[str], output_path: str | Path, readme_text: str = "") -> None:
    summary = {"projects": [summarize_repo_tree(repo_name, file_paths, readme_text)]}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(summary, sort_keys=False), encoding="utf-8")


def _relevant_for(tech_stack: list[str], text: str) -> list[str]:
    roles = []
    if "Testing" in tech_stack:
        roles += ["QA Automation", "SDET"]
    if "AI Testing" in tech_stack:
        roles += ["GenAI QA", "AI Testing"]
    if "React" in tech_stack:
        roles.append("Full Stack QA")
    if "Docker" in tech_stack or "GitHub Actions" in tech_stack:
        roles.append("CI/CD Testing")
    return roles or ["Software Portfolio"]
