#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import argparse
import json
import math
import re
import sys


FIGMA_DIR_NAMES = {"figma_top_level_sections", "figma_png"}
CASE_LINE_RE = re.compile(r"^\s*-\s*\[C\]\s+(.+?)\s*$")
SPLIT_SIGNAL_PATTERNS = [
    ("标题包含复合关键词", re.compile(r"同时|且|并且|反复|复合|批量|多个")),
    ("同时覆盖展示与校验", re.compile(r"展示.*校验|校验.*展示")),
    ("同时覆盖编辑与结果", re.compile(r"编辑.*(成功|失败|报错|结果)|(成功|失败|报错|结果).*编辑")),
    ("同时覆盖成功与失败", re.compile(r"成功.*失败|失败.*成功|成功.*报错|报错.*成功")),
    ("同时覆盖主备", re.compile(r"主.*备|备.*主")),
    ("同时覆盖客户端与服务端", re.compile(r"客户端.*服务端|服务端.*客户端|客户端/服务端")),
]
BYTES_PER_CASE = 12000
MAX_INTERNAL_ROUNDS = 5


def resolve_case_path(workdir: Path, raw_case_file: str) -> Path:
    raw_path = Path(raw_case_file).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve(strict=False)
    return (workdir / raw_path).resolve(strict=False)


def default_case_path(workdir: Path) -> Path:
    for candidate in ("step10_ui_cases_final.md", "step9_ui_cases_final.md"):
        path = workdir / candidate
        if path.is_file():
            return path.resolve(strict=False)
    return (workdir / "step9_ui_cases_final.md").resolve(strict=False)


def collect_figma_total_bytes(workdir: Path) -> tuple[int, list[str]]:
    figma_dirs: list[str] = []
    total_bytes = 0
    for path in sorted(workdir.rglob("*")):
        if not path.is_dir():
            continue
        if path.name not in FIGMA_DIR_NAMES:
            continue
        figma_dirs.append(str(path.resolve()))
        total_bytes += sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    return total_bytes, figma_dirs


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def collect_case_titles(path: Path) -> list[str]:
    titles: list[str] = []
    for line in read_text(path).splitlines():
        match = CASE_LINE_RE.match(line)
        if match:
            titles.append(match.group(1).strip())
    return titles


def collect_split_signals(case_titles: list[str]) -> tuple[list[dict], int]:
    findings: list[dict] = []
    for title in case_titles:
        reasons = [label for label, pattern in SPLIT_SIGNAL_PATTERNS if pattern.search(title)]
        if reasons:
            findings.append({"case_title": title, "signals": reasons})
    return findings[:50], len(findings)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate Step10 case splitting by figma size and composite-case signals.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    parser.add_argument("--case-file", default="", help="Optional case file path; defaults to step10_ui_cases_final.md or step9_ui_cases_final.md")
    parser.add_argument("--round-index", type=int, default=1, help="Current Step10 round index, 1-based")
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(json.dumps({"ok": False, "error": f"workdir not found: {workdir}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    case_path = resolve_case_path(workdir, args.case_file) if args.case_file else default_case_path(workdir)
    if not case_path.is_file():
        print(json.dumps({"ok": False, "error": f"case file not found: {case_path}"}, ensure_ascii=False, indent=2))
        sys.exit(1)

    case_titles = collect_case_titles(case_path)
    current_case_count = len(case_titles)
    split_signal_examples, split_signal_count = collect_split_signals(case_titles)
    figma_total_bytes, figma_dirs = collect_figma_total_bytes(workdir)
    numeric_gate_skipped = figma_total_bytes == 0
    target_min_case_count = None if numeric_gate_skipped else int(math.ceil(figma_total_bytes / BYTES_PER_CASE))
    count_gap = 0 if target_min_case_count is None else max(target_min_case_count - current_case_count, 0)

    needs_more_split = split_signal_count > 0 or (target_min_case_count is not None and current_case_count < target_min_case_count)
    internal_limit_reached = False
    if needs_more_split and args.round_index > MAX_INTERNAL_ROUNDS:
        needs_more_split = False
        internal_limit_reached = True

    output = {
        "ok": True,
        "workdir": str(workdir),
        "case_file": str(case_path),
        "round_index": args.round_index,
        "figma_dirs": figma_dirs,
        "figma_total_bytes": figma_total_bytes,
        "target_min_case_count": target_min_case_count,
        "current_case_count": current_case_count,
        "count_gap": count_gap,
        "numeric_gate_skipped": numeric_gate_skipped,
        "split_signal_count": split_signal_count,
        "split_signal_examples": split_signal_examples,
        "needs_more_split": needs_more_split,
        "internal_limit_reached": internal_limit_reached,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
