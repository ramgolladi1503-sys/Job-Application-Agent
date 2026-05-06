from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models import CandidateProfile, Project, ResumeRules


def _read_yaml(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {file_path}")
    return data


def load_profile(path: str | Path) -> CandidateProfile:
    return CandidateProfile.model_validate(_read_yaml(path))


def load_projects(path: str | Path) -> list[Project]:
    data = _read_yaml(path)
    return [Project.model_validate(item) for item in data.get("projects", [])]


def load_rules(path: str | Path) -> ResumeRules:
    return ResumeRules.model_validate(_read_yaml(path))
