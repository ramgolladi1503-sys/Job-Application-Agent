from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from rich.console import Console

from app.core.application_tracker import export_tracker, render_tracker_summary, update_application_status
from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import write_application_pack
from app.core.github_portfolio import write_local_repo_summary, write_portfolio_summary, write_remote_repo_summary
from app.core.jd_parser import parse_job_file
from app.core.profile_loader import load_profile, load_projects, load_rules
from app.core.resume_ingestion import ingest_resume_file

app = typer.Typer(help="PortfolioFit Agent: evidence-backed job application pack generator.")
console = Console()

DEFAULT_PROFILE = Path("profile/master_profile.example.yaml")
DEFAULT_PORTFOLIO = Path("profile/project_portfolio.example.yaml")
DEFAULT_RULES = Path("profile/resume_rules.example.yaml")
DEFAULT_TRACKER = Path("outputs/applications/application_tracker.csv")


@app.command()
def init_profile(output: Path = typer.Option(Path("profile"), help="Directory for editable profile files.")) -> None:
    """Create editable profile files from examples."""
    output.mkdir(parents=True, exist_ok=True)
    for source in [DEFAULT_PROFILE, DEFAULT_PORTFOLIO, DEFAULT_RULES]:
        destination = output / source.name.replace(".example", "")
        shutil.copyfile(source, destination)
        console.print(f"Created {destination}")


@app.command(name="import-resume")
def import_resume(
    resume_text_file: Path,
    candidate_name: str = typer.Option("Candidate", help="Candidate name to write into generated YAML."),
    output: Path = typer.Option(Path("profile/master_profile.generated.yaml")),
) -> None:
    """Create a starter profile YAML from a plain-text resume export."""
    ingest_resume_file(resume_text_file, output, candidate_name=candidate_name)
    console.print(f"[bold green]Profile YAML generated:[/bold green] {output}")
    console.print("Review this generated profile before using it for real applications.")


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


@app.command(name="ingest-github-repo")
def ingest_github_repo(
    repo_name: str,
    file_list: Path = typer.Argument(..., help="Text file containing one repo path per line."),
    readme: Path | None = typer.Option(None, help="Optional README text file."),
    output: Path = typer.Option(Path("profile/github_portfolio.generated.yaml")),
) -> None:
    """Convert a file listing into portfolio evidence YAML."""
    paths = [line.strip() for line in file_list.read_text(encoding="utf-8").splitlines() if line.strip()]
    readme_text = readme.read_text(encoding="utf-8") if readme else ""
    write_portfolio_summary(repo_name, paths, output, readme_text)
    console.print(f"[bold green]GitHub portfolio summary written:[/bold green] {output}")


@app.command(name="scan-local-repo")
def scan_local_repo(
    repo_path: Path,
    output: Path = typer.Option(Path("profile/github_portfolio.generated.yaml")),
) -> None:
    """Scan a local repository folder and create portfolio evidence YAML."""
    write_local_repo_summary(repo_path, output)
    console.print(f"[bold green]Local repo portfolio summary written:[/bold green] {output}")


@app.command(name="fetch-github-repo")
def fetch_github_repo(
    owner: str,
    repo: str,
    ref: str = typer.Option("main", help="Git ref/branch to scan."),
    output: Path = typer.Option(Path("profile/github_portfolio.generated.yaml")),
) -> None:
    """Fetch a public GitHub repository tree through the GitHub API and create portfolio evidence YAML."""
    write_remote_repo_summary(owner, repo, output, ref=ref)
    console.print(f"[bold green]Remote GitHub portfolio summary written:[/bold green] {output}")


@app.command(name="tracker-summary")
def tracker_summary(tracker: Path = typer.Option(DEFAULT_TRACKER)) -> None:
    """Render a Markdown summary of prepared application packs."""
    console.print(render_tracker_summary(tracker))


@app.command(name="tracker-update")
def tracker_update(
    company: str,
    role_title: str,
    status: str,
    tracker: Path = typer.Option(DEFAULT_TRACKER),
    follow_up_date: str = typer.Option(""),
    notes: str = typer.Option(""),
) -> None:
    """Update tracker status for matching company and role."""
    updated = update_application_status(tracker, company, role_title, status, follow_up_date, notes)
    if not updated:
        console.print("[bold red]No matching tracker rows found.[/bold red]")
        raise typer.Exit(code=1)
    console.print(f"[bold green]Updated {updated} tracker row(s).[/bold green]")


@app.command(name="tracker-export")
def tracker_export(
    output: Path,
    tracker: Path = typer.Option(DEFAULT_TRACKER),
) -> None:
    """Export tracker CSV to another path."""
    export_tracker(tracker, output)
    console.print(f"[bold green]Tracker exported:[/bold green] {output}")


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
        "12_missing_skills_report.md",
        "13_resume_diff.md",
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
