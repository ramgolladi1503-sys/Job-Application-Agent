# Connected Profile Pipeline

The connected profile pipeline turns PortfolioFit Agent from a single-job pack generator into an end-to-end preparation workflow.

## Goal

```text
Connected profile config
  -> sync profile and portfolio evidence
  -> read saved job alerts / job exports
  -> discover roles
  -> filter by fit score and blocked keywords
  -> generate application packs
  -> create next-action report
  -> wait for manual review/submission
```

## Main config

```text
config/profile_pipeline.yaml
```

This config connects:

```text
profile/master_profile.yaml
profile/project_portfolio.yaml
profile/resume_rules.yaml
config/job_sources.saved_alerts.yaml
outputs/job_discovery/profile_pipeline
outputs/applications/profile_pipeline
```

## Run locally

```bash
portfoliofit run-profile-pipeline --config config/profile_pipeline.yaml
```

Outputs:

```text
outputs/job_discovery/profile_pipeline/jobs.json
outputs/job_discovery/profile_pipeline/discovery_report.md
outputs/job_discovery/profile_pipeline/job_descriptions/*.txt
outputs/applications/profile_pipeline/00_next_actions.md
outputs/applications/profile_pipeline/00_pipeline_results.csv
outputs/applications/profile_pipeline/<company_role_score>/
```

## Run from GitHub Actions

Workflow:

```text
.github/workflows/profile-pipeline.yml
```

Manual run path:

```text
Actions -> Profile Pipeline -> Run workflow
```

Artifact:

```text
profile-pipeline-output
```

## How to connect your profiles safely

### GitHub

The pipeline can sync public/private GitHub repo metadata through the GitHub API when `GITHUB_TOKEN` is available.

Configure repositories in:

```yaml
portfolio_sync:
  enabled: true
  generated_output: profile/github_profile_pipeline.generated.yaml
  github_repositories:
    - owner: ramgolladi1503-sys
      repo: Job-Application-Agent
      ref: main
      enabled: true
```

Generated repo evidence is written separately for review. Do not blindly merge it into your main portfolio without checking it.

### LinkedIn / Naukri / Indeed / Monster

Use saved exports, not aggressive scraping.

```text
1. Create job alerts on the platform.
2. Save/export the alert email, job page, or listing as .html, .txt, or .eml.
3. Drop it into data/job_alert_exports/.
4. Run the pipeline.
```

The saved-alert config automatically picks up:

```text
data/job_alert_exports/*.html
data/job_alert_exports/*.txt
data/job_alert_exports/*.eml
```

## Filtering

Controlled in `config/profile_pipeline.yaml`:

```yaml
filtering:
  min_fit_score: 70
  high_priority_score: 82
  blocked_keywords:
    - PhD required
    - Senior ML Research Scientist
```

Jobs below threshold are skipped. Jobs matching blocked keywords are skipped even if the score looks decent.

## Next-action report

The final report is:

```text
outputs/applications/profile_pipeline/00_next_actions.md
```

It groups jobs into:

```text
High Priority Applications
Normal Generated Applications
Skipped Roles
```

## Boundary

The pipeline prepares material only. It does not submit applications or send recruiter messages.
