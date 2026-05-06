from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from rich.console import Console

from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import write_application_pack
from app.core.jd_parser import parse_job_file
from app.core.profile_loader import load_profile, load_projects, load_rules

app = typer.Typer(help="PortfolioFit Agent: evidence-backed job application pack generator.")
console = Console()

DEFAULT_PROFILE = Path("profile/master_profile.example.yaml")
DEFAULT_PORTFOLIO = Path("profile/project_portfolio.example.yaml")
DEFAULT_RULES = Path("profile/resume_rules.example.yaml")


@app.command()
def init_profile(output: Path = typer.Option(Path("profile"), help="Directory for editable profile files.")) -> None:
    """Create editable profile files from examples."""
    output.mkdir(parents=True, exist_ok=True)
    for source in [DEFAULT_PROFILE, DEFAULT_PORTFOLIO, DEFAULT_RULES]:
        destination = output / source.name.replace(".example", "")
        shutil.copyfile(source, destination)
        console.print(f"Created {destination}")


@app.command()
def parse_job(job_file: Path) -> None:
    """Parse a raw job description and print structured JSON."""
    job = parse_job_file(job_file)
    console.print_json(json.dumps(job.model_dump(), indent=2))


@app.command(name="score-job")
def score_job_command(job_file: Path, profile: Path = DEFAULT_PROFILE, portfolio: Path = DEFAULT_PORTFOLIO) -> None:
    """Score job fit against profile and portfolio."""
    job = parse_job_file(job_file)
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    fit = score_job(job, candidate, projects)
    console.print_json(json.dumps(fit.model_dump(), indent=2))


@app.command()
def generate_pack(
    job_file: Path,
    profile: Path = typer.Option(DEFAULT_PROFILE, help="Candidate profile YAML."),
    portfolio: Path = typer.Option(DEFAULT_PORTFOLIO, help="Project portfolio YAML."),
    rules: Path = typer.Option(DEFAULT_RULES, help="Resume rules YAML."),
    output: Path = typer.Option(Path("outputs/applications/demo_pack"), help="Output pack directory."),
) -> None:
    """Generate a full application pack for manual approval."""
    job = parse_job_file(job_file)
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    resume_rules = load_rules(rules)
    fit = score_job(job, candidate, projects)
    evidence = map_evidence(job, candidate, projects)
    files = write_application_pack(output, job, candidate, projects, resume_rules, fit, evidence)
    console.print(f"[bold green]Application pack generated:[/bold green] {output}")
    console.print(f"Decision: [bold]{fit.decision}[/bold] | Score: [bold]{fit.final_score}/100[/bold]")
    console.print("Manual approval required before submitting any application.")
    for file in files:
        console.print(f"- {file}")


@app.command()
def validate_pack(pack_dir: Path) -> None:
    """Validate that an application pack contains required files."""
    required = [
        "01_raw_job_description.txt",
        "02_parsed_job_description.json",
        "03_fit_score.md",
        "04_evidence_map.md",
        "05_tailored_resume.md",
        "06_tailored_resume.docx",
        "07_tailored_resume.pdf",
        "08_cover_letter.md",
        "09_recruiter_message.md",
        "10_application_notes.md",
        "11_truthfulness_report.md",
    ]
    missing = [name for name in required if not (pack_dir / name).exists()]
    if missing:
        console.print("[bold red]Pack is incomplete.[/bold red]")
        for name in missing:
            console.print(f"- Missing: {name}")
        raise typer.Exit(code=1)
    console.print("[bold green]Pack is complete and ready for manual review.[/bold green]")


if __name__ == "__main__":
    app()
