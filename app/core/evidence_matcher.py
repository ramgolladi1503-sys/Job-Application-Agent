from __future__ import annotations

from app.models import CandidateProfile, EvidenceMatch, JobDescription, Project


def map_evidence(job: JobDescription, profile: CandidateProfile, projects: list[Project]) -> list[EvidenceMatch]:
    skills = profile.all_skills()
    output: list[EvidenceMatch] = []
    for req in _unique(job.must_have_skills + job.nice_to_have_skills):
        project = _select_project(req, projects, job)
        if project is not None:
            output.append(
                EvidenceMatch(
                    requirement=req,
                    candidate_evidence=_specific_evidence(req, project),
                    resume_bullet=_project_bullet(req, project, job),
                    evidence_strength="Strong",
                    source_project=project.name,
                )
            )
        elif req.lower() in skills:
            output.append(
                EvidenceMatch(
                    requirement=req,
                    candidate_evidence=f"{req} appears in the skill inventory and should be supported with interview examples.",
                    resume_bullet=_skill_inventory_bullet(req, job),
                    evidence_strength="Medium",
                )
            )
        else:
            output.append(
                EvidenceMatch(
                    requirement=req,
                    candidate_evidence="No matching project entry found.",
                    resume_bullet="",
                    evidence_strength="Missing",
                    risk="Do not convert this requirement into a strong resume claim until evidence is added.",
                )
            )
    return output


def _select_project(req: str, projects: list[Project], job: JobDescription) -> Project | None:
    key = req.lower()
    job_text = " ".join([job.role_title, job.domain, *job.must_have_skills, *job.nice_to_have_skills]).lower()
    ranked: list[tuple[int, Project]] = []
    for project in projects:
        text = project.searchable_text()
        score = 0
        if key in text:
            score += 6
        if any(token in key for token in ["llm", "genai", "hallucination", "mcp", "model", "prompt", "policy", "security"]):
            if "mcp shield" in project.name.lower():
                score += 12
            if "portfoliofit" in project.name.lower() or "job application" in project.name.lower():
                score += 4
        if any(token in key for token in ["react", "api", "docker", "ci/cd", "selenium", ".net", "mvc", "regression"]):
            if "tradebot" in project.name.lower():
                score += 8
            if "automation" in project.name.lower():
                score += 6
            if "portfoliofit" in project.name.lower() or "job application" in project.name.lower():
                score += 3
        if "fintech" in job_text or "financial" in job_text or "trading" in job_text:
            if "tradebot" in project.name.lower():
                score += 7
        if "genai" in job_text or "llm" in job_text or "mcp" in job_text:
            if "mcp shield" in project.name.lower():
                score += 7
        if score:
            ranked.append((score, project))
    return sorted(ranked, key=lambda item: item[0], reverse=True)[0][1] if ranked else None


def _specific_evidence(req: str, project: Project) -> str:
    key = req.lower()
    targeted = [item for item in project.evidence if _evidence_matches(key, item.lower())]
    chosen = targeted[:2] if targeted else project.evidence[:2]
    return f"{project.name}: " + "; ".join(chosen)


def _evidence_matches(requirement: str, evidence: str) -> bool:
    groups = {
        "api": ["api", "json-rpc", "backend"],
        "docker": ["docker", "dockerized", "runtime"],
        "ci/cd": ["ci", "release", "dry-run", "github actions", "quality gate"],
        "regression": ["regression", "failure", "coverage"],
        "selenium": ["selenium", "automation"],
        "react": ["react", "dashboard", "frontend"],
        ".net": [".net", "application"],
        "llm": ["llm", "model", "response"],
        "genai": ["genai", "agent", "ai"],
        "hallucination": ["hallucination", "unsafe", "risk"],
        "prompt": ["prompt", "behavior"],
        "mcp": ["mcp", "tool-use", "gateway"],
        "security": ["security", "policy", "allowlist", "blocked"],
        "model": ["model", "response", "behavior"],
    }
    tokens = groups.get(requirement, [token for token in requirement.replace("/", " ").replace("-", " ").split() if len(token) > 2])
    return any(token in evidence for token in tokens)


def _project_bullet(req: str, project: Project, job: JobDescription) -> str:
    key = req.lower()
    name = project.name.lower()
    if "mcp shield" in name:
        return _mcp_shield_bullet(key)
    if "tradebot" in name:
        return _tradebot_bullet(key, job)
    if "portfoliofit" in name or "job application" in name:
        return _portfoliofit_bullet(key)
    if "automation" in name:
        return _automation_bullet(key)
    return f"Mapped {req} to {project.name} through evidence-backed validation work, focusing on repeatability, risk coverage, and reviewable outputs."


def _mcp_shield_bullet(req: str) -> str:
    if any(token in req for token in ["mcp", "tool", "agent"]):
        return "Validated MCP Shield tool-use flows by enforcing policy checks, approval pauses, JSON-RPC-safe blocked responses, and audit-friendly gateway behavior."
    if any(token in req for token in ["hallucination", "model", "llm", "genai"]):
        return "Designed GenAI QA checks for MCP Shield covering hallucination risk, model-response validation, unsafe tool-use attempts, and prompt-driven behavior changes."
    if any(token in req for token in ["prompt"]):
        return "Tested prompt-behavior risks by mapping user intent to allowed/blocked tool actions and verifying safe alternatives when requests were denied."
    if any(token in req for token in ["security", "policy", "risk"]):
        return "Built security-focused validation around MCP Shield policy enforcement, domain allowlisting, blocked command handling, and fail-closed approval behavior."
    if any(token in req for token in ["ci/cd", "github actions", "docker"]):
        return "Added CI-oriented validation for MCP Shield using security corpus checks, release dry-runs, package validation, and repeatable gateway test workflows."
    return "Used MCP Shield as concrete GenAI QA evidence for validating AI tool-use, policy enforcement, approval gates, auditability, and production-safe agent behavior."


def _tradebot_bullet(req: str, job: JobDescription) -> str:
    domain_prefix = "financial trading" if job.domain == "FinTech" else "complex runtime"
    if any(token in req for token in ["api", "backend"]):
        return f"Validated {domain_prefix} API/data workflows in Tradebot by checking market data consistency, execution readiness, stale-feed risks, and failure-path behavior."
    if any(token in req for token in ["regression", "functional", "test strategy"]):
        return "Designed Tradebot regression coverage around stale LTP/feed handling, option contract resolution, execution gates, dashboard defects, and recurring runtime failures."
    if any(token in req for token in ["docker", "ci/cd", "github actions", "kubernetes"]):
        return "Used Tradebot runtime scripts, Docker-style workflows, diagnostics, and CI-style checks to make validation repeatable across trading scenarios and release changes."
    if any(token in req for token in ["react", "frontend", "mvc", ".net"]):
        return "Applied full-stack QA thinking in Tradebot by validating dashboard/runtime behavior, backend readiness signals, data visibility, and defect symptoms across UI and execution layers."
    if any(token in req for token in ["selenium", "playwright", "automation"]):
        return "Applied automation-first QA discipline to Tradebot by converting recurring trading defects into repeatable validation checks and diagnostic workflows."
    return "Used Tradebot as fintech QA evidence by validating trading workflow reliability, execution-safety gates, runtime diagnostics, and regression-prone failure paths."


def _portfoliofit_bullet(req: str) -> str:
    if any(token in req for token in ["fastapi", "api"]):
        return "Built FastAPI endpoints in PortfolioFit Agent for job analysis, pack generation, GitHub ingestion, tracker reads, and status updates over the same tested core engine."
    if any(token in req for token in ["react", "frontend", "dashboard", "streamlit"]):
        return "Built a Streamlit dashboard for PortfolioFit Agent covering job analysis, pack generation, application tracking, and GitHub portfolio ingestion workflows."
    if any(token in req for token in ["ci/cd", "github actions", "docker"]):
        return "Hardened PortfolioFit Agent with GitHub Actions, Docker support, generated-pack workflows, linting, tests, and downloadable application-pack artifacts."
    if any(token in req for token in ["ats", "resume", "interview"]):
        return "Implemented ATS scoring, resume diffing, truthfulness checks, missing-skill reports, and interview-prep generation in PortfolioFit Agent."
    return "Built PortfolioFit Agent as an evidence-backed application-preparation system with CLI, FastAPI, Streamlit, GitHub ingestion, CI, tests, and manual approval gates."


def _automation_bullet(req: str) -> str:
    if any(token in req for token in ["selenium", "playwright", "appium", "automation"]):
        return "Built reusable automation validation practices across Selenium, Appium, Playwright/Pytest-style workflows, regression checks, and defect-focused test execution."
    if any(token in req for token in ["api", "postman"]):
        return "Created API validation practices covering request/response checks, data consistency, defect isolation, and regression-focused backend verification."
    return "Applied structured QA methods across functional testing, regression coverage, API validation, defect analysis, and risk-based release checks."


def _skill_inventory_bullet(req: str, job: JobDescription) -> str:
    role = job.role_title or "target role"
    return f"Applied {req} as part of QA/SDET validation for {role}, with emphasis on evidence-backed testing, defect analysis, and release-readiness checks."


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
