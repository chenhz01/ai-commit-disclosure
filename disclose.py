"""ai-commit-disclosure: audit a git log for AI-contribution disclosure hygiene.

Input: `git log --format=fuller` output (or raw messages separated by
"commit <sha>" lines). Every commit is classified:

  disclosed_ai         an AI marker trailer exists (AI-assisted / Generated-by /
                       Assisted-by / AI-looking Co-authored-by)
  undeclared_suspect   an AI-looking identity appears (author or Co-authored-by)
                       but no explicit disclosure trailer exists
  human                nothing AI-looking detected

The report answers one management question: of the commits that look
AI-involved, how many actually said so?
"""
from __future__ import annotations

import os
import re
import json

TRAILER_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)\s*:\s*(.+)$", re.MULTILINE)
DISCLOSURE_KEYS = {"ai-assisted", "generated-by", "assisted-by", "ai-generated",
                   "co-authored-by", "authored-by"}
AI_IDENTITY_PATTERNS = [
    r"ai[-_ ]?assistant", r"\bai\b", r"\bbot\b", r"\bcopilot\b", r"\bllm\b",
    r"\bclaude\b", r"\bgpt\b", r"\bgemini\b", r"\bchatgpt\b", r"\bdeepseek\b",
    r"generated\s+with", r"\bcodex\b", r"\bcursor\b",
]
AI_IDENTITY_RE = re.compile("|".join(AI_IDENTITY_PATTERNS), re.IGNORECASE)
COMMIT_SEP_RE = re.compile(r"^commit ([0-9a-f]{7,40})", re.MULTILINE)
DATE_RE = re.compile(r"^AuthorDate:\s*(.+)$", re.MULTILINE)


def looks_ai_identity(text: str, patterns=None) -> bool:
    if patterns is None:
        return bool(AI_IDENTITY_RE.search(text))
    return bool(re.compile("|".join(patterns), re.IGNORECASE).search(text))


def parse_person(line: str) -> dict:
    m = re.match(r"^(.*?)\s*<([^>]*)>\s*$", line.strip())
    if m:
        return {"name": m.group(1).strip(), "email": m.group(2).strip().lower()}
    return {"name": line.strip(), "email": ""}


def split_commits(text: str) -> list:
    """Split a git-log dump into raw commit blocks."""
    text = text.replace("\r\n", "\n")
    if not text.strip():
        return []
    marks = [m.start() for m in COMMIT_SEP_RE.finditer(text)]
    if not marks:
        return [text.strip()]
    blocks = []
    for i, start in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(text)
        blocks.append(text[start:end].strip())
    return blocks


def parse_commit(block: str) -> dict:
    lines = block.split("\n")
    sha = ""
    m = re.match(r"^commit ([0-9a-f]{7,40})", lines[0]) if lines else None
    if m:
        sha = m.group(1)
    author = ""
    am = re.search(r"^Author:\s*(.+)$", block, re.MULTILINE)
    if am:
        author = am.group(1)
    dm = DATE_RE.search(block)
    date = dm.group(1).strip() if dm else ""
    subject = ""
    sm = re.search(r"\n\n(.+)", block)
    if sm:
        subject = sm.group(1).strip().split("\n")[0]
    trailers = []
    for tm in TRAILER_RE.finditer(block):
        key = tm.group(1).lower()
        if key in DISCLOSURE_KEYS or key in {"signed-off-by"}:
            trailers.append({"key": key, "value": tm.group(2).strip()})
    return {"sha": sha, "author": author, "date": date, "subject": subject,
            "trailers": trailers}


def classify(commit: dict, ai_patterns=None) -> tuple:
    """Returns (label, reasons). Label in {disclosed_ai, undeclared_suspect, human}."""
    reasons = []
    explicit = False
    ai_identity_seen = False
    author_p = parse_person(commit.get("author", ""))
    if looks_ai_identity(author_p["name"], ai_patterns):
        ai_identity_seen = True
        reasons.append("author name looks AI-generated: %s" % author_p["name"])
    for t in commit.get("trailers", []):
        key, value = t["key"], t["value"]
        if key in ("ai-assisted", "generated-by", "assisted-by", "ai-generated"):
            if value.lower() in ("no", "false", "none"):
                continue
            explicit = True
            reasons.append("%s: %s" % (key, value))
        elif key == "co-authored-by":
            p = parse_person(value)
            if looks_ai_identity(p["name"], ai_patterns):
                ai_identity_seen = True
                reasons.append("AI-looking co-author: %s" % p["name"])
    if explicit and ai_identity_seen:
        return "disclosed_ai", reasons
    if explicit:
        return "disclosed_ai", reasons
    if ai_identity_seen:
        return "undeclared_suspect", reasons
    return "human", []


def audit(text: str, ai_patterns=None) -> dict:
    blocks = split_commits(text)
    commits, missing = [], []
    counts = {"disclosed_ai": 0, "undeclared_suspect": 0, "human": 0}
    for b in blocks:
        c = parse_commit(b)
        label, reasons = classify(c, ai_patterns)
        c["label"], c["reasons"] = label, reasons
        counts[label] += 1
        commits.append(c)
        if label == "undeclared_suspect":
            missing.append(c["sha"] or "(no sha)")
    ai_involved = counts["disclosed_ai"] + counts["undeclared_suspect"]
    rate = (counts["disclosed_ai"] / ai_involved) if ai_involved else 1.0
    return {"total": len(commits), "disclosed_ai": counts["disclosed_ai"],
            "undeclared_suspect": counts["undeclared_suspect"], "human": counts["human"],
            "ai_involved": ai_involved, "disclosure_rate": round(rate, 4),
            "missing_disclosure": missing, "commits": commits}


def audit_file(path: str, ai_patterns=None) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return audit(f.read(), ai_patterns)


def audit_dir(path: str, ai_patterns=None) -> dict:
    merged = []
    for f in sorted(os.listdir(path)):
        if f.endswith(".txt") or f.endswith(".log"):
            with open(os.path.join(path, f), "r", encoding="utf-8", errors="replace") as fh:
                merged.extend(split_commits(fh.read()))
    return audit("\n".join(merged), ai_patterns)


def gate_verdict(report: dict) -> str:
    """FAIL if any AI-looking commit lacked disclosure."""
    return "FAIL" if report["undeclared_suspect"] > 0 else "PASS"
