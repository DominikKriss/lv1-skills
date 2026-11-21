"""Check that docs/adr/README.md lists every ADR with the status, scope and date in its file.

Usage: check_adr_index.py [ADR_DIR]
"""
import re
import sys
from pathlib import Path

FILE = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")
ROW = re.compile(r"^\|\s*\[(\d{4})\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
STATUS = re.compile(r"^(Proposed|Accepted|Deprecated|Superseded by \d{4})$")


def field(text, name):
    m = re.search(rf"^- \*\*{name}:\*\* (.+)$", text, re.M)
    return m.group(1).strip() if m else None


def check(adr_dir):
    errors = []
    files = {}
    for p in sorted(adr_dir.glob("*.md")):
        if p.name in ("README.md", "template.md"):
            continue
        m = FILE.match(p.name)
        if not m:
            errors.append(f"{p.name}: name must be NNNN-short-title.md")
            continue
        text = p.read_text(encoding="utf-8")
        title = re.search(r"^# (\d{4})\. (.+)$", text, re.M)
        if not title or title.group(1) != m.group(1):
            errors.append(f"{p.name}: first heading must be '# {m.group(1)}. Title'")
        meta = {k: field(text, k) for k in ("Status", "Scope", "Date")}
        for k, v in meta.items():
            if not v:
                errors.append(f"{p.name}: missing '- **{k}:**' line")
        if meta["Status"] and not STATUS.match(meta["Status"]):
            errors.append(f"{p.name}: status '{meta['Status']}' is not Proposed, Accepted, Deprecated or Superseded by NNNN")
        files[m.group(1)] = (p.name, title.group(2) if title else None, meta)
    rows = {}
    for line in (adr_dir / "README.md").read_text(encoding="utf-8").splitlines():
        m = ROW.match(line.strip())
        if m:
            num, link, title, status, scope, date = m.groups()
            if num in rows:
                errors.append(f"index: {num} is listed twice")
            rows[num] = (link, title, status, scope, date)
    for num, (name, title, meta) in files.items():
        if num not in rows:
            errors.append(f"index: {name} is not listed")
            continue
        link, rtitle, status, scope, date = rows[num]
        if link != name:
            errors.append(f"index: {num} links to {link}, not {name}")
        for label, want, got in (("title", title, rtitle), ("status", meta["Status"], status),
                                 ("scope", meta["Scope"], scope), ("date", meta["Date"], date)):
            if want and want != got:
                errors.append(f"index: {num} {label} is '{got}', the file says '{want}'")
    for num in rows:
        if num not in files:
            errors.append(f"index: {num} has no ADR file")
    return errors


def main(argv):
    adr_dir = Path(argv[0]) if argv else Path(__file__).resolve().parents[2] / "docs" / "adr"
    errors = check(adr_dir)
    for e in errors:
        print(e)
    print("adr index: ok" if not errors else f"adr index: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
