#!/usr/bin/env python3

from pathlib import Path
import json
import sys

MARKDOWN_SUFFIXES = {".md", ".markdown"}


def as_list(data, key):
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def scan_path(raw_path):
    path = Path(raw_path).expanduser()
    record = {
        "input": raw_path,
        "resolved_path": str(path),
        "kind": "missing",
        "exists": False,
        "used_files": [],
    }
    if path.is_dir():
        record["kind"] = "directory"
        record["exists"] = True
        record["used_files"] = [
            str(item.relative_to(path))
            for item in sorted(path.rglob("*"))
            if item.is_file() and item.suffix.lower() in MARKDOWN_SUFFIXES
        ]
    elif path.is_file():
        record["kind"] = "file"
        record["exists"] = True
        record["used_files"] = [str(path)]
    return record


def confirmation_rule(data):
    has_google = bool(data["google doc url"])
    has_uploaded = bool(data["uploaded files by agent"])
    has_figma = bool(data["figma url"])
    has_user_dir = bool(data["user file directory"])
    if not (has_google or has_uploaded or has_figma or has_user_dir):
        return {
            "type": 0,
            "title": "当前没有可处理资料",
            "message": "四类输入都为空，请至少补充一种输入后再继续。",
        }
    if has_figma and not (has_google or has_uploaded or has_user_dir):
        return {
            "type": 1,
            "title": "仅收到 Figma 链接",
            "message": "是否需要补充上传该 Figma 对应 feature 的需求文件？",
        }
    if not has_figma:
        return {
            "type": 2,
            "title": "缺少 Figma 设计稿",
            "message": "当前没有 Figma 链接，是否需要补充上传该 feature 相关的 Figma 设计稿？",
        }
    return {
        "type": 3,
        "title": "已有 Figma 与其他资料",
        "message": "请确认本次拟使用的 Figma、目录和文件清单是否全部纳入，或指出要排除的文件。",
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python inspect_input_manifest.py <input_manifest.json>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1]).expanduser()
    if not manifest_path.is_file():
        print(f"input manifest not found: {manifest_path}")
        sys.exit(1)

    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    summary = {
        "google doc url": as_list(data, "google doc url"),
        "uploaded files by agent": as_list(data, "uploaded files by agent"),
        "figma url": as_list(data, "figma url"),
        "user file directory": [
            scan_path(item) for item in as_list(data, "user file directory")
        ],
    }
    summary["confirmation"] = confirmation_rule(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
