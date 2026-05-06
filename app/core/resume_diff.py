from __future__ import annotations

import difflib
from pathlib import Path


def create_resume_diff(base_resume: str, tailored_resume: str) -> str:
    base_lines = base_resume.splitlines()
    tailored_lines = tailored_resume.splitlines()
    diff = difflib.unified_diff(
        base_lines,
        tailored_lines,
        fromfile="base_resume.md",
        tofile="tailored_resume.md",
        lineterm="",
    )
    return "# Resume Diff\n\n```diff\n" + "\n".join(diff) + "\n```\n"


def create_resume_diff_from_files(base_path: str | Path, tailored_path: str | Path) -> str:
    base = Path(base_path).read_text(encoding="utf-8")
    tailored = Path(tailored_path).read_text(encoding="utf-8")
    return create_resume_diff(base, tailored)
