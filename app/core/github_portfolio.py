from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

import yaml

TECH_HINTS = {
    "Python": [".py", "pytest", "pydantic", "typer", "fastapi"],
    "JavaScript": [".js", "package.json", "node", "react"],
    "TypeScript": [".ts", "typescript", "tsx"],
    "React": ["react", "jsx", "tsx"],
    "Docker": ["dockerfile", "docker-compose"],
    "GitHub Actions": [".github/workflows", "ci.yml"],
    "Testing": ["tests/", "pytest", "unittest", "selenium", "playwright", "cypress"],
    "AI Testing": ["llm", "genai", "mcp", "prompt", "model", "hallucination"],
    "CI/CD": ["ci.yml", "pipeline", "github actions", "azure-pipelines"],
}

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"}


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
    if any(path.lower().endswith(("requirements.txt", "pyproject.toml", "package.json")) for path in file_paths):
        evidence.append("Repository includes dependency/package configuration.")
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


def scan_local_repo(repo_path: str | Path) -> tuple[str, list[str], str]:
    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path not found: {root}")
    file_paths: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in IGNORED_DIRS for part in relative.split("/")):
            continue
        file_paths.append(relative)
    readme_text = _read_first_existing(root, ["README.md", "readme.md", "README.txt"])
    return root.name, sorted(file_paths), readme_text


def fetch_github_repo_tree(owner: str, repo: str, ref: str = "main") -> tuple[str, list[str], str]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    try:
        payload = _fetch_json(api_url)
    except Exception:
        if ref != "master":
            return fetch_github_repo_tree(owner, repo, ref="master")
        raise
    file_paths = sorted(item["path"] for item in payload.get("tree", []) if item.get("type") == "blob")
    readme_text = _fetch_readme(owner, repo, ref)
    return repo, file_paths, readme_text


def write_portfolio_summary(repo_name: str, file_paths: list[str], output_path: str | Path, readme_text: str = "") -> None:
    summary = {"projects": [summarize_repo_tree(repo_name, file_paths, readme_text)]}
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(summary, sort_keys=False), encoding="utf-8")


def write_local_repo_summary(repo_path: str | Path, output_path: str | Path) -> None:
    repo_name, paths, readme_text = scan_local_repo(repo_path)
    write_portfolio_summary(repo_name, paths, output_path, readme_text)


def write_remote_repo_summary(owner: str, repo: str, output_path: str | Path, ref: str = "main") -> None:
    repo_name, paths, readme_text = fetch_github_repo_tree(owner, repo, ref)
    write_portfolio_summary(repo_name, paths, output_path, readme_text)


def _fetch_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "portfoliofit-agent"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_readme(owner: str, repo: str, ref: str) -> str:
    for name in ["README.md", "readme.md", "README.txt"]:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{name}"
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "portfoliofit-agent"})
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception:
            continue
    return ""


def _read_first_existing(root: Path, names: list[str]) -> str:
    for name in names:
        path = root / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _relevant_for(tech_stack: list[str], text: str) -> list[str]:
    roles = []
    if "Testing" in tech_stack:
        roles += ["QA Automation", "SDET"]
    if "AI Testing" in tech_stack:
        roles += ["GenAI QA", "AI Testing"]
    if "React" in tech_stack:
        roles.append("Full Stack QA")
    if "Docker" in tech_stack or "GitHub Actions" in tech_stack or "CI/CD" in tech_stack:
        roles.append("CI/CD Testing")
    return roles or ["Software Portfolio"]
