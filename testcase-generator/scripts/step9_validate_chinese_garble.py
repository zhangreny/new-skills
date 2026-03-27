#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys


STEP9_FILES = (
    "step9_rule_gate_report.md",
    "step9_ui_cases_review.md",
    "step9_ui_cases_final.md",
)
QUESTION_MARK_RUN_RE = re.compile(r"\?{2,}")
REPLACEMENT_CHAR = "\uFFFD"


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def issue(file_path: Path, line: int | None, matched_text: str, reason: str) -> dict:
    return {
        "file": str(file_path),
        "line": line,
        "matched_text": matched_text,
        "reason": reason,
    }


def print_json(payload: dict) -> None:
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def scan_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    if not path.is_file():
        issues.append(issue(path, None, "", "file not found"))
        return issues

    text = read_text(path)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if REPLACEMENT_CHAR in line:
            issues.append(issue(path, lineno, REPLACEMENT_CHAR, "found replacement character"))
        for match in QUESTION_MARK_RUN_RE.finditer(line):
            issues.append(issue(path, lineno, match.group(0), "found repeated ASCII question marks"))
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Step9 outputs for Chinese garble markers.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print_json({"ok": False, "error": f"workdir not found: {workdir}"})
        sys.exit(1)

    checked_files = [str((workdir / file_name).resolve(strict=False)) for file_name in STEP9_FILES]
    issues: list[dict] = []
    for file_name in STEP9_FILES:
        issues.extend(scan_file(workdir / file_name))

    output = {
        "ok": len(issues) == 0,
        "checked_files": checked_files,
        "issues": issues,
    }
    print_json(output)
    if issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
