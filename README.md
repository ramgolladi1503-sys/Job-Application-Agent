# PortfolioFit Agent

Evidence-based job application preparation agent that scores job fit, maps real portfolio proof to role requirements, and generates tailored resumes, cover letters, recruiter messages, and application packs for manual approval.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![CLI](https://img.shields.io/badge/interface-Typer%20CLI-green)
![Safety](https://img.shields.io/badge/auto--apply-disabled-red)

## What it does

PortfolioFit Agent turns a raw job description into a reviewable application pack:

```text
Candidate profile + project portfolio + job description
        ↓
JD parsing
        ↓
Fit scoring
        ↓
Evidence mapping
        ↓
Tailored resume
        ↓
Cover letter
        ↓
Recruiter message
        ↓
Application pack
        ↓
Manual user approval
```

This project does **not** auto-apply to LinkedIn, Indeed, Naukri, Workday, or company portals. It prepares truthful material. The candidate reviews and submits manually.

## Why it exists

Most resume generators produce generic, inflated output. PortfolioFit Agent is built around one stricter rule:

> Every strong resume claim must trace back to profile data, work history, or project evidence.

That makes it useful for serious candidates who want targeted applications without fake experience.

## Key features

- Structured candidate profile loader
- Project portfolio evidence engine
- Heuristic job description parser
- Fit scoring with reasoning
- Evidence-to-requirement mapping
- Role-specific resume generation
- Cover letter generation
- Recruiter message generation
- Application pack folder creation
- Truthfulness validator
- Markdown, DOCX, and PDF exports
- CLI-first workflow
- Docker support
- GitHub Actions CI
- Pytest coverage

## Best use cases

### .NET + React + QA Automation role

Highlights:

- QA automation
- SDET-style test strategy
- API testing
- .NET Core / React exposure
- Docker and CI/CD validation
- Tradebot-style financial workflow validation

### GenAI QA / AI Testing role

Highlights:

- MCP Shield
- LLM validation
- Hallucination risk testing
- Prompt behavior checks
- AI tool-use policy controls
- Model behavior validation
- Automation-backed test strategy

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Or with requirements:

```bash
pip install -r requirements.txt
```

## Quick start

Generate a pack for a sample .NET + React + QA job:

```bash
portfoliofit generate-pack \
  data/sample_jobs/dotnet_react_qa_job.txt \
  --profile profile/master_profile.example.yaml \
  --portfolio profile/project_portfolio.example.yaml \
  --rules profile/resume_rules.example.yaml \
  --output outputs/applications/dotnet_react_qa_demo
```

Generate a pack for a GenAI QA role:

```bash
portfoliofit generate-pack \
  data/sample_jobs/genai_qa_job.txt \
  --profile profile/master_profile.example.yaml \
  --portfolio profile/project_portfolio.example.yaml \
  --rules profile/resume_rules.example.yaml \
  --output outputs/applications/genai_qa_demo
```

## CLI commands

```bash
portfoliofit init-profile
portfoliofit parse-job data/sample_jobs/dotnet_react_qa_job.txt
portfoliofit score-job data/sample_jobs/dotnet_react_qa_job.txt
portfoliofit generate-pack data/sample_jobs/genai_qa_job.txt
portfoliofit validate-pack outputs/applications/genai_qa_demo
```

## Application pack output

Each generated pack contains:

```text
01_raw_job_description.txt
02_parsed_job_description.json
03_fit_score.md
04_evidence_map.md
05_tailored_resume.md
06_tailored_resume.docx
07_tailored_resume.pdf
08_cover_letter.md
09_recruiter_message.md
10_application_notes.md
11_truthfulness_report.md
```

## Safety boundary

This project intentionally excludes:

- Auto-submit
- LinkedIn auto-apply
- Captcha bypass
- Portal automation
- Mass application spam
- Fake skill injection
- Unsupported resume claims

## Project status

MVP scaffold is ready: CLI, parser, scorer, evidence mapper, generators, validators, sample data, docs, tests, Docker, and CI.

## License

MIT
