#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import json
import re
from typing import Iterable, Optional


PRODUCT_DIRS = {
    "lb": "负载均衡",
    "vpc": "虚拟专有云网络",
    "ops": "Everoute 服务运维",
    "dfw": "分布式防火墙",
}
PRODUCT_RULE_FILES = {
    "lb": "everoute_lb_testcase_rules.md",
    "vpc": "everoute_vpc_testcase_rules.md",
    "ops": "everoute_ops_testcase_rules.md",
    "dfw": "everoute_dfw_testcase_rules.md",
}
PRODUCT_NAMES = {
    "lb": ("LB", "负载均衡"),
    "vpc": ("VPC", "虚拟专有云网络"),
    "ops": ("OPS", "运维", "Everoute 服务运维"),
    "dfw": ("DFW", "分布式防火墙"),
}
TOKEN_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_]+")
PATH_PATTERNS = [
    re.compile(r"([A-Za-z]:\\[^`\n]+?\.md)"),
    re.compile(r"(references[\\/][^`\n]+?\.md)"),
]
STOPWORDS = {
    "测试用例",
    "页面",
    "页",
    "步骤",
    "step",
    "tower",
    "ui",
    "case",
}


@dataclass
class CaseEntry:
    source_file: str
    path_tokens: list[str]
    case_title: str
    match_scope: str
    priority: int
    normalized_tokens: list[str]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_selected_golden_path(workdir: Path) -> Optional[Path]:
    candidate_files = [
        workdir / "step6_product_context.md",
        workdir / "step7_test_blueprint.md",
    ]
    for file_path in candidate_files:
        if not file_path.is_file():
            continue
        text = read_text(file_path)
        for line in text.splitlines():
            if "已采用黄金参考" not in line:
                continue
            for pattern in PATH_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                raw = match.group(1)
                if re.match(r"^[A-Za-z]:\\", raw):
                    resolved = Path(raw).expanduser().resolve(strict=False)
                else:
                    resolved = (Path(__file__).resolve().parent.parent / raw).resolve(strict=False)
                if resolved.is_file():
                    return resolved
    return None


def detect_products(workdir: Path) -> tuple[Optional[str], list[str]]:
    step7_path = workdir / "step7_test_blueprint.md"
    text = read_text(step7_path) if step7_path.is_file() else ""
    main_product: Optional[str] = None
    supplementary: list[str] = []

    main_match = re.search(r"主产品(?:为|是)\s*`?([A-Za-z\u4e00-\u9fff ]+)`?", text)
    if main_match:
        raw = main_match.group(1).strip()
        for product, names in PRODUCT_NAMES.items():
            if any(name.lower() in raw.lower() for name in names):
                main_product = product
                break

    rule_hits: list[str] = []
    for product, filename in PRODUCT_RULE_FILES.items():
        if filename in text and product not in rule_hits:
            rule_hits.append(product)

    if main_product is None and rule_hits:
        main_product = rule_hits[0]

    if main_product is not None:
        supplementary = [product for product in rule_hits if product != main_product]
    else:
        supplementary = rule_hits

    return main_product, supplementary


def collect_history_case_files(skill_root: Path, selected_golden: Optional[Path], main_product: Optional[str], supplementary: list[str]) -> list[tuple[Path, str, int]]:
    seen: set[str] = set()
    sources: list[tuple[Path, str, int]] = []
    reference_root = skill_root / "references" / "UI-former-testcase-analyse" / "Everoute"

    def add_path(path: Path, scope: str, priority: int) -> None:
        resolved = str(path.resolve(strict=False))
        if resolved in seen or not path.is_file():
            return
        seen.add(resolved)
        sources.append((path.resolve(strict=False), scope, priority))

    if selected_golden is not None and selected_golden.is_file():
        add_path(selected_golden, "golden", 1000)

    ordered_products = [product for product in [main_product, *supplementary] if product]
    for index, product in enumerate(ordered_products):
        product_dir_name = PRODUCT_DIRS.get(product)
        if product_dir_name is None:
            continue
        product_root = reference_root / product_dir_name
        scope = "main_product_history" if index == 0 and product == main_product else "supplementary_product_history"
        base_priority = 700 if scope == "main_product_history" else 500 - (index * 50)
        for case_file in sorted(product_root.rglob("测试用例*.md")):
            add_path(case_file, scope, base_priority)

    return sources


def tokenize(parts: Iterable[str]) -> list[str]:
    tokens: list[str] = []
    for part in parts:
        for token in TOKEN_RE.findall(part):
            lowered = token.lower()
            if lowered in STOPWORDS:
                continue
            tokens.append(token)
    return tokens


def parse_case_entries(path: Path, scope: str, priority: int) -> list[CaseEntry]:
    stack: list[str] = []
    entries: list[CaseEntry] = []
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        content = stripped[2:]
        if content.startswith(("描述：", "来源：", "承接：")):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        level = indent // 4
        while len(stack) > level:
            stack.pop()

        if content.startswith("[C] "):
            case_title = content[4:].strip()
            normalized = tokenize([*stack, case_title])
            entries.append(
                CaseEntry(
                    source_file=str(path.resolve(strict=False)),
                    path_tokens=list(stack),
                    case_title=case_title,
                    match_scope=scope,
                    priority=priority,
                    normalized_tokens=normalized,
                )
            )
            continue

        if len(stack) == level:
            stack.append(content)
        else:
            stack = stack[:level] + [content]
    return entries


def parse_step8_leaf_queries(path: Path) -> list[dict]:
    nodes: list[dict] = []
    stack_indexes: list[int] = []
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if not stripped.startswith("- "):
            continue
        content = stripped[2:]
        if content.startswith(("描述：", "来源：", "承接：")):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        level = indent // 4
        while len(stack_indexes) > level:
            stack_indexes.pop()
        parent_index = stack_indexes[-1] if stack_indexes else None
        nodes.append(
            {
                "title": content,
                "level": level,
                "parent_index": parent_index,
                "children": [],
            }
        )
        current_index = len(nodes) - 1
        if parent_index is not None:
            nodes[parent_index]["children"].append(current_index)
        if len(stack_indexes) == level:
            stack_indexes.append(current_index)
        else:
            stack_indexes = stack_indexes[:level] + [current_index]

    queries: list[dict] = []
    for index, node in enumerate(nodes):
        if node["children"]:
            continue
        path_tokens: list[str] = []
        current_index: Optional[int] = index
        while current_index is not None:
            current_node = nodes[current_index]
            path_tokens.append(current_node["title"])
            current_index = current_node["parent_index"]
        path_tokens.reverse()
        queries.append(
            {
                "leaf_title": node["title"],
                "path_tokens": path_tokens,
                "normalized_tokens": tokenize(path_tokens),
            }
        )
    return queries


def score_query_against_entry(query_tokens: list[str], query_leaf_title: str, entry: CaseEntry) -> float:
    query_token_set = set(query_tokens)
    entry_token_set = set(entry.normalized_tokens)
    overlap = len(query_token_set & entry_token_set)
    score = float(overlap)

    if entry.path_tokens:
        if entry.path_tokens[-1] == query_leaf_title:
            score += 5.0
        elif query_leaf_title in entry.case_title or entry.case_title in query_leaf_title:
            score += 3.0

    entry_path_set = set(entry.path_tokens)
    score += sum(2.0 for token in query_tokens if token in entry_path_set)
    score += entry.priority / 1000.0
    return score


def build_leaf_suggestions(queries: list[dict], title_bank: list[CaseEntry]) -> list[dict]:
    suggestions: list[dict] = []
    for query in queries:
        scored: list[tuple[float, CaseEntry]] = []
        for entry in title_bank:
            score = score_query_against_entry(query["normalized_tokens"], query["leaf_title"], entry)
            if score <= 0:
                continue
            scored.append((score, entry))
        scored.sort(key=lambda item: (-item[0], -item[1].priority, item[1].case_title))
        suggestions.append(
            {
                "leaf_title": query["leaf_title"],
                "path_tokens": query["path_tokens"],
                "candidates": [
                    {
                        "score": round(score, 3),
                        "source_file": entry.source_file,
                        "path_tokens": entry.path_tokens,
                        "case_title": entry.case_title,
                        "match_scope": entry.match_scope,
                        "priority": entry.priority,
                    }
                    for score, entry in scored[:8]
                ],
            }
        )
    return suggestions


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Step9 title bank from selected golden reference and historical testcase samples.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    step8_path = workdir / "step8_combination_expansion.md"
    if not step8_path.is_file():
        print(json.dumps({"ok": False, "error": f"step8 combination file not found: {step8_path}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    skill_root = Path(__file__).resolve().parent.parent
    selected_golden = resolve_selected_golden_path(workdir)
    main_product, supplementary = detect_products(workdir)
    history_sources = collect_history_case_files(skill_root, selected_golden, main_product, supplementary)

    title_bank: list[CaseEntry] = []
    for source_file, scope, priority in history_sources:
        title_bank.extend(parse_case_entries(source_file, scope, priority))

    queries = parse_step8_leaf_queries(step8_path)
    suggestions = build_leaf_suggestions(queries, title_bank)

    output = {
        "ok": True,
        "workdir": str(workdir),
        "selected_golden_path": str(selected_golden) if selected_golden is not None else "",
        "detected_products": {
            "main_product": main_product,
            "supplementary_products": supplementary,
        },
        "source_files": [
            {"path": str(path), "match_scope": scope, "priority": priority}
            for path, scope, priority in history_sources
        ],
        "title_bank": [
            {
                "source_file": entry.source_file,
                "path_tokens": entry.path_tokens,
                "case_title": entry.case_title,
                "match_scope": entry.match_scope,
                "priority": entry.priority,
            }
            for entry in title_bank
        ],
        "leaf_match_suggestions": suggestions,
    }

    output_path = workdir / "step9_title_bank.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output_path": str(output_path), "source_file_count": len(history_sources), "title_bank_count": len(title_bank), "leaf_query_count": len(queries)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
