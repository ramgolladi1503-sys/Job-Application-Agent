# Profile and Portfolio Ingestion

This document explains how PortfolioFit Agent turns resume text and repository evidence into structured YAML.

## Resume import

Use this when you have a plain-text resume export and want a starter profile YAML.

```bash
portfoliofit import-resume resume.txt \
  --candidate-name "Ram Golladi" \
  --output profile/master_profile.generated.yaml
```

The generated file should be reviewed manually before real applications. Resume import is a starter, not a source of unquestioned truth.

## Local repository scan

Use this when the repository exists on your machine.

```bash
portfoliofit scan-local-repo ../tradebot \
  --output profile/tradebot.generated.yaml
```

The scanner reads file paths and README content. It ignores noisy folders like `.git`, `.venv`, `node_modules`, `__pycache__`, `dist`, and `build`.

## Remote public GitHub scan

Use this for public repositories.

```bash
portfoliofit fetch-github-repo ramgolladi1503-sys Job-Application-Agent \
  --output profile/job_agent.generated.yaml
```

The command uses the GitHub tree API and README from `raw.githubusercontent.com`.

If rate limits become a problem, set:

```bash
export GITHUB_TOKEN=your_token_here
```

## Manual file-list ingestion

Use this when you already have a list of repo paths.

```bash
portfoliofit ingest-github-repo my-repo file_list.txt \
  --readme README.md \
  --output profile/my_repo.generated.yaml
```

## Output shape

Generated portfolio YAML follows this structure:

```yaml
projects:
  - name: repo-name
    type: GitHub repository summary
    role: Repository owner / contributor
    tech_stack: []
    relevant_for: []
    evidence: []
    safe_resume_bullets: []
    metadata:
      source: github_repo_scan
      file_count: 0
      has_readme: true
```

## Hard rule

Generated repository evidence is not automatically perfect. It is evidence to review, not permission to exaggerate.
