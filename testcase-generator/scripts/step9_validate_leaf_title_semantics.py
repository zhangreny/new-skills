#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import argparse
import json
import re


CASE_LINE_RE = re.compile(r"^(?P<indent> *)- \[C\] (?P<title>.+?)\s*$")
NODE_LINE_RE = re.compile(r"^(?P<indent> *)- (?P<content>.+?)\s*$")
GENERIC_EXACT_TITLES = {
    "显示入口",
    "显示默认值",
    "显示说明文案",
    "显示资源范围",
    "列表可见",
    "详情可见",
    "状态正确",
    "提交成功",
    "按钮置灰",
    "提示必填",
    "提示格式错误",
    "提示资源冲突",
    "保留原状态",
    "详情显示限制",
}
GENERIC_STEM_RE = re.compile(r"^(显示|提示|提交|按钮|状态|列表|详情|记录|保留).{0,6}$")
META_PREFIXES = ("描述：", "来源：", "承接：")


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def is_generic_title(title: str) -> bool:
    if title in GENERIC_EXACT_TITLES:
        return True
    return bool(GENERIC_STEM_RE.fullmatch(title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate that Step9 leaf titles are semantic and not fixed generic buckets.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    case_file = workdir / "step9_ui_cases_final.md"
    if not case_file.is_file():
        print(json.dumps({"ok": False, "error": f"case file not found: {case_file}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    stack: list[str] = []
    generic_examples: list[dict] = []
    parent_case_titles: dict[str, list[str]] = defaultdict(list)
    case_count = 0

    for lineno, raw in enumerate(read_text(case_file).splitlines(), start=1):
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        content = stripped[2:]
        if content.startswith(META_PREFIXES):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        level = indent // 4
        while len(stack) > level:
            stack.pop()

        case_match = CASE_LINE_RE.match(raw)
        if case_match:
            title = case_match.group("title").strip()
            case_count += 1
            parent_key = " | ".join(stack)
            parent_case_titles[parent_key].append(title)
            if is_generic_title(title):
                generic_examples.append(
                    {
                        "line": lineno,
                        "title": title,
                        "parent_path": list(stack),
                    }
                )
            continue

        node_match = NODE_LINE_RE.match(raw)
        if not node_match:
            continue
        node_content = node_match.group("content")
        if node_content.startswith("[C] "):
            continue

        if len(stack) == level:
            stack.append(node_content)
        else:
            stack = stack[:level] + [node_content]

    repetitive_subtrees: list[dict] = []
    for parent_key, titles in parent_case_titles.items():
        if len(titles) < 5:
            continue
        generic_titles = [title for title in titles if is_generic_title(title)]
        if not generic_titles:
            continue
        generic_ratio = len(generic_titles) / len(titles)
        unique_titles = sorted(set(titles))
        if generic_ratio >= 0.7 and len(unique_titles) <= 10:
            repetitive_subtrees.append(
                {
                    "parent_path": parent_key.split(" | ") if parent_key else [],
                    "case_count": len(titles),
                    "generic_case_count": len(generic_titles),
                    "generic_ratio": round(generic_ratio, 3),
                    "title_examples": unique_titles[:10],
                }
            )

    issues: list[dict] = []
    if generic_examples:
        for example in generic_examples[:50]:
            issues.append(
                {
                    "type": "generic_exact_or_stem_leaf_title",
                    "line": example["line"],
                    "title": example["title"],
                    "parent_path": example["parent_path"],
                    "reason": "leaf title is a generic result bucket and must be rewritten to 动作 + 条件 + 结果",
                }
            )
    if repetitive_subtrees:
        for subtree in repetitive_subtrees[:20]:
            issues.append(
                {
                    "type": "repetitive_generic_subtree",
                    "parent_path": subtree["parent_path"],
                    "case_count": subtree["case_count"],
                    "generic_case_count": subtree["generic_case_count"],
                    "generic_ratio": subtree["generic_ratio"],
                    "title_examples": subtree["title_examples"],
                    "reason": "sibling leaf titles under the same parent are dominated by generic result buckets",
                }
            )

    output = {
        "ok": not issues,
        "case_file": str(case_file),
        "case_count": case_count,
        "generic_title_count": len(generic_examples),
        "generic_title_examples": generic_examples[:50],
        "repetitive_subtrees": repetitive_subtrees[:20],
        "issues": issues,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not output["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
