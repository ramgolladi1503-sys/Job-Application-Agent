# ATS Scoring and Interview Prep

PortfolioFit Agent now generates two extra reports in every application pack:

```text
14_ats_score_report.md
15_interview_prep.md
```

## ATS score report

The ATS report is a practical resume quality check. It is not a guarantee that an ATS system will rank the resume highly.

It scores:

```text
Keyword match:      45 points
Structure:          20 points
Evidence strength:  20 points
Clarity:            15 points
Risk penalty:       deducted
```

The report shows:

```text
Final score
Grade
Matched keywords
Missing keywords
Recommendations
```

CLI:

```bash
portfoliofit ats-score data/sample_jobs/genai_qa_job.txt
```

## Interview prep report

The interview prep report uses the job description, fit score, and evidence map to generate:

```text
Elevator pitch
Likely questions
Project talking points
Risk/gap questions
Closing pitch
```

CLI:

```bash
portfoliofit interview-prep data/sample_jobs/genai_qa_job.txt
```

## Hard rule

If a skill is missing, do not fake it. Use the gap question section to prepare an honest answer with adjacent experience and a learning plan.
