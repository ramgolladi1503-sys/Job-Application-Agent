from __future__ import annotations

import email
import imaplib
import os
import re
from dataclasses import dataclass
from email.message import Message
from pathlib import Path


@dataclass(frozen=True)
class EmailFetchConfig:
    host: str
    username: str
    password: str
    mailbox: str = "INBOX"
    query: str = '(OR SUBJECT "job alert" SUBJECT "jobs")'
    limit: int = 25


def fetch_job_alert_emails(config: EmailFetchConfig, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    with imaplib.IMAP4_SSL(config.host) as client:
        client.login(config.username, config.password)
        client.select(config.mailbox)
        status, data = client.search(None, config.query)
        if status != "OK" or not data or not data[0]:
            return []
        ids = data[0].split()[-config.limit :]
        for index, message_id in enumerate(reversed(ids), start=1):
            status, payload = client.fetch(message_id, "(RFC822)")
            if status != "OK" or not payload:
                continue
            raw = _extract_raw_message(payload)
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            text = _message_to_text(msg)
            subject = _safe_subject(msg.get("Subject", f"job_alert_{index}"))
            path = out / f"{index:03d}_{subject}.txt"
            path.write_text(text, encoding="utf-8")
            paths.append(path)
    return paths


def fetch_job_alert_emails_from_env(output_dir: str | Path, limit: int = 25) -> list[Path]:
    config = EmailFetchConfig(
        host=_env_required("JOB_ALERT_IMAP_HOST"),
        username=_env_required("JOB_ALERT_IMAP_USERNAME"),
        password=_env_required("JOB_ALERT_IMAP_PASSWORD"),
        mailbox=os.getenv("JOB_ALERT_IMAP_MAILBOX", "INBOX"),
        query=os.getenv("JOB_ALERT_IMAP_QUERY", '(OR SUBJECT "job alert" SUBJECT "jobs")'),
        limit=limit,
    )
    return fetch_job_alert_emails(config, output_dir)


def _extract_raw_message(payload: list[bytes | tuple[bytes, bytes] | tuple[bytes, bytes, bytes]]) -> bytes:
    for item in payload:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return b""


def _message_to_text(msg: Message) -> str:
    parts = []
    if msg.get("Subject"):
        parts.append(f"Subject: {msg.get('Subject')}")
    if msg.get("From"):
        parts.append(f"From: {msg.get('From')}")
    if msg.get("Date"):
        parts.append(f"Date: {msg.get('Date')}")
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True)
            if payload:
                parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parts.append(payload.decode(msg.get_content_charset() or "utf-8", errors="replace"))
    return "\n\n".join(parts)


def _safe_subject(subject: str) -> str:
    decoded = str(email.header.make_header(email.header.decode_header(subject)))
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", decoded).strip("_").lower()
    return cleaned[:80] or "job_alert"


def _env_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
