from pathlib import Path

from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import write_application_pack
from app.core.jd_parser import parse_job_file
from app.core.profile_loader import load_profile, load_projects, load_rules
from app.validators.truthfulness_validator import validate_claims

ROOT = Path(__file__).resolve().parents[1]


def test_genai_qa_job_highlights_mcp_shield(tmp_path):
    job = parse_job_file(ROOT / "data/sample_jobs/genai_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    rules = load_rules(ROOT / "profile/resume_rules.example.yaml")
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    files = write_application_pack(tmp_path / "pack", job, profile, projects, rules, fit, evidence)
    resume = (tmp_path / "pack/05_tailored_resume.md").read_text(encoding="utf-8")
    assert fit.final_score >= 70
    assert "MCP Shield" in resume
    assert "hallucination" in resume.lower()
    assert len(files) == 11


def test_dotnet_react_job_scores_as_apply():
    job = parse_job_file(ROOT / "data/sample_jobs/dotnet_react_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    fit = score_job(job, profile, projects)
    assert fit.final_score >= 70
    assert "SDET" in fit.best_positioning


def test_unsupported_kubernetes_claim_is_flagged():
    rules = load_rules(ROOT / "profile/resume_rules.example.yaml")
    findings = validate_claims("Owned production Kubernetes infrastructure", evidence_matches=[], rules=rules)
    assert any(finding.status == "unsupported" for finding in findings)


def test_pack_contains_manual_approval_boundary(tmp_path):
    job = parse_job_file(ROOT / "data/sample_jobs/dotnet_react_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    rules = load_rules(ROOT / "profile/resume_rules.example.yaml")
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    write_application_pack(tmp_path / "pack", job, profile, projects, rules, fit, evidence)
    notes = (tmp_path / "pack/10_application_notes.md").read_text(encoding="utf-8")
    assert "Manual Approval Checklist" in notes
    assert "No auto-apply action has been taken" in notes
