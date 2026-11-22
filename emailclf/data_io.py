"""Loading emails from CSV, a folder of .txt files, or a folder of .eml files.

Start with CSV / .txt. Connecting to Gmail/IMAP is possible later, but OAuth setup can
eat hours and teaches you nothing about classification.

CSV columns:   id (optional), sender (optional), subject, body, label (optional)
.txt format:   optional "Subject: ..." and "From: ..." lines at the top, blank line, body.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path

csv.field_size_limit(10_000_000)


@dataclass
class Email:
    id: str
    subject: str
    body: str
    sender: str = ""
    label: str | None = None


def load_csv(path: Path) -> list[Email]:
    emails: list[Email] = []
    with open(path, newline="", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=1):
            emails.append(
                Email(
                    id=(row.get("id") or f"row{n}").strip(),
                    subject=row.get("subject", "") or "",
                    body=row.get("body", "") or "",
                    sender=row.get("sender", "") or "",
                    label=(row.get("label") or "").strip() or None,
                )
            )
    return emails


def parse_txt(path: Path) -> Email:
    text = path.read_text(encoding="utf-8", errors="replace")
    subject, sender = "", ""
    lines = text.split("\n")
    body_start = 0
    for i, line in enumerate(lines[:10]):
        low = line.lower()
        if low.startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
        elif low.startswith("from:"):
            sender = line.split(":", 1)[1].strip()
            body_start = i + 1
        elif not line.strip():
            body_start = i + 1
            break
        else:
            break
    return Email(id=path.stem, subject=subject, body="\n".join(lines[body_start:]).strip(), sender=sender)


def parse_eml(path: Path) -> Email:
    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    part = msg.get_body(preferencelist=("plain", "html"))
    body = part.get_content() if part is not None else ""
    return Email(id=path.stem, subject=str(msg["subject"] or ""), body=body, sender=str(msg["from"] or ""))


def load_folder(path: Path) -> list[Email]:
    emails: list[Email] = []
    for file in sorted(path.iterdir()):
        if file.suffix.lower() == ".txt":
            emails.append(parse_txt(file))
        elif file.suffix.lower() == ".eml":
            emails.append(parse_eml(file))
    return emails


def load_emails(path: str | Path) -> list[Email]:
    path = Path(path)
    if path.is_dir():
        return load_folder(path)
    if path.suffix.lower() == ".csv":
        return load_csv(path)
    if path.suffix.lower() == ".eml":
        return [parse_eml(path)]
    return [parse_txt(path)]
