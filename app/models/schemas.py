from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    candidate: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, str] = Field(default_factory=dict)
    skills: dict[str, list[str]] = Field(default_factory=dict)
    experience: list[dict[str, Any]] = Field(default_factory=list)

    def all_skills(self) -> set[str]:
        values: set[str] = set()
        for skills in self.skills.values():
            values.update(skill.lower() for skill in skills)
        return values


class Project(BaseModel):
    name: str
    type: str = ""
    role: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    relevant_for: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    safe_resume_bullets: list[str] = Field(default_factory=list)

    def searchable_text(self) -> str:
        parts = [self.name, self.type, self.role]
        parts += self.tech_stack + self.relevant_for + self.evidence + self.safe_resume_bullets
        return " ".join(parts).lower()


class ResumeRules(BaseModel):
    rules: dict[str, Any] = Field(default_factory=dict)

    @property
    def forbidden_claims(self) -> list[str]:
        return list(self.rules.get("forbidden_claims", []))


class JobDescription(BaseModel):
    role_title: str = "Unknown Role"
    company: str = "Unknown Company"
    location: str = "Unknown"
    seniority: str = "Unknown"
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    domain: str = "General"
    keywords: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ScoreBreakdown(BaseModel):
    must_have_skill_match: int
    project_evidence_match: int
    domain_relevance: int
    seniority_match: int
    tooling_platform_match: int
    resume_positioning_strength: int
    risk_check: int


class FitScore(BaseModel):
    final_score: int
    decision: str
    confidence: str
    best_positioning: str
    explanation: str
    risks: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    breakdown: ScoreBreakdown


class EvidenceMatch(BaseModel):
    requirement: str
    candidate_evidence: str
    resume_bullet: str
    evidence_strength: str
    source_project: str | None = None
    risk: str | None = None
