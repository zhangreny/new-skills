#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import json
import sys


CASE_FILE_NAMES = {
    "step6_subagent_a_ui_cases.md",
    "step6_subagent_b_ui_cases.md",
    "step7_ui_cases_merged.md",
    "step8_ui_cases_final.md",
}
REVIEW_FILE_NAMES = {
    "step8_ui_cases_review.md",
}
REQUIRED_FILE_NAMES = CASE_FILE_NAMES | REVIEW_FILE_NAMES


@dataclass
class FileValidationResult:
    path: str
    file_kind: str
    ok: bool = True
    issues: list[str] = field(default_factory=list)
    line_count: int = 0
    heading_count: int = 0
    description_count: int = 0
    source_count: int = 0

    def add_issue(self, message: str) -> None:
        self.ok = False
        self.issues.append(message)


def expected_files(workdir: Path) -> list[Path]:
    return [workdir / name for name in sorted(REQUIRED_FILE_NAMES)]


def resolve_requested_file(workdir: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = workdir / path
    return path.resolve(strict=False)


def validate_prefixed_line(
    *,
    lineno: int,
    stripped: str,
    prefix: str,
    label: str,
    result: FileValidationResult,
) -> None:
    content = stripped.removeprefix(prefix).strip()
    if not content:
        result.add_issue(f"line {lineno}: {label} line is missing content after '{prefix}'")


def validate_case_file(text: str, result: FileValidationResult) -> None:
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        lineno = index + 1
        stripped = lines[index].strip()

        if not stripped:
            index += 1
            continue

        if not stripped.startswith("#"):
            result.add_issue(f"line {lineno}: unexpected content for case markdown: {stripped[:80]}")
            index += 1
            continue

        result.heading_count += 1
        index += 1
        if index >= len(lines) or lines[index].strip():
            result.add_issue(f"line {lineno}: heading must be followed by a blank line")
        else:
            index += 1

        if index >= len(lines):
            result.add_issue(f"line {lineno}: missing '描述：' line after heading")
            break

        description_lineno = index + 1
        description_stripped = lines[index].strip()
        if not description_stripped.startswith("描述："):
            result.add_issue(f"line {description_lineno}: expected '描述：' line after heading")
        else:
            result.description_count += 1
            validate_prefixed_line(
                lineno=description_lineno,
                stripped=description_stripped,
                prefix="描述：",
                label="description",
                result=result,
            )
            index += 1

        if index >= len(lines):
            result.add_issue(f"line {description_lineno}: missing '来源：' line after '描述：'")
            break

        source_lineno = index + 1
        source_stripped = lines[index].strip()
        if not source_stripped.startswith("来源："):
            result.add_issue(f"line {source_lineno}: expected '来源：' line after '描述：'")
        else:
            result.source_count += 1
            validate_prefixed_line(
                lineno=source_lineno,
                stripped=source_stripped,
                prefix="来源：",
                label="source",
                result=result,
            )
            index += 1

    if result.heading_count == 0:
        result.add_issue("missing markdown headings")
    if result.description_count == 0:
        result.add_issue("missing '描述：' lines")
    if result.source_count == 0:
        result.add_issue("missing '来源：' lines")
    if result.heading_count != result.description_count:
        result.add_issue("heading count does not match '描述：' line count")
    if result.heading_count != result.source_count:
        result.add_issue("heading count does not match '来源：' line count")


def validate_review_file(text: str, result: FileValidationResult) -> None:
    if not text.strip():
        result.add_issue("review file is empty")


def validate_file(path: Path) -> FileValidationResult:
    if path.name in CASE_FILE_NAMES:
        file_kind = "case"
    elif path.name in REVIEW_FILE_NAMES:
        file_kind = "review"
    else:
        file_kind = "unknown"

    result = FileValidationResult(path=str(path), file_kind=file_kind)
    if not path.exists():
        result.add_issue("file not found")
        return result

    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        result.add_issue(f"utf-8 decode failed: {exc}")
        return result

    result.line_count = len(text.splitlines())

    if "\ufffd" in text:
        result.add_issue("contains replacement character U+FFFD")
    if "\x00" in text:
        result.add_issue("contains NUL byte")

    if path.name in CASE_FILE_NAMES:
        validate_case_file(text, result)
    elif path.name in REVIEW_FILE_NAMES:
        validate_review_file(text, result)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate generated case markdown outputs for encoding loss and expected markdown structure."
    )
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    parser.add_argument(
        "--files",
        nargs="*",
        help="Optional explicit file names under workdir to validate",
    )
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    files = [resolve_requested_file(workdir, name) for name in args.files] if args.files else expected_files(workdir)
    if not files:
        print(json.dumps({"ok": False, "error": "no generated markdown files found"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    results = [validate_file(path) for path in files]
    output = {
        "ok": all(item.ok for item in results),
        "workdir": str(workdir),
        "validated_files": len(results),
        "results": [
            {
                "path": item.path,
                "file_kind": item.file_kind,
                "ok": item.ok,
                "line_count": item.line_count,
                "heading_count": item.heading_count,
                "description_count": item.description_count,
                "source_count": item.source_count,
                "issues": item.issues,
            }
            for item in results
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not output["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
