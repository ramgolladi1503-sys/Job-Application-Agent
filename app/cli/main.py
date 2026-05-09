from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer
from rich.console import Console

from app.core.application_tracker import export_tracker, render_tracker_summary, update_application_status
from app.core.ats_scorer import render_ats_report, score_resume_ats
from app.core.email_job_ingestion import fetch_job_alert_emails_from_env
from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import render_resume, write_application_pack
from app.core.github_portfolio import write_local_repo_summary, write_portfolio_summary, write_remote_repo_summary
from app.core.interview_prep import generate_interview_prep, render_interview_prep
from app.core.jd_parser import parse_job_file
from app.core.job_discovery import discover_jobs_from_config, load_discovered_jobs, write_job_lead_files
from app.core.profile_loader import load_profile, load_projects, load_rules
from app.core.profile_pipeline import run_profile_pipeline
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


@app.command(name="fetch-job-alert-emails")
def fetch_job_alert_emails_command(
    output: Path = typer.Option(Path("data/job_alert_exports"), help="Folder to write fetched alert text files."),
    limit: int = typer.Option(25, help="Maximum number of matching emails to fetch."),
) -> None:
    """Fetch job-alert emails through IMAP using JOB_ALERT_IMAP_* environment variables."""
    paths = fetch_job_alert_emails_from_env(output, limit=limit)
    console.print(f"[bold green]Fetched {len(paths)} job-alert email(s).[/bold green]")
    for path in paths:
        console.print(f"- {path}")


@app.command(name="run-profile-pipeline")
def run_profile_pipeline_command(
    config: Path = typer.Option(Path("config/profile_pipeline.yaml"), help="Profile pipeline config YAML."),
) -> None:
    """Run profile sync, job discovery, filtering, pack generation, and next-action reporting."""
    result = run_profile_pipeline(config)
    console.print("[bold green]Profile pipeline completed.[/bold green]")
    console.print(f"Discovered: {result.discovered_count}")
    console.print(f"Generated packs: {result.generated_count}")
    console.print(f"Skipped: {result.skipped_count}")
    console.print(f"Next actions: {result.next_actions_path}")
    console.print(f"Output directory: {result.output_dir}")


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


@app.command(name="discover-jobs")
def discover_jobs(
    config: Path = typer.Option(Path("config/job_sources.example.yaml"), help="YAML file containing compliant job sources."),
    output: Path = typer.Option(Path("outputs/job_discovery/latest"), help="Discovery output directory."),
    limit: int = typer.Option(25, help="Maximum number of job leads to keep."),
) -> None:
    """Discover job leads from configured public/file sources and save normalized JD files."""
    leads = discover_jobs_from_config(config, output, limit=limit)
    console.print(f"[bold green]Discovered {len(leads)} job lead(s).[/bold green]")
    console.print(f"Report: {output / 'discovery_report.md'}")
    console.print(f"Job descriptions: {output / 'job_descriptions'}")


@app.command(name="generate-packs-from-discovery")
def generate_packs_from_discovery(
    discovered_json: Path = typer.Argument(..., help="Path to outputs/job_discovery/.../jobs.json"),
    profile: Path = typer.Option(Path("profile/master_profile.yaml"), help="Candidate profile YAML."),
    portfolio: Path = typer.Option(Path("profile/project_portfolio.yaml"), help="Project portfolio YAML."),
    rules: Path = typer.Option(Path("profile/resume_rules.yaml"), help="Resume rules YAML."),
    output: Path = typer.Option(Path("outputs/applications/discovered_jobs"), help="Output folder for generated packs."),
    min_score: int = typer.Option(70, help="Only generate packs for jobs scoring at or above this fit score."),
) -> None:
    """Score discovered jobs and generate application packs for strong matches."""
    leads = load_discovered_jobs(discovered_json)
    job_files = write_job_lead_files(leads, output / "job_descriptions")
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    resume_rules = load_rules(rules)
    generated = 0
    for job_file in job_files:
        job = parse_job_file(job_file)
        fit = score_job(job, candidate, projects)
        if fit.final_score < min_score:
            console.print(f"[yellow]Skipped[/yellow] {job.role_title} at {job.company}: {fit.final_score}/100")
            continue
        evidence = map_evidence(job, candidate, projects)
        pack_dir = output / _safe_folder_name(f"{job.company}_{job.role_title}_{fit.final_score}")
        write_application_pack(pack_dir, job, candidate, projects, resume_rules, fit, evidence)
        generated += 1
        console.print(f"[green]Generated[/green] {pack_dir} ({fit.final_score}/100)")
    console.print(f"[bold green]Generated {generated} application pack(s).[/bold green]")


@app.command(name="score-job")
def score_job_command(job_file: Path, profile: Path = DEFAULT_PROFILE, portfolio: Path = DEFAULT_PORTFOLIO) -> None:
    """Score job fit against profile and portfolio."""
    job = parse_job_file(job_file)
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    fit = score_job(job, candidate, projects)
    console.print_json(json.dumps(fit.model_dump(), indent=2))


@app.command(name="ats-score")
def ats_score_command(job_file: Path, profile: Path = DEFAULT_PROFILE, portfolio: Path = DEFAULT_PORTFOLIO) -> None:
    """Generate an ATS score report for the tailored resume preview."""
    job = parse_job_file(job_file)
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    fit = score_job(job, candidate, projects)
    evidence = map_evidence(job, candidate, projects)
    resume = render_resume(job, candidate, projects, fit, evidence)
    console.print(render_ats_report(score_resume_ats(resume, job, evidence)))


@app.command(name="interview-prep")
def interview_prep_command(job_file: Path, profile: Path = DEFAULT_PROFILE, portfolio: Path = DEFAULT_PORTFOLIO) -> None:
    """Generate interview prep from a job description and evidence map."""
    job = parse_job_file(job_file)
    candidate = load_profile(profile)
    projects = load_projects(portfolio)
    fit = score_job(job, candidate, projects)
    evidence = map_evidence(job, candidate, projects)
    console.print(render_interview_prep(generate_interview_prep(job, fit, evidence)))


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
    """Fetch a GitHub repository tree through the GitHub API and create portfolio evidence YAML."""
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
        "14_ats_score_report.md",
        "15_interview_prep.md",
    ]
    missing = [name for name in required if not (pack_dir / name).exists()]
    if missing:
        console.print("[bold red]Pack is incomplete.[/bold red]")
        for name in missing:
            console.print(f"- Missing: {name}")
        raise typer.Exit(code=1)
    console.print("[bold green]Pack is complete and ready for manual review.[/bold green]")


def _safe_folder_name(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value)
    return "_".join(part for part in cleaned.split("_") if part)[:120]


if __name__ == "__main__":
    app()
