#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import json
import re
import sys


SECTIONED_REQUIREMENTS = {
    "step6_product_context.md": [
        "已扫描的产品资料",
        "选中的产品资料",
        "未采用的产品资料",
        "产品对象与术语校准",
        "黄金参考候选与结论",
        "测试资源类型",
        "资源前提与消耗/归还规则",
        "对需求文档和图片理解的帮助",
        "版本边界与提醒",
    ],
    "step7_test_blueprint.md": [
        "规则装载",
        "测试对象总览",
        "Subsection 蓝图",
        "适用维度",
        "资源类型映射",
        "固定块与必测项",
        "资源前提",
        "黄金参考继承策略",
        "排除项",
        "来源映射",
    ],
    "step9_rule_gate_report.md": [
        "已加载资料",
        "采用的规则",
        "继承的蓝图与组合",
        "剪枝与未落地组合",
        "违规项与修正结果",
        "黄金参考对比或跳过说明",
    ],
    "step9_ui_cases_review.md": [
        "覆盖结论",
        "去重与拆分原则",
        "固定块检查",
        "主要风险与缺口",
    ],
    "step10_case_split_report.md": [
        "轮次概览",
        "数量闸门结果",
        "命中的拆分信号",
        "已拆分用例",
        "未拆分原因",
        "最终结论",
    ],
}
TREE_FILE_RULES = {
    "step8_combination_expansion.md": {"allow_cases": False},
    "step9_ui_cases_final.md": {"allow_cases": True},
    "step10_ui_cases_final.md": {"allow_cases": True},
}
TREE_METADATA_PREFIXES = ("描述：", "来源：", "承接：")
BULLET_RE = re.compile(r"^(?P<indent> *)(- )(?P<content>.+?)\s*$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")


@dataclass
class FileValidationResult:
    path: str
    file_kind: str
    ok: bool = True
    issues: list[str] = field(default_factory=list)
    line_count: int = 0
    node_count: int = 0
    case_count: int = 0

    def add_issue(self, message: str) -> None:
        self.ok = False
        self.issues.append(message)


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def validate_sectioned_file(text: str, result: FileValidationResult, headings: list[str]) -> None:
    lines = text.splitlines()
    result.line_count = len(lines)
    if not text.strip():
        result.add_issue("file is empty")
        return

    heading_indexes: dict[str, int] = {}
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            heading_indexes[match.group(1)] = index

    for heading in headings:
        if heading not in heading_indexes:
            result.add_issue(f"missing section heading: {heading}")
            continue
        start = heading_indexes[heading] + 1
        next_indexes = [heading_indexes[item] for item in headings if item in heading_indexes and heading_indexes[item] > heading_indexes[heading]]
        end = min(next_indexes) if next_indexes else len(lines)
        body = "\n".join(lines[start:end]).strip()
        if not body:
            result.add_issue(f"section is empty: {heading}")


def parse_tree_entries(text: str, result: FileValidationResult) -> list[tuple[int, int, str]]:
    entries: list[tuple[int, int, str]] = []
    lines = text.splitlines()
    result.line_count = len(lines)
    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        match = BULLET_RE.match(line)
        if not match:
            result.add_issue(f"line {lineno}: non-empty line must start with '- '")
            continue
        indent = len(match.group("indent"))
        if indent % 4 != 0:
            result.add_issue(f"line {lineno}: indentation must use multiples of 4 spaces")
            continue
        entries.append((lineno, indent // 4, match.group("content")))
    if not entries:
        result.add_issue("tree file is empty")
    return entries


def validate_tree_file(text: str, result: FileValidationResult, allow_cases: bool) -> None:
    entries = parse_tree_entries(text, result)
    if not entries:
        return

    for index, (lineno, level, content) in enumerate(entries):
        if any(content.startswith(prefix) for prefix in TREE_METADATA_PREFIXES):
            continue

        result.node_count += 1
        if content.startswith("[C] "):
            result.case_count += 1
            if not allow_cases:
                result.add_issue(f"line {lineno}: Step8 tree must not contain '[C]' nodes")
        elif allow_cases and content.startswith("[C]"):
            result.add_issue(f"line {lineno}: case node must use '[C] ' prefix")

        for offset, prefix in enumerate(TREE_METADATA_PREFIXES, start=1):
            meta_index = index + offset
            if meta_index >= len(entries):
                result.add_issue(f"line {lineno}: missing child metadata lines")
                continue
            meta_lineno, meta_level, meta_content = entries[meta_index]
            if meta_level != level + 1 or not meta_content.startswith(prefix):
                result.add_issue(f"line {lineno}: expected child '- {prefix}' indented by 4 spaces")
                continue
            if not meta_content[len(prefix):].strip():
                result.add_issue(f"line {meta_lineno}: metadata line '{prefix}' is empty")

    if result.node_count == 0:
        result.add_issue("missing tree nodes")
    if allow_cases and result.case_count == 0:
        result.add_issue("final case file must contain at least one '[C]' node")


def validate_file(path: Path) -> FileValidationResult:
    if path.name in SECTIONED_REQUIREMENTS:
        result = FileValidationResult(path=str(path), file_kind="sectioned")
    elif path.name in TREE_FILE_RULES:
        result = FileValidationResult(path=str(path), file_kind="tree")
    else:
        result = FileValidationResult(path=str(path), file_kind="unknown")

    if not path.exists():
        result.add_issue("file not found")
        return result

    text = read_text(path)
    if path.name in SECTIONED_REQUIREMENTS:
        validate_sectioned_file(text, result, SECTIONED_REQUIREMENTS[path.name])
    elif path.name in TREE_FILE_RULES:
        validate_tree_file(text, result, TREE_FILE_RULES[path.name]["allow_cases"])
    return result


def build_required_file_names(include_step10: bool) -> list[str]:
    required = [
        "step6_product_context.md",
        "step7_test_blueprint.md",
        "step8_combination_expansion.md",
        "step9_rule_gate_report.md",
        "step9_ui_cases_review.md",
        "step9_ui_cases_final.md",
    ]
    if include_step10:
        required.extend(["step10_case_split_report.md", "step10_ui_cases_final.md"])
    return required


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate testcase-generator Step6-9 outputs, optionally including Step10.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    parser.add_argument("--include-step10", action="store_true", help="Also validate Step10 outputs")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    required_files = build_required_file_names(args.include_step10)
    results = [validate_file(workdir / filename) for filename in required_files]
    output = {
        "ok": all(item.ok for item in results),
        "workdir": str(workdir),
        "include_step10": args.include_step10,
        "validated_files": len(results),
        "results": [
            {
                "path": item.path,
                "file_kind": item.file_kind,
                "ok": item.ok,
                "line_count": item.line_count,
                "node_count": item.node_count,
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
