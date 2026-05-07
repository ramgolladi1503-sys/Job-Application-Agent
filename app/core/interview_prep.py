from __future__ import annotations

from typing import Any

from app.models import EvidenceMatch, FitScore, JobDescription


def generate_interview_prep(job: JobDescription, fit: FitScore, evidence: list[EvidenceMatch]) -> dict[str, Any]:
    strong = [item for item in evidence if item.evidence_strength == "Strong"][:6]
    missing = [item for item in evidence if item.evidence_strength == "Missing"][:6]
    return {
        "role": job.role_title,
        "company": job.company,
        "positioning": fit.best_positioning,
        "elevator_pitch": _elevator_pitch(job, fit, strong),
        "likely_questions": _likely_questions(job, strong, missing),
        "project_talking_points": _project_talking_points(strong),
        "risk_questions": _risk_questions(fit, missing),
        "closing_pitch": _closing_pitch(job, fit),
    }


def render_interview_prep(prep: dict[str, Any]) -> str:
    lines = ["# Interview Prep", "", f"Role: {prep['role']}", f"Company: {prep['company']}", f"Positioning: {prep['positioning']}", "", "## Elevator Pitch", "", prep["elevator_pitch"], "", "## Likely Questions", ""]
    lines += [f"- {item}" for item in prep.get("likely_questions", [])]
    lines += ["", "## Project Talking Points", ""]
    lines += [f"- {item}" for item in prep.get("project_talking_points", [])] or ["- Prepare one concrete project story."]
    lines += ["", "## Risk / Gap Questions", ""]
    lines += [f"- {item}" for item in prep.get("risk_questions", [])] or ["- No major gap questions detected."]
    lines += ["", "## Closing Pitch", "", prep["closing_pitch"], ""]
    return "\n".join(lines)


def _elevator_pitch(job: JobDescription, fit: FitScore, strong: list[EvidenceMatch]) -> str:
    evidence_text = strong[0].source_project if strong and strong[0].source_project else "my project portfolio"
    return f"I am positioning myself for this {job.role_title} role as {fit.best_positioning}. The strongest proof is {evidence_text}, which maps directly to the role requirements through practical, evidence-backed work rather than generic claims."


def _likely_questions(job: JobDescription, strong: list[EvidenceMatch], missing: list[EvidenceMatch]) -> list[str]:
    questions = [
        f"Why are you a fit for this {job.role_title} role?",
        "Walk me through the strongest project on your resume.",
        "How do you decide what to automate versus test manually?",
        "How do you handle ambiguous requirements or unclear acceptance criteria?",
    ]
    for item in strong[:4]:
        questions.append(f"Can you explain your experience with {item.requirement} using {item.source_project or 'your profile evidence'}?")
    for item in missing[:3]:
        questions.append(f"The JD mentions {item.requirement}. What is your current level with it?")
    if job.domain == "AI":
        questions += [
            "How would you test hallucination risk in an AI product?",
            "How would you validate model behavior across prompt variations?",
            "What safety gates would you add before allowing an AI agent to use tools?",
        ]
    if job.domain == "FinTech":
        questions += [
            "How would you validate a financial workflow before release?",
            "How do you test stale data, failed execution, and reconciliation issues?",
        ]
    return questions


def _project_talking_points(strong: list[EvidenceMatch]) -> list[str]:
    points = []
    for item in strong[:6]:
        source = item.source_project or "Profile evidence"
        points.append(f"{source}: {item.requirement} — {item.resume_bullet}")
    return points


def _risk_questions(fit: FitScore, missing: list[EvidenceMatch]) -> list[str]:
    questions = []
    for risk in fit.risks[:4]:
        questions.append(f"Prepare an honest answer for this risk: {risk}")
    for item in missing[:4]:
        questions.append(f"Do not fake {item.requirement}; explain adjacent experience and learning plan.")
    return questions


def _closing_pitch(job: JobDescription, fit: FitScore) -> str:
    return f"My value for this {job.role_title} role is {fit.best_positioning}: I can connect requirements to real validation work, explain risks clearly, and produce quality-focused delivery without overstating my background."
