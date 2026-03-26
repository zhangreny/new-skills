#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import json
import re
import sys


DIMENSION_FILE_NAMES = {
    "step6_dimension_breakdown.md",
}
TREE_FILE_NAMES = {
    "step7_combination_expansion.md",
    "step8_ui_cases_final.md",
}
TEXT_FILE_NAMES = {
    "step8_rule_gate_report.md",
    "step8_ui_cases_review.md",
}
REQUIRED_FILE_NAMES = DIMENSION_FILE_NAMES | TREE_FILE_NAMES | TEXT_FILE_NAMES
BULLET_RE = re.compile(r"^(?P<indent> *)(- )(?P<content>.+?)\s*$")
DIMENSION_LINE_RE = re.compile(r"^(?P<name>[^：\s][^：]*维度)：(?P<values>.+)$")


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
    case_count: int = 0

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


def validate_dimension_file(text: str, result: FileValidationResult) -> None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        result.add_issue("dimension file is empty")
        return

    for lineno, line in enumerate(lines, start=1):
        match = DIMENSION_LINE_RE.match(line)
        if not match:
            result.add_issue(f"line {lineno}: expected 'xx维度：值1 / 值2 / 值3' format")
            continue
        values = [item.strip() for item in match.group("values").split("/") if item.strip()]
        if len(values) == 0:
            result.add_issue(f"line {lineno}: dimension line must include at least one value")


def parse_bullet_line(line: str) -> tuple[int, str] | None:
    match = BULLET_RE.match(line)
    if not match:
        return None
    indent = len(match.group("indent"))
    if indent % 4 != 0:
        return (-1, match.group("content"))
    return (indent // 4, match.group("content"))


def validate_tree_file(text: str, result: FileValidationResult, *, allow_cases: bool) -> None:
    entries: list[tuple[int, int, str]] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        parsed = parse_bullet_line(raw_line)
        if parsed is None:
            result.add_issue(f"line {lineno}: non-empty line must start with '- '")
            continue
        level, content = parsed
        if level < 0:
            result.add_issue(f"line {lineno}: indentation must use multiples of 4 spaces")
            continue
        entries.append((lineno, level, content))

    if not entries:
        result.add_issue("tree file is empty")
        return

    for index, (lineno, level, content) in enumerate(entries):
        if content.startswith("描述："):
            result.description_count += 1
            validate_prefixed_line(
                lineno=lineno,
                stripped=content,
                prefix="描述：",
                label="description",
                result=result,
            )
            continue

        if content.startswith("来源："):
            result.source_count += 1
            validate_prefixed_line(
                lineno=lineno,
                stripped=content,
                prefix="来源：",
                label="source",
                result=result,
            )
            continue

        result.heading_count += 1
        if content.startswith("[C] "):
            result.case_count += 1
            if not allow_cases:
                result.add_issue(f"line {lineno}: tree file must not contain '[C]' case nodes")
        elif allow_cases and content.startswith("[C]") is False and level > 0:
            # non-case grouping nodes are allowed
            pass

        if index + 1 >= len(entries):
            result.add_issue(f"line {lineno}: missing child '- 描述：' item")
            continue
        desc_lineno, desc_level, desc_content = entries[index + 1]
        if desc_level != level + 1 or not desc_content.startswith("描述："):
            result.add_issue(f"line {lineno}: expected child '- 描述：' item indented by 4 spaces")

        if index + 2 >= len(entries):
            result.add_issue(f"line {lineno}: missing child '- 来源：' item")
            continue
        source_lineno, source_level, source_content = entries[index + 2]
        if source_level != level + 1 or not source_content.startswith("来源："):
            result.add_issue(f"line {lineno}: expected child '- 来源：' item indented by 4 spaces")

    if result.heading_count == 0:
        result.add_issue("missing tree nodes")
    if result.heading_count != result.description_count:
        result.add_issue("node count does not match '描述：' line count")
    if result.heading_count != result.source_count:
        result.add_issue("node count does not match '来源：' line count")
    if allow_cases and result.case_count == 0:
        result.add_issue("final case file must contain at least one '[C]' node")


def validate_text_file(text: str, result: FileValidationResult) -> None:
    if not text.strip():
        result.add_issue("text file is empty")


def validate_file(path: Path) -> FileValidationResult:
    if path.name in DIMENSION_FILE_NAMES:
        file_kind = "dimension"
    elif path.name in TREE_FILE_NAMES:
        file_kind = "tree"
    elif path.name in TEXT_FILE_NAMES:
        file_kind = "text"
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

    if path.name in DIMENSION_FILE_NAMES:
        validate_dimension_file(text, result)
    elif path.name == "step7_combination_expansion.md":
        validate_tree_file(text, result, allow_cases=False)
    elif path.name == "step8_ui_cases_final.md":
        validate_tree_file(text, result, allow_cases=True)
    elif path.name in TEXT_FILE_NAMES:
        validate_text_file(text, result)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate testcase-generator Step6-8 outputs.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    parser.add_argument("--files", nargs="*", help="Optional explicit file names under workdir to validate")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    files = [resolve_requested_file(workdir, name) for name in args.files] if args.files else expected_files(workdir)
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
                "case_count": item.case_count,
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
