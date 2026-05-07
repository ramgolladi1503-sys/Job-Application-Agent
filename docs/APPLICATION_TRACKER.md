# Application Tracker

PortfolioFit Agent writes a CSV tracker whenever an application pack is generated.

Default path:

```text
outputs/applications/application_tracker.csv
```

This file is ignored by Git because real application data may contain private career information.

## View tracker summary

```bash
portfoliofit tracker-summary
```

## Update application status

```bash
portfoliofit tracker-update "Example AI Labs" "GenAI QA Engineer" submitted \
  --follow-up-date 2026-05-14 \
  --notes "Submitted manually"
```

Matching is case-insensitive and partial for company and role title.

## Export tracker

```bash
portfoliofit tracker-export exports/application_tracker.csv
```

## Status suggestions

Use simple statuses:

```text
prepared
submitted
followed_up
interviewing
rejected
offer
withdrawn
```

## Tracker columns

```text
date_created
company
role_title
fit_score
decision
status
pack_path
follow_up_date
notes
```

## Boundary

The tracker records preparation and manual submission status. It does not submit applications.
