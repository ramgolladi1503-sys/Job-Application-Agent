# Job Discovery Agent

PortfolioFit Agent can discover job leads from configured sources, normalize them into job-description files, score them, and generate application packs.

## What this does

```text
Configured job sources
  -> fetch/read public or exported job content
  -> extract job leads
  -> normalize into JD text files
  -> score fit
  -> generate application packs for strong matches
  -> draft recruiter / hiring-manager messages
  -> wait for manual approval
```

## What this does not do

This project does not:

```text
- auto-apply to LinkedIn, Naukri, Indeed, Monster, Workday, or company portals
- bypass login walls, CAPTCHAs, anti-bot controls, or robots restrictions
- auto-message recruiters or hiring managers
- spam job boards
- fake experience
```

## Configure sources

Start from:

```text
config/job_sources.example.yaml
```

Supported source types:

```text
file        saved HTML, exported job-alert email, or local text source
url         public URL
search_url  public search/career page URL
```

Best sources:

```text
- Company career pages
- Public job alert emails saved as HTML/text
- Public RSS/search pages
- Manually exported job posts
```

Risky sources:

```text
- LinkedIn pages behind login
- Job sites that block automated fetches
- Pages requiring CAPTCHA
- Sites with restrictive terms
```

Use those only through manual export or compliant access.

## Discover jobs

```bash
portfoliofit discover-jobs \
  --config config/job_sources.example.yaml \
  --output outputs/job_discovery/latest \
  --limit 25
```

Outputs:

```text
outputs/job_discovery/latest/jobs.json
outputs/job_discovery/latest/discovery_report.md
outputs/job_discovery/latest/job_descriptions/*.txt
```

## Generate packs from discovered jobs

```bash
portfoliofit generate-packs-from-discovery \
  outputs/job_discovery/latest/jobs.json \
  --profile profile/master_profile.yaml \
  --portfolio profile/project_portfolio.yaml \
  --rules profile/resume_rules.yaml \
  --output outputs/applications/discovered_jobs \
  --min-score 70
```

The agent skips jobs below the minimum score and generates packs only for strong matches.

## Hiring manager / recruiter outreach

Generated packs include:

```text
09_recruiter_message.md
```

This is a draft only. You review, edit, and send manually.

## Hard rule

Job discovery is for preparation and prioritization. Submission and outreach stay human-controlled.
