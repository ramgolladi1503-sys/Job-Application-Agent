# Architecture

## Design principle

The system is intentionally CLI-first. The engine must be reliable before adding dashboards or browser automation.

## Main components

```text
app/cli/main.py
  User-facing Typer commands

app/core/profile_loader.py
  Loads candidate profile, project portfolio, and resume rules

app/core/jd_parser.py
  Converts raw job descriptions into structured job objects

app/core/fit_scorer.py
  Scores candidate-role fit with explainable breakdown

app/core/evidence_matcher.py
  Maps job requirements to real candidate/project evidence

app/core/generators.py
  Generates resume, cover letter, recruiter message, reports, DOCX, and PDF

app/core/missing_skills.py
  Separates strong matches, project evidence matches, and weak/missing skills

app/core/resume_diff.py
  Produces a unified diff between base and tailored resume

app/core/github_portfolio.py
  Converts GitHub repo file paths and README text into portfolio evidence YAML

app/core/application_tracker.py
  Appends generated packs to a CSV tracker and renders tracker summaries

app/validators/truthfulness_validator.py
  Flags forbidden or unsupported claims
```

## Data flow

```text
Raw JD text
  → JobDescription
  → FitScore
  → EvidenceMatch[]
  → generated pack files
  → tracker row
```

## Storage model

Profile and portfolio data are stored in YAML because they are readable, versionable, and easy to manually review.

Generated application packs are written to `outputs/applications/`. That folder is ignored by Git to prevent accidental exposure of real applications.

## Future architecture

A future UI should call the same core engine. Do not duplicate logic in a frontend.

Suggested future layers:

- FastAPI wrapper around core functions
- SQLite or DuckDB tracker backend
- React dashboard for pack preview and approval
- GitHub API integration for repository evidence ingestion
- Resume diff viewer UI
