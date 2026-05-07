from __future__ import annotations

from pathlib import Path

from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import write_application_pack
from app.core.jd_parser import parse_job_file
from app.core.profile_loader import load_profile, load_projects, load_rules

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile/master_profile.example.yaml"
PORTFOLIO = ROOT / "profile/project_portfolio.example.yaml"
RULES = ROOT / "profile/resume_rules.example.yaml"

EXAMPLES = [
    (ROOT / "data/sample_jobs/genai_qa_job.txt", ROOT / "examples/generated/genai_qa_application_pack"),
    (ROOT / "data/sample_jobs/dotnet_react_qa_job.txt", ROOT / "examples/generated/dotnet_react_qa_application_pack"),
]


def main() -> None:
    profile = load_profile(PROFILE)
    projects = load_projects(PORTFOLIO)
    rules = load_rules(RULES)
    for job_path, output_dir in EXAMPLES:
        job = parse_job_file(job_path)
        fit = score_job(job, profile, projects)
        evidence = map_evidence(job, profile, projects)
        write_application_pack(output_dir, job, profile, projects, rules, fit, evidence)
        readme = output_dir / "README.md"
        readme.write_text(
            "# Generated Example Application Pack\n\n"
            "This folder is generated from the sample profile, sample portfolio, and sample job description.\n\n"
            "Run `python scripts/generate_examples.py` to refresh it.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
