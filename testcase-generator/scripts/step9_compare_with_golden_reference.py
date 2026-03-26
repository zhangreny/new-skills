#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
from typing import Optional


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def parse_case_tree(path: Path, depth: int = 4) -> dict:
    stack: list[str] = []
    clusters: dict[str, int] = {}
    case_count = 0

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
            case_count += 1
            if stack:
                slice_parts = stack[:depth]
                key = " | ".join(slice_parts)
                clusters[key] = clusters.get(key, 0) + 1
            continue

        if len(stack) == level:
            stack.append(content)
        else:
            stack = stack[:level] + [content]

    return {"case_count": case_count, "clusters": clusters}


def resolve_selected_golden_path(workdir: Path) -> Optional[Path]:
    candidate_files = [
        workdir / "step6_product_context.md",
        workdir / "step7_test_blueprint.md",
    ]
    path_patterns = [
        re.compile(r"([A-Za-z]:\\[^`\n]+?\.md)"),
        re.compile(r"(references[\\/][^`\n]+?\.md)"),
    ]
    for file_path in candidate_files:
        if not file_path.is_file():
            continue
        text = read_text(file_path)
        for line in text.splitlines():
            if "已采用黄金参考" not in line:
                continue
            for pattern in path_patterns:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare generated testcase output with the selected golden reference.")
    parser.add_argument("workdir", help="Workdir created by testcase-generator")
    parser.add_argument(
        "--golden-path",
        default="",
        help="Optional override for the golden testcase markdown file",
    )
    args = parser.parse_args()

    workdir = Path(args.workdir).expanduser().resolve(strict=False)
    generated_path = workdir / "step9_ui_cases_final.md"
    if not generated_path.is_file():
        print(json.dumps({"ok": False, "error": f"generated final case file not found: {generated_path}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    if args.golden_path:
        golden_path: Optional[Path] = Path(args.golden_path).expanduser().resolve(strict=False)
    else:
        golden_path = resolve_selected_golden_path(workdir)

    if golden_path is None:
        print(
            json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "no golden reference selected in step6_product_context.md or step7_test_blueprint.md, and --golden-path was not provided",
                    "generated_file": str(generated_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not golden_path.is_file():
        print(json.dumps({"ok": False, "error": f"golden testcase file not found: {golden_path}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    generated = parse_case_tree(generated_path)
    golden = parse_case_tree(golden_path)

    generated_top = sorted(generated["clusters"].items(), key=lambda item: (-item[1], item[0]))[:20]
    golden_top = sorted(golden["clusters"].items(), key=lambda item: (-item[1], item[0]))[:20]

    missing = [cluster for cluster, _count in golden_top if cluster not in generated["clusters"]]

    output = {
        "generated_file": str(generated_path),
        "golden_file": str(golden_path),
        "generated_case_count": generated["case_count"],
        "golden_case_count": golden["case_count"],
        "case_count_delta": generated["case_count"] - golden["case_count"],
        "relative_ratio": round(generated["case_count"] / golden["case_count"], 4) if golden["case_count"] else None,
        "within_default_relative_range": (
            bool(golden["case_count"]) and 0.8 <= (generated["case_count"] / golden["case_count"]) <= 1.2
        ),
        "generated_top_clusters": [{"cluster": cluster, "count": count} for cluster, count in generated_top],
        "golden_top_clusters": [{"cluster": cluster, "count": count} for cluster, count in golden_top],
        "missing_high_value_clusters": missing,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
