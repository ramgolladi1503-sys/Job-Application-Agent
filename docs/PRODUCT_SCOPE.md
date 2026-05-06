# Product Scope

## Mission

PortfolioFit Agent is an evidence-based job application preparation system. It helps a candidate convert real profile, work-history, GitHub, and project evidence into targeted application packs.

## Core workflow

```text
Candidate profile
+ Project portfolio
+ Job description
        ↓
Parse job requirements
        ↓
Score candidate fit
        ↓
Map real evidence to requirements
        ↓
Generate tailored resume
        ↓
Generate cover letter
        ↓
Generate recruiter message
        ↓
Generate application pack
        ↓
Wait for manual approval
```

## In scope

- Candidate profile loading from YAML
- Project portfolio evidence loading from YAML
- Job description parsing
- Fit scoring with explainable breakdown
- Evidence-to-requirement mapping
- Tailored resume generation
- Cover letter generation
- Recruiter message generation
- Missing-skills report
- Resume diff report
- Truthfulness validation
- Application tracker CSV
- GitHub repo file-list ingestion
- Markdown, DOCX, and PDF resume exports
- CLI-first workflow
- Docker and CI support

## Out of scope

- Auto-submit to job portals
- LinkedIn auto-apply
- Captcha bypass
- Mass spam applications
- Fake claim generation
- Unsupported skill injection
- Browser automation for applications

## MVP definition

The MVP is complete when a user can run one command against a raw job description and receive a complete application pack that is truthful, targeted, reviewable, and manually approvable.

## Elite-level bar

This project should be judged by evidence quality, not UI flash. A good output explains why a role fits, what proof supports the resume, what gaps exist, and what the candidate should avoid exaggerating.
