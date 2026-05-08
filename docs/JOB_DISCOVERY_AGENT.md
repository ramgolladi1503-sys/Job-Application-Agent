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

## Saved job-alert workflow

For LinkedIn, Naukri, Indeed, Monster, and similar job boards, the safest workflow is:

```text
1. Create job alerts on the job site.
2. Open the alert email or job page yourself.
3. Save/export the HTML or text.
4. Put the exported file under data/job_alert_exports/.
5. Add it as a file source in config/job_sources.example.yaml.
6. Run discovery and pack generation.
```

Example source:

```yaml
sources:
  - name: linkedin_genai_qa_alert_export
    type: file
    enabled: true
    path: data/job_alert_exports/linkedin_genai_qa_alert.html
```

This keeps control with you and avoids brittle or non-compliant scraping.

## Discover jobs locally

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

## Generate packs from discovered jobs locally

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

## Run through GitHub Actions

A workflow is available:

```text
.github/workflows/discover-and-prepare.yml
```

Manual run path:

```text
Actions -> Discover and Prepare Applications -> Run workflow
```

Inputs:

```text
limit      maximum discovered leads
min_score  minimum score required to generate an application pack
```

Artifacts:

```text
discovered-job-leads-and-application-packs
```

The artifact contains discovery reports, normalized job descriptions, generated packs, and tracker CSV.

## Hiring manager / recruiter outreach

Generated packs include:

```text
09_recruiter_message.md
```

This is a draft only. You review, edit, and send manually.

## Hard rule

Job discovery is for preparation and prioritization. Submission and outreach stay human-controlled.
