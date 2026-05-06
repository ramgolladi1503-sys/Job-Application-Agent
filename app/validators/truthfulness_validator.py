from __future__ import annotations

from dataclasses import dataclass

from app.models import EvidenceMatch, ResumeRules


@dataclass(frozen=True)
class TruthfulnessFinding:
    claim: str
    status: str
    suggestion: str


def validate_claims(text: str, evidence_matches: list[EvidenceMatch], rules: ResumeRules) -> list[TruthfulnessFinding]:
    findings: list[TruthfulnessFinding] = []
    lower_text = text.lower()
    for forbidden in rules.forbidden_claims:
        if forbidden.lower() in lower_text:
            findings.append(TruthfulnessFinding(forbidden, "unsupported", "Remove or replace with evidence-backed wording."))
    if "expert" in lower_text:
        findings.append(TruthfulnessFinding("expert", "caution", "Avoid this word unless direct evidence exists."))
    for item in evidence_matches:
        if item.evidence_strength == "Missing" and item.requirement.lower() in lower_text:
            findings.append(TruthfulnessFinding(item.requirement, "unsupported", "This requirement has no matched evidence."))
    if not findings:
        findings.append(TruthfulnessFinding("Generated material", "passed", "No forbidden or obvious unsupported claims detected."))
    return findings


def render_truthfulness_report(findings: list[TruthfulnessFinding]) -> str:
    lines = ["# Truthfulness Report", ""]
    for item in findings:
        lines += [f"## {item.status.upper()}", f"- Claim: {item.claim}", f"- Suggestion: {item.suggestion}", ""]
    return "\n".join(lines)
