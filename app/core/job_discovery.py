from __future__ import annotations

import glob
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class JobLead:
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str
    raw_text: str

    def to_job_description_text(self) -> str:
        return "\n".join(
            [
                f"Company: {self.company or 'Unknown Company'}",
                f"Role: {self.title or 'Unknown Role'}",
                f"Location: {self.location or 'Unknown'}",
                "",
                self.description or self.raw_text,
                "",
                f"Source: {self.source}",
                f"URL: {self.url}",
            ]
        ).strip()


def discover_jobs_from_config(config_path: str | Path, output_dir: str | Path, limit: int = 25) -> list[JobLead]:
    config = _read_yaml(config_path)
    leads: list[JobLead] = []
    for source in _expand_sources(config.get("sources", [])):
        if not source.get("enabled", True):
            continue
        source_type = source.get("type", "url")
        if source_type not in {"url", "search_url", "file"}:
            continue
        try:
            text = _load_source_text(source)
        except Exception as exc:
            leads.append(
                JobLead(
                    source=source.get("name", "unknown"),
                    title="SOURCE_FETCH_FAILED",
                    company="",
                    location="",
                    url=source.get("url", ""),
                    description=str(exc),
                    raw_text="",
                )
            )
            continue
        leads.extend(_extract_job_leads(source.get("name", "unknown"), source.get("url", ""), text))
        if len([lead for lead in leads if lead.title != "SOURCE_FETCH_FAILED"]) >= limit:
            break
    clean = _dedupe_leads([lead for lead in leads if lead.title != "SOURCE_FETCH_FAILED"])[:limit]
    failures = [lead for lead in leads if lead.title == "SOURCE_FETCH_FAILED"]
    _write_discovery_outputs(clean, failures, output_dir)
    return clean


def write_job_lead_files(leads: list[JobLead], output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, lead in enumerate(leads, start=1):
        safe_name = _slugify(f"{index:03d}_{lead.company}_{lead.title}")
        path = out / f"{safe_name}.txt"
        path.write_text(lead.to_job_description_text(), encoding="utf-8")
        paths.append(path)
    return paths


def render_discovery_report(leads: list[JobLead], failures: list[JobLead] | None = None) -> str:
    failures = failures or []
    lines = ["# Job Discovery Report", "", f"Valid leads discovered: {len(leads)}", f"Source failures: {len(failures)}", ""]
    if leads:
        lines += ["## Leads", ""]
        for lead in leads:
            lines += [f"### {lead.title}", f"- Company: {lead.company or 'Unknown'}", f"- Location: {lead.location or 'Unknown'}", f"- Source: {lead.source}", f"- URL: {lead.url or 'N/A'}", ""]
    if failures:
        lines += ["## Source Failures", ""]
        for failure in failures:
            lines += [f"- {failure.source}: {failure.description}"]
    lines += ["", "## Boundary", "", "This agent prepares application material only. It does not auto-apply or auto-message hiring managers.", ""]
    return "\n".join(lines)


def load_discovered_jobs(discovered_json: str | Path) -> list[JobLead]:
    data = json.loads(Path(discovered_json).read_text(encoding="utf-8"))
    return [JobLead(**item) for item in data.get("jobs", [])]


def _expand_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for source in sources:
        if not source.get("enabled", True):
            expanded.append(source)
            continue
        source_type = source.get("type", "url")
        if source_type not in {"glob", "directory"}:
            expanded.append(source)
            continue
        pattern = source.get("pattern") or source.get("path")
        if source_type == "directory":
            folder = Path(source.get("path", ""))
            patterns = [folder / "*.html", folder / "*.txt", folder / "*.eml"]
            matches = [match for p in patterns for match in glob.glob(str(p))]
        else:
            matches = glob.glob(str(pattern))
        for path in sorted(matches):
            expanded.append({"name": f"{source.get('name', 'saved_alert')}:{Path(path).name}", "type": "file", "enabled": True, "path": path})
    return expanded


def _read_yaml(path: str | Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Job discovery config must be a YAML mapping.")
    return data


def _load_source_text(source: dict[str, Any]) -> str:
    if source.get("type") == "file":
        path = Path(source["path"])
        if path.suffix.lower() == ".eml":
            return _read_eml_text(path)
        return path.read_text(encoding="utf-8", errors="replace")
    url = source.get("url", "")
    if url.startswith("file://"):
        path = Path(urllib.parse.urlparse(url).path)
        if path.suffix.lower() == ".eml":
            return _read_eml_text(path)
        return path.read_text(encoding="utf-8", errors="replace")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 PortfolioFit-Agent/0.2 application-prep-only",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=int(source.get("timeout_seconds", 20))) as response:
        return response.read().decode("utf-8", errors="replace")


def _read_eml_text(path: Path) -> str:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    parts = []
    if message["subject"]:
        parts.append(f"Subject: {message['subject']}")
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type in {"text/plain", "text/html"}:
                payload = part.get_content()
                if isinstance(payload, str):
                    parts.append(payload)
    else:
        payload = message.get_content()
        if isinstance(payload, str):
            parts.append(payload)
    return "\n".join(parts)


def _extract_job_leads(source_name: str, source_url: str, text: str) -> list[JobLead]:
    json_ld = _extract_json_ld_jobs(source_name, source_url, text)
    if json_ld:
        return json_ld
    blocks = _split_possible_job_blocks(text)
    leads = [_lead_from_block(source_name, source_url, block) for block in blocks]
    return [lead for lead in leads if lead.title and len(lead.description) > 40]


def _extract_json_ld_jobs(source_name: str, source_url: str, html: str) -> list[JobLead]:
    leads = []
    scripts = re.findall(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", html, re.I | re.S)
    for script in scripts:
        try:
            payload = json.loads(_html_unescape(script.strip()))
        except json.JSONDecodeError:
            continue
        for item in _flatten_json_ld(payload):
            if item.get("@type") != "JobPosting":
                continue
            org = item.get("hiringOrganization") or {}
            location = item.get("jobLocation") or {}
            address = location.get("address", {}) if isinstance(location, dict) else {}
            lead_url = item.get("url") or source_url
            leads.append(
                JobLead(
                    source=source_name,
                    title=_clean_text(str(item.get("title", ""))),
                    company=_clean_text(str(org.get("name", "") if isinstance(org, dict) else "")),
                    location=_clean_text(" ".join(str(address.get(key, "")) for key in ["addressLocality", "addressRegion", "addressCountry"])),
                    url=str(lead_url),
                    description=_clean_text(str(item.get("description", ""))),
                    raw_text=_clean_text(json.dumps(item)[:4000]),
                )
            )
    return leads


def _flatten_json_ld(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        graph = payload.get("@graph")
        if isinstance(graph, list):
            return [item for item in graph if isinstance(item, dict)]
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _split_possible_job_blocks(text: str) -> list[str]:
    cleaned = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    cleaned = re.sub(r"</(p|div|li|section|article|tr|h\d)>", "\n", cleaned, flags=re.I)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = _html_unescape(cleaned)
    chunks = re.split(r"\n\s*\n|(?=\b(?:Role|Job Title|Title):)", cleaned)
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 80]


def _lead_from_block(source_name: str, source_url: str, block: str) -> JobLead:
    title = _field(block, ["Role", "Job Title", "Title"]) or _guess_title(block)
    company = _field(block, ["Company", "Organization"]) or "Unknown Company"
    location = _field(block, ["Location"]) or "Unknown"
    url = _first_url(block) or source_url
    return JobLead(source=source_name, title=title, company=company, location=location, url=url, description=_clean_text(block), raw_text=block[:4000])


def _field(text: str, names: list[str]) -> str:
    for name in names:
        match = re.search(rf"\b{re.escape(name)}\s*:\s*(.+)", text, re.I)
        if match:
            return _clean_text(match.group(1).splitlines()[0])
    return ""


def _guess_title(text: str) -> str:
    for line in text.splitlines():
        cleaned = _clean_text(line)
        if cleaned.lower().startswith(("company:", "location:", "apply:", "url:", "source:", "subject:")):
            continue
        if 5 <= len(cleaned) <= 90 and any(token in cleaned.lower() for token in ["qa", "sdet", "test", "automation", "genai", "ai", "engineer", "developer"]):
            return cleaned
    return ""


def _first_url(text: str) -> str:
    match = re.search(r"https?://\S+", text)
    return match.group(0).rstrip("),.;") if match else ""


def _write_discovery_outputs(leads: list[JobLead], failures: list[JobLead], output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "jobs.json").write_text(json.dumps({"jobs": [asdict(lead) for lead in leads]}, indent=2), encoding="utf-8")
    (out / "discovery_report.md").write_text(render_discovery_report(leads, failures), encoding="utf-8")
    write_job_lead_files(leads, out / "job_descriptions")


def _dedupe_leads(leads: list[JobLead]) -> list[JobLead]:
    seen = set()
    result = []
    for lead in leads:
        key = (lead.title.lower(), lead.company.lower(), lead.url.lower())
        if key not in seen:
            result.append(lead)
            seen.add(key)
    return result


def _clean_text(value: str) -> str:
    value = _html_unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _html_unescape(value: str) -> str:
    return value.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return value[:120] or "job_lead"
