from pathlib import Path

from app.core.application_tracker import append_application_record, export_tracker, read_tracker, update_application_status
from app.core.ats_scorer import score_resume_ats
from app.core.evidence_matcher import map_evidence
from app.core.fit_scorer import score_job
from app.core.generators import render_resume, write_application_pack
from app.core.github_portfolio import scan_local_repo, summarize_repo_tree, write_portfolio_summary
from app.core.interview_prep import generate_interview_prep
from app.core.job_discovery import discover_jobs_from_config, load_discovered_jobs
from app.core.missing_skills import analyze_missing_skills
from app.core.profile_loader import load_profile, load_projects, load_rules
from app.core.jd_parser import parse_job_description, parse_job_file
from app.core.resume_ingestion import ingest_resume_text
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
    assert len(files) == 15
    assert (tmp_path / "pack/12_missing_skills_report.md").exists()
    assert (tmp_path / "pack/13_resume_diff.md").exists()
    assert (tmp_path / "pack/14_ats_score_report.md").exists()
    assert (tmp_path / "pack/15_interview_prep.md").exists()
    assert (tmp_path / "application_tracker.csv").exists()


def test_job_discovery_extracts_and_normalizes_sample_jobs(tmp_path):
    config = tmp_path / "sources.yaml"
    sample_html = ROOT / "data/sample_jobs/job_discovery_sample.html"
    config.write_text(
        "sources:\n"
        "  - name: sample\n"
        "    type: file\n"
        "    enabled: true\n"
        f"    path: {sample_html.as_posix()}\n",
        encoding="utf-8",
    )
    leads = discover_jobs_from_config(config, tmp_path / "discovery", limit=10)
    assert leads
    assert any("GenAI QA" in lead.title for lead in leads)
    assert (tmp_path / "discovery/jobs.json").exists()
    assert (tmp_path / "discovery/discovery_report.md").exists()
    loaded = load_discovered_jobs(tmp_path / "discovery/jobs.json")
    assert loaded[0].to_job_description_text().startswith("Company:")


def test_saved_alert_glob_discovery(tmp_path):
    alerts = tmp_path / "alerts"
    alerts.mkdir()
    (alerts / "one.html").write_text(
        "<h2>AI Testing Engineer</h2><p>Company: Guardrail AI</p><p>Location: Remote</p><p>Need LLM Evaluation, Prompt Testing, AI Testing, API Testing, and risk controls.</p>",
        encoding="utf-8",
    )
    (alerts / "two.txt").write_text(
        "Role: QA Automation Engineer\nCompany: FinQA Labs\nLocation: Hyderabad\nMust have Selenium, API Testing, Regression Testing, Docker, and CI/CD validation.",
        encoding="utf-8",
    )
    config = tmp_path / "sources.yaml"
    config.write_text(
        "sources:\n"
        "  - name: html_alerts\n"
        "    type: glob\n"
        "    enabled: true\n"
        f"    pattern: {alerts.as_posix()}/*.html\n"
        "  - name: text_alerts\n"
        "    type: glob\n"
        "    enabled: true\n"
        f"    pattern: {alerts.as_posix()}/*.txt\n",
        encoding="utf-8",
    )
    leads = discover_jobs_from_config(config, tmp_path / "discovery", limit=10)
    titles = " ".join(lead.title for lead in leads)
    assert "AI Testing Engineer" in titles
    assert "QA Automation Engineer" in titles


def test_generated_resume_uses_requirement_specific_bullets():
    job = parse_job_file(ROOT / "data/sample_jobs/genai_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.yaml")
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    resume = render_resume(job, profile, projects, fit, evidence)
    bullets = [item.resume_bullet for item in evidence if item.resume_bullet]
    assert len(set(bullets)) >= 4
    assert "JSON-RPC" in resume or "approval" in resume.lower()
    assert "MCP Shield" in resume
    assert "The strongest proof is" not in resume


def test_dotnet_react_job_scores_as_apply():
    job = parse_job_file(ROOT / "data/sample_jobs/dotnet_react_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    fit = score_job(job, profile, projects)
    assert fit.final_score >= 70
    assert "SDET" in fit.best_positioning


def test_low_fit_job_scores_lower_than_target_jobs():
    low_fit = parse_job_description(
        """
        Company: Research Lab
        Role: Senior ML Research Scientist
        Must have:
        - PhD
        - Advanced machine learning model training
        - Research publications
        - Distributed training infrastructure
        """
    )
    target = parse_job_file(ROOT / "data/sample_jobs/genai_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    assert score_job(low_fit, profile, projects).final_score < score_job(target, profile, projects).final_score


def test_ats_scoring_and_interview_prep_outputs():
    job = parse_job_file(ROOT / "data/sample_jobs/genai_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    fit = score_job(job, profile, projects)
    evidence = map_evidence(job, profile, projects)
    resume = render_resume(job, profile, projects, fit, evidence)
    ats = score_resume_ats(resume, job, evidence)
    prep = generate_interview_prep(job, fit, evidence)
    assert ats["final_score"] > 0
    assert "matched_keywords" in ats
    assert prep["likely_questions"]
    assert "MCP" in " ".join(prep["elevator_pitch"].split()) or "AI" in prep["positioning"]


def test_missing_skills_report_identifies_gaps():
    job = parse_job_description(
        """
        Role: QA Engineer
        Must have:
        - Cypress
        - Selenium
        - Azure DevOps
        """
    )
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    analysis = analyze_missing_skills(job, profile, projects)
    assert "Selenium" in analysis["strong_matches"]
    assert "Cypress" in analysis["missing_or_weak"]


def test_github_repo_ingestion_detects_project_evidence():
    summary = summarize_repo_tree(
        "sample-ai-testing-repo",
        ["README.md", "app/main.py", "tests/test_app.py", ".github/workflows/ci.yml", "Dockerfile"],
        "MCP LLM prompt validation and hallucination testing",
    )
    assert "Docker" in summary["tech_stack"]
    assert "GitHub Actions" in summary["tech_stack"]
    assert "AI Testing" in summary["tech_stack"]
    assert "GenAI QA" in summary["relevant_for"]
    assert summary["metadata"]["file_count"] == 5
    assert summary["metadata"]["has_readme"] is True


def test_github_portfolio_yaml_writer_outputs_loadable_project_schema(tmp_path):
    output = tmp_path / "portfolio.yaml"
    write_portfolio_summary(
        "job-agent",
        ["README.md", "README.md", "app/main.py", "tests/test_app.py", ".github/workflows/ci.yml"],
        output,
        "LLM prompt validation",
    )
    projects = load_projects(output)
    assert len(projects) == 1
    assert projects[0].name == "job-agent"
    assert "GitHub Actions" in projects[0].tech_stack
    assert "SDET" in projects[0].relevant_for


def test_local_repo_scan_ignores_noise_and_reads_readme(tmp_path):
    repo = tmp_path / "sample_repo"
    (repo / "app").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("MCP LLM prompt validation", encoding="utf-8")
    (repo / "app/main.py").write_text("print('hello')", encoding="utf-8")
    (repo / "tests/test_main.py").write_text("def test_ok(): assert True", encoding="utf-8")
    (repo / ".git/config").write_text("ignored", encoding="utf-8")
    repo_name, paths, readme = scan_local_repo(repo)
    assert repo_name == "sample_repo"
    assert "app/main.py" in paths
    assert ".git/config" not in paths
    assert "MCP" in readme


def test_resume_ingestion_builds_profile_yaml_shape():
    profile = ingest_resume_text(
        """
        Professional Summary
        QA Automation Engineer with Selenium, API Testing, React, .NET Core, Docker, GenAI, LLM Evaluation, and Prompt Testing experience.

        Experience
        - Designed automation tests for API and regression workflows across release cycles.
        - Validated LLM prompt behavior and model response risks for AI workflows.
        """,
        candidate_name="Ram Golladi",
    )
    assert profile["candidate"]["name"] == "Ram Golladi"
    assert "GenAI QA Engineer" in profile["candidate"]["target_roles"]
    assert "automation" in profile["skills"]
    assert "ai_testing" in profile["skills"]


def test_application_tracker_update_and_export(tmp_path):
    tracker = tmp_path / "tracker.csv"
    exported = tmp_path / "exports/tracker_copy.csv"
    job = parse_job_file(ROOT / "data/sample_jobs/dotnet_react_qa_job.txt")
    profile = load_profile(ROOT / "profile/master_profile.example.yaml")
    projects = load_projects(ROOT / "profile/project_portfolio.example.yaml")
    fit = score_job(job, profile, projects)
    append_application_record(tracker, job, fit, tmp_path / "pack")
    updated = update_application_status(tracker, "Example FinTech", ".NET + React", "submitted", "2026-05-14", "Submitted manually")
    rows = read_tracker(tracker)
    export_tracker(tracker, exported)
    assert updated == 1
    assert rows[0]["status"] == "submitted"
    assert exported.exists()


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
    assert "ATS report reviewed" in notes
    assert "Interview prep reviewed" in notes
    assert "No auto-apply action has been taken" in notes
