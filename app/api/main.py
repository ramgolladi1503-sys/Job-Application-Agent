from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.application_service import analyze_job_text, generate_pack_from_file
from app.core.application_tracker import read_tracker, render_tracker_summary, update_application_status
from app.core.github_portfolio import write_remote_repo_summary

app = FastAPI(
    title="PortfolioFit Agent API",
    version="0.2.0",
    description="Evidence-backed job application preparation API with fit scoring, ATS scoring, and interview prep.",
)


class AnalyzeRequest(BaseModel):
    job_text: str = Field(..., min_length=20)
    profile_path: str = "profile/master_profile.example.yaml"
    portfolio_path: str = "profile/project_portfolio.example.yaml"


class GeneratePackRequest(BaseModel):
    job_file: str
    profile_path: str = "profile/master_profile.example.yaml"
    portfolio_path: str = "profile/project_portfolio.example.yaml"
    rules_path: str = "profile/resume_rules.example.yaml"
    output_dir: str = "outputs/applications/api_pack"


class GitHubIngestRequest(BaseModel):
    owner: str
    repo: str
    ref: str = "main"
    output_path: str = "profile/github_portfolio.generated.yaml"


class TrackerUpdateRequest(BaseModel):
    company: str
    role_title: str
    status: str
    tracker_path: str = "outputs/applications/application_tracker.csv"
    follow_up_date: str = ""
    notes: str = ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze-job")
def analyze_job(request: AnalyzeRequest) -> dict[str, Any]:
    try:
        return analyze_job_text(request.job_text, request.profile_path, request.portfolio_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/generate-pack")
def generate_pack(request: GeneratePackRequest) -> dict[str, Any]:
    try:
        return generate_pack_from_file(
            request.job_file,
            request.profile_path,
            request.portfolio_path,
            request.rules_path,
            request.output_dir,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ingest/github")
def ingest_github(request: GitHubIngestRequest) -> dict[str, str]:
    try:
        write_remote_repo_summary(request.owner, request.repo, request.output_path, ref=request.ref)
        return {"status": "written", "output_path": request.output_path}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/tracker")
def tracker(tracker_path: str = "outputs/applications/application_tracker.csv") -> dict[str, Any]:
    path = Path(tracker_path)
    return {"tracker_path": str(path), "rows": read_tracker(path), "summary_markdown": render_tracker_summary(path)}


@app.post("/tracker/update")
def tracker_update(request: TrackerUpdateRequest) -> dict[str, Any]:
    updated = update_application_status(
        request.tracker_path,
        request.company,
        request.role_title,
        request.status,
        request.follow_up_date,
        request.notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="No matching tracker rows found")
    return {"updated": updated}
