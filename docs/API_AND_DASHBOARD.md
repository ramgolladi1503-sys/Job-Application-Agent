# API and Dashboard

PortfolioFit Agent now exposes the same engine through CLI, FastAPI, and Streamlit.

## FastAPI

Run locally:

```bash
uvicorn app.api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## API endpoints

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Analyze job text

```bash
curl -X POST http://127.0.0.1:8000/analyze-job \
  -H "Content-Type: application/json" \
  -d '{
    "job_text": "Company: Example AI Labs\nRole: GenAI QA Engineer\nMust have:\n- AI testing\n- LLM Evaluation\n- Prompt Testing",
    "profile_path": "profile/master_profile.example.yaml",
    "portfolio_path": "profile/project_portfolio.example.yaml"
  }'
```

Returns:

```text
job
fit_score
evidence
ats_score
interview_prep
```

### Generate application pack

```bash
curl -X POST http://127.0.0.1:8000/generate-pack \
  -H "Content-Type: application/json" \
  -d '{
    "job_file": "data/sample_jobs/genai_qa_job.txt",
    "output_dir": "outputs/applications/api_pack"
  }'
```

### Ingest GitHub repository

```bash
curl -X POST http://127.0.0.1:8000/ingest/github \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "ramgolladi1503-sys",
    "repo": "Job-Application-Agent",
    "ref": "main",
    "output_path": "profile/github_portfolio.generated.yaml"
  }'
```

For private repositories or higher rate limits, set:

```bash
export GITHUB_TOKEN=your_token_here
```

### Tracker

```bash
curl http://127.0.0.1:8000/tracker
```

Update tracker:

```bash
curl -X POST http://127.0.0.1:8000/tracker/update \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Example AI Labs",
    "role_title": "GenAI QA Engineer",
    "status": "submitted",
    "follow_up_date": "2026-05-14",
    "notes": "Submitted manually"
  }'
```

## Streamlit dashboard

Run locally:

```bash
streamlit run app/dashboard/streamlit_app.py
```

Dashboard tabs:

```text
Analyze Job
Generate Pack
Tracker
GitHub Ingestion
```

## Boundary

The API and dashboard prepare materials only. They do not auto-submit applications.
