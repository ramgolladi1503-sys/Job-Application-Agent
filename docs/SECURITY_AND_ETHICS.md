# Security and Ethics

## Boundary

PortfolioFit Agent prepares application material. It does not submit applications.

The user must manually review and submit every application.

## Explicitly disallowed behavior

- LinkedIn auto-apply
- Workday or job-portal auto-submit
- Captcha bypass
- Credential storage for job portals
- Mass application spam
- Fake skill or fake employment generation
- Unsupported resume claims
- Misrepresentation of seniority

## Why this matters

Automated job submission creates low-quality spam and can damage a candidate's reputation. This project is designed to improve application quality, not bypass human judgment.

## Truthfulness model

Every strong claim should be backed by one of these sources:

1. Candidate profile
2. Work history
3. Project portfolio
4. GitHub repository evidence
5. User-approved manual evidence

If evidence is missing, the system should mark the skill as missing or weak rather than inventing experience.

## Data safety

Generated application packs may contain sensitive career information. The `outputs/applications/` folder is ignored by Git by default.

Do not commit real resumes, real contact details, private job descriptions, or employer correspondence unless intentionally sanitized.

## Safe wording examples

Good:

```text
Worked with Dockerized environments for validation and repeatable test execution.
```

Risky without proof:

```text
Owned production Kubernetes infrastructure.
```

Good:

```text
Designed MCP Shield as an AI tool-use validation and risk-control project.
```

Risky without proof:

```text
Expert AI safety researcher with production LLM ownership.
```

## Approval gate

Every generated pack must include a manual approval checklist:

- Resume reviewed
- Cover letter reviewed
- Recruiter message reviewed
- Fit score accepted
- User manually submitted application
