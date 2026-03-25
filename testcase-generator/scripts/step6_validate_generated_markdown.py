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
    "step6_ui_cases_merged.md",
    "step6_ui_cases_final.md",
}

REVIEW_FILE_NAMES = {
    "step6_ui_cases_review.md",
}

REVIEW_REQUIRED_HEADINGS = {
    "# Step6 Review",
    "## 汇总结论",
    "## 发现与修正",
    "## 最终判断",
}

REVIEW_BULLET_SECTIONS = {
    "## 汇总结论",
    "## 发现与修正",
}

REVIEW_ALLOWED_VERDICTS = {
    "（通过）",
    "（需补充）",
}


@dataclass
class FileValidationResult:
    path: str
    ok: bool = True
    issues: list[str] = field(default_factory=list)
    line_count: int = 0
    heading_count: int = 0
    description_count: int = 0
    source_count: int = 0
    suspicious_question_line_count: int = 0

    def add_issue(self, message: str) -> None:
        self.ok = False
        self.issues.append(message)


def expected_files(workdir: Path) -> list[Path]:
    names = sorted(CASE_FILE_NAMES | REVIEW_FILE_NAMES)
    return [workdir / name for name in names if (workdir / name).exists()]


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
    if "?" in stripped:
        result.suspicious_question_line_count += 1
        result.add_issue(f"line {lineno}: {label} contains '?' which is suspicious for Chinese mojibake")


def validate_case_file(path: Path, text: str, result: FileValidationResult) -> None:
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
        if "?" in stripped:
            result.suspicious_question_line_count += 1
            result.add_issue(f"line {lineno}: heading contains '?' which is suspicious for Chinese mojibake")

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


def validate_review_file(path: Path, text: str, result: FileValidationResult) -> None:
    seen_headings: set[str] = set()
    section_bullet_counts = {section: 0 for section in REVIEW_BULLET_SECTIONS}
    verdicts: list[str] = []
    current_section: str | None = None

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            result.heading_count += 1
            current_section = stripped
            seen_headings.add(stripped)
            if stripped not in REVIEW_REQUIRED_HEADINGS:
                result.add_issue(f"line {lineno}: unexpected review heading: {stripped}")
        elif stripped.startswith("- "):
            if current_section not in REVIEW_BULLET_SECTIONS:
                result.add_issue(f"line {lineno}: bullet item must appear under a review bullet section")
            else:
                section_bullet_counts[current_section] += 1
        elif stripped.startswith("（") and stripped.endswith("）"):
            if current_section != "## 最终判断":
                result.add_issue(f"line {lineno}: verdict must appear under '## 最终判断'")
            verdicts.append(stripped)
            if stripped not in REVIEW_ALLOWED_VERDICTS:
                result.add_issue(f"line {lineno}: unexpected review verdict: {stripped}")
        else:
            result.add_issue(f"line {lineno}: unexpected content for review markdown: {stripped[:80]}")

        if "?" in stripped:
            result.suspicious_question_line_count += 1
            result.add_issue(f"line {lineno}: content contains '?' which is suspicious for Chinese mojibake")

    if result.heading_count == 0:
        result.add_issue("missing markdown headings")
    for heading in sorted(REVIEW_REQUIRED_HEADINGS):
        if heading not in seen_headings:
            result.add_issue(f"missing required review heading: {heading}")
    for section, count in section_bullet_counts.items():
        if count == 0:
            result.add_issue(f"missing bullet items under review section: {section}")
    if len(verdicts) != 1:
        result.add_issue("review markdown must contain exactly one final verdict line")


def validate_file(path: Path) -> FileValidationResult:
    result = FileValidationResult(path=str(path))
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

    if path.name in CASE_FILE_NAMES:
        validate_case_file(path, text, result)
    elif path.name in REVIEW_FILE_NAMES:
        validate_review_file(path, text, result)
    else:
        if "?" in text:
            result.suspicious_question_line_count += text.count("?")
            result.add_issue("contains '?' which is suspicious for Chinese mojibake")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate generated markdown outputs for encoding loss and expected markdown structure."
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

    files = [workdir / name for name in args.files] if args.files else expected_files(workdir)
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
                "ok": item.ok,
                "line_count": item.line_count,
                "heading_count": item.heading_count,
                "description_count": item.description_count,
                "source_count": item.source_count,
                "suspicious_question_line_count": item.suspicious_question_line_count,
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
