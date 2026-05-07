from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.core.application_service import analyze_job_text, generate_pack_from_file
from app.core.application_tracker import read_tracker, render_tracker_summary, update_application_status
from app.core.github_portfolio import write_local_repo_summary, write_remote_repo_summary

st.set_page_config(page_title="PortfolioFit Agent", layout="wide")
st.title("PortfolioFit Agent")
st.caption("Evidence-backed job application preparation. No auto-apply. Human approval required.")

DEFAULT_PROFILE = "profile/master_profile.example.yaml"
DEFAULT_PORTFOLIO = "profile/project_portfolio.example.yaml"
DEFAULT_RULES = "profile/resume_rules.example.yaml"
DEFAULT_TRACKER = "outputs/applications/application_tracker.csv"

with st.sidebar:
    st.header("Configuration")
    profile_path = st.text_input("Profile YAML", DEFAULT_PROFILE)
    portfolio_path = st.text_input("Portfolio YAML", DEFAULT_PORTFOLIO)
    rules_path = st.text_input("Resume rules YAML", DEFAULT_RULES)
    tracker_path = st.text_input("Tracker CSV", DEFAULT_TRACKER)

tab_analyze, tab_generate, tab_tracker, tab_github = st.tabs(["Analyze Job", "Generate Pack", "Tracker", "GitHub Ingestion"])

with tab_analyze:
    st.subheader("Job Fit Analysis")
    job_text = st.text_area("Paste job description", height=320)
    if st.button("Analyze job", type="primary"):
        if len(job_text.strip()) < 20:
            st.error("Paste a real job description first.")
        else:
            result = analyze_job_text(job_text, profile_path, portfolio_path)
            col1, col2, col3 = st.columns(3)
            col1.metric("Fit Score", result["fit_score"]["final_score"])
            col2.metric("Decision", result["fit_score"]["decision"])
            col3.metric("ATS Score", result["ats_score"]["final_score"])
            st.markdown("### Best Positioning")
            st.write(result["fit_score"]["best_positioning"])
            st.markdown("### Evidence Map")
            st.dataframe(result["evidence"], use_container_width=True)
            st.markdown("### ATS Recommendations")
            for item in result["ats_score"].get("recommendations", []):
                st.write(f"- {item}")
            st.markdown("### Interview Questions")
            for item in result["interview_prep"].get("likely_questions", []):
                st.write(f"- {item}")

with tab_generate:
    st.subheader("Generate Application Pack")
    job_file = st.text_input("Job description file", "data/sample_jobs/genai_qa_job.txt")
    output_dir = st.text_input("Output directory", "outputs/applications/streamlit_pack")
    if st.button("Generate pack", type="primary"):
        result = generate_pack_from_file(job_file, profile_path, portfolio_path, rules_path, output_dir)
        st.success(f"Pack generated: {result['output_dir']}")
        st.json(result)

with tab_tracker:
    st.subheader("Application Tracker")
    rows = read_tracker(tracker_path)
    st.markdown(render_tracker_summary(tracker_path))
    if rows:
        st.dataframe(rows, use_container_width=True)
    st.markdown("### Update Status")
    company = st.text_input("Company match")
    role_title = st.text_input("Role match")
    status = st.selectbox("Status", ["prepared", "submitted", "followed_up", "interviewing", "rejected", "offer", "withdrawn"])
    follow_up = st.text_input("Follow-up date")
    notes = st.text_input("Notes")
    if st.button("Update tracker"):
        updated = update_application_status(tracker_path, company, role_title, status, follow_up, notes)
        if updated:
            st.success(f"Updated {updated} row(s).")
        else:
            st.error("No matching rows found.")

with tab_github:
    st.subheader("GitHub Portfolio Ingestion")
    mode = st.radio("Mode", ["Remote public/private with token", "Local folder"])
    output = st.text_input("Output portfolio YAML", "profile/github_portfolio.generated.yaml")
    if mode == "Remote public/private with token":
        st.info("Set GITHUB_TOKEN in your environment for private repos or higher rate limits.")
        owner = st.text_input("Owner", "ramgolladi1503-sys")
        repo = st.text_input("Repo", "Job-Application-Agent")
        ref = st.text_input("Branch/ref", "main")
        if st.button("Fetch GitHub repo"):
            write_remote_repo_summary(owner, repo, output, ref=ref)
            st.success(f"Portfolio YAML written: {output}")
    else:
        local_path = st.text_input("Local repo path", ".")
        if st.button("Scan local repo"):
            write_local_repo_summary(Path(local_path), output)
            st.success(f"Portfolio YAML written: {output}")
