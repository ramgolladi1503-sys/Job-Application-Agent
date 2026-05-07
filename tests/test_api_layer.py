from fastapi.testclient import TestClient

from app.api.main import app


def test_api_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_analyze_job_returns_fit_ats_and_interview_prep():
    client = TestClient(app)
    response = client.post(
        "/analyze-job",
        json={
            "job_text": "Company: Example AI Labs\nRole: GenAI QA Engineer\nMust have:\n- AI testing\n- LLM Evaluation\n- Prompt Testing\n- Model Validation\n",
            "profile_path": "profile/master_profile.example.yaml",
            "portfolio_path": "profile/project_portfolio.example.yaml",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "fit_score" in payload
    assert "ats_score" in payload
    assert "interview_prep" in payload
    assert payload["fit_score"]["final_score"] > 0
    assert payload["ats_score"]["final_score"] > 0
    assert payload["interview_prep"]["likely_questions"]
