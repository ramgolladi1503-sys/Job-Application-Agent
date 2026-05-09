# Connected Profile Pipeline

The connected profile pipeline turns PortfolioFit Agent from a single-job pack generator into an end-to-end preparation workflow.

## Goal

```text
Connected profile config
  -> sync profile and portfolio evidence
  -> fetch job-alert emails or read saved job exports
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

## No-manual-export workflow

This is the recommended workflow if you do not want to manually export job alerts.

```text
1. Create job alerts once on LinkedIn, Naukri, Indeed, Monster, or company career pages.
2. Route those alerts to a mailbox you control.
3. Add IMAP credentials as GitHub Secrets.
4. Run Profile Pipeline with fetch_email_alerts=true.
5. Download profile-pipeline-output.
```

Required GitHub Secrets:

```text
JOB_ALERT_IMAP_HOST       example: imap.gmail.com
JOB_ALERT_IMAP_USERNAME   mailbox username
JOB_ALERT_IMAP_PASSWORD   app password / mailbox password
```

Optional GitHub Secrets:

```text
JOB_ALERT_IMAP_MAILBOX    default: INBOX
JOB_ALERT_IMAP_QUERY      default: (OR SUBJECT "job alert" SUBJECT "jobs")
```

For Gmail, use an app password. Do not use your normal Gmail password.

Manual run path:

```text
Actions -> Profile Pipeline -> Run workflow -> fetch_email_alerts=true
```

The workflow fetches matching emails into:

```text
data/job_alert_exports/
```

Then the saved-alert discovery config picks them up automatically.

## Run locally

Fetch job-alert emails locally:

```bash
export JOB_ALERT_IMAP_HOST=imap.gmail.com
export JOB_ALERT_IMAP_USERNAME=your_alert_mailbox@gmail.com
export JOB_ALERT_IMAP_PASSWORD=your_app_password
portfoliofit fetch-job-alert-emails --output data/job_alert_exports --limit 50
```

Run the pipeline:

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

Preferred method: job alerts through email. This avoids brittle scraping and account-risk behavior.

Fallback method: save/export the alert email, job page, or listing as `.html`, `.txt`, or `.eml`.

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
