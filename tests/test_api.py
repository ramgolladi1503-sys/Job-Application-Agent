from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_job_endpoint_returns_fit_ats_and_interview_prep() -> None:
    response = client.post(
        "/analyze-job",
        json={
            "job_text": "Company: Example AI Labs\nRole: GenAI QA Engineer\nMust have:\n- AI Testing\n- LLM Evaluation\n- Prompt Testing\n- Model Validation",
            "profile_path": "profile/master_profile.example.yaml",
            "portfolio_path": "profile/project_portfolio.example.yaml",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["fit_score"]["final_score"] > 0
    assert payload["ats_score"]["final_score"] > 0
    assert payload["interview_prep"]["likely_questions"]
    assert payload["evidence"]


def test_generate_pack_endpoint_creates_full_pack(tmp_path) -> None:
    output_dir = tmp_path / "api_pack"
    response = client.post(
        "/generate-pack",
        json={
            "job_file": "data/sample_jobs/genai_qa_job.txt",
            "profile_path": "profile/master_profile.example.yaml",
            "portfolio_path": "profile/project_portfolio.example.yaml",
            "rules_path": "profile/resume_rules.example.yaml",
            "output_dir": str(output_dir),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["fit_score"]["final_score"] >= 70
    assert (output_dir / "14_ats_score_report.md").exists()
    assert (output_dir / "15_interview_prep.md").exists()


def test_tracker_endpoint_handles_empty_tracker(tmp_path) -> None:
    tracker = tmp_path / "tracker.csv"
    response = client.get("/tracker", params={"tracker_path": str(tracker)})
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == []
    assert "No application records found" in payload["summary_markdown"]
