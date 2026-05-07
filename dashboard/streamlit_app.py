from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.core.application_service import analyze_job_text, generate_pack_from_file
from app.core.application_tracker import render_tracker_summary

st.set_page_config(page_title="PortfolioFit Agent", layout="wide")
st.title("PortfolioFit Agent")
st.caption("Evidence-backed job application preparation. No auto-apply. Manual approval only.")

profile_path = st.sidebar.text_input("Profile YAML", "profile/master_profile.example.yaml")
portfolio_path = st.sidebar.text_input("Portfolio YAML", "profile/project_portfolio.example.yaml")
rules_path = st.sidebar.text_input("Rules YAML", "profile/resume_rules.example.yaml")

page = st.sidebar.radio("Workflow", ["Analyze Job", "Generate Pack", "Tracker"])

if page == "Analyze Job":
    st.header("Analyze Job Description")
    job_text = st.text_area("Paste job description", height=320)
    if st.button("Analyze", type="primary"):
        if len(job_text.strip()) < 20:
            st.error("Paste a real job description first.")
        else:
            result = analyze_job_text(job_text, profile_path, portfolio_path)
            fit = result["fit_score"]
            ats = result["ats_score"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Fit Score", f"{fit['final_score']}/100")
            c2.metric("Decision", fit["decision"])
            c3.metric("ATS Score", f"{ats['final_score']}/100")
            st.subheader("Best Positioning")
            st.write(fit["best_positioning"])
            st.subheader("Risks")
            st.write(fit.get("risks", []))
            st.subheader("Missing Keywords")
            st.write(ats.get("missing_keywords", []))
            st.subheader("Interview Prep")
            st.json(result["interview_prep"])

elif page == "Generate Pack":
    st.header("Generate Application Pack")
    uploaded = st.file_uploader("Upload job description .txt", type=["txt"])
    output_dir = st.text_input("Output directory", "outputs/applications/streamlit_pack")
    if st.button("Generate Pack", type="primary"):
        if uploaded is None:
            st.error("Upload a text job description first.")
        else:
            with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as tmp:
                tmp.write(uploaded.read())
                tmp_path = Path(tmp.name)
            result = generate_pack_from_file(tmp_path, profile_path, portfolio_path, rules_path, output_dir)
            st.success(f"Pack generated: {result['output_dir']}")
            st.json(result)

else:
    st.header("Application Tracker")
    tracker_path = st.text_input("Tracker CSV", "outputs/applications/application_tracker.csv")
    st.markdown(render_tracker_summary(tracker_path))
