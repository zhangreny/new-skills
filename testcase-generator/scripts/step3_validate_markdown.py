#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

MARKDOWN_SUFFIXES = {
    ".md",
    ".markdown",
    ".mdown",
    ".mkd",
    ".mkdn",
    ".mdx",
}

DATA_URI_MARKDOWN_RE = re.compile(
    r"!\[[^\]]*]\(\s*data:image\/[\w.+-]+;base64,[^)]+\s*\)",
    flags=re.IGNORECASE | re.DOTALL,
)
DATA_URI_HTML_RE = re.compile(
    r"<img\b[^>]*\bsrc=(['\"])data:image\/[\w.+-]+;base64,.*?\1[^>]*>",
    flags=re.IGNORECASE | re.DOTALL,
)
DATA_URI_BARE_RE = re.compile(
    r"data:image\/[\w.+-]+;base64,[A-Za-z0-9+/=\s]+",
    flags=re.IGNORECASE,
)


def as_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def resolve_input_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(strict=False)


def is_markdown_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in MARKDOWN_SUFFIXES


def read_text_with_fallback(path: Path) -> str:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return path.read_text(encoding="utf-8")


def looks_like_base64_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 80:
        return False
    return all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for ch in stripped)


def strip_trailing_base64_block(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text

    original_had_trailing_newline = text.endswith(("\n", "\r"))

    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    block_start = len(lines)
    saw_data_uri = False
    base64_chars = 0

    index = len(lines) - 1
    while index >= 0:
        stripped = lines[index].strip()
        if not stripped:
            if block_start < len(lines):
                block_start = index
                index -= 1
                continue
            break
        if stripped.startswith("data:image/"):
            saw_data_uri = True
            base64_chars += len(stripped)
            block_start = index
            index -= 1
            continue
        if looks_like_base64_line(stripped):
            base64_chars += len(stripped)
            block_start = index
            index -= 1
            continue
        if block_start < len(lines) and stripped.startswith(("![", "<img")):
            block_start = index
        break

    if block_start < len(lines) and (saw_data_uri or base64_chars >= 512):
        lines = lines[:block_start]

    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return ""

    cleaned = "\n".join(lines)
    if original_had_trailing_newline:
        cleaned += "\n"
    return cleaned


def sanitize_markdown(text: str) -> str:
    cleaned = DATA_URI_MARKDOWN_RE.sub("", text)
    cleaned = DATA_URI_HTML_RE.sub("", cleaned)
    cleaned = DATA_URI_BARE_RE.sub("", cleaned)
    return strip_trailing_base64_block(cleaned)


def expand_markdown_inputs(entries: list[str], base_dir: Path) -> tuple[list[str], dict]:
    collected: list[str] = []
    seen: set[str] = set()
    stats = {
        "cleaned_files": 0,
        "kept_files": 0,
        "skipped_missing": [],
        "skipped_non_markdown": [],
    }

    for raw_entry in entries:
        path = resolve_input_path(raw_entry, base_dir)

        if path.is_dir():
            markdown_files = sorted(item for item in path.rglob("*") if is_markdown_file(item))
            if not markdown_files:
                stats["skipped_non_markdown"].append(str(path))
                continue
            for item in markdown_files:
                key = str(item)
                if key not in seen:
                    sanitize_file(item, stats)
                    seen.add(key)
                    collected.append(key)
            continue

        if is_markdown_file(path):
            key = str(path)
            if key not in seen:
                sanitize_file(path, stats)
                seen.add(key)
                collected.append(key)
            continue

        if path.exists():
            stats["skipped_non_markdown"].append(str(path))
        else:
            stats["skipped_missing"].append(str(path))

    stats["kept_files"] = len(collected)
    return collected, stats


def sanitize_file(path: Path, stats: dict) -> None:
    original = read_text_with_fallback(path)
    cleaned = sanitize_markdown(original)
    if cleaned != original:
        path.write_text(cleaned, encoding="utf-8")
        stats["cleaned_files"] += 1


def build_user_confirmation_message(data: dict) -> str:
    google_doc_urls = as_list(data, "google doc url")
    uploaded_files = as_list(data, "uploaded files by agent")
    figma_urls = as_list(data, "figma url")
    user_files = as_list(data, "user file directory")

    has_figma = bool(figma_urls)
    has_other_inputs = bool(google_doc_urls or uploaded_files or user_files)

    if not has_figma and not has_other_inputs:
        return "当前没有有效的输入内容，请上传文件并提供设计稿链接"
    if has_figma and not has_other_inputs:
        return "是否需要上传需求文档，有助于 AI 更好的解析设计稿内容，并生成功能相关测试用例"
    if not has_figma:
        return "是否需要上传 figma 设计稿链接，有助于 AI 更好理解功能并生成配套前端测试用例"
    return "请确认当前输入内容，确认后将继续下一步"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/step3_validate_markdown.py <input-manifest.json>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1]).expanduser().resolve(strict=False)
    if not manifest_path.is_file():
        print(f"input manifest not found: {manifest_path}")
        sys.exit(1)

    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    base_dir = manifest_path.parent

    uploaded_files, uploaded_stats = expand_markdown_inputs(
        as_list(data, "uploaded files by agent"),
        base_dir,
    )
    user_files, user_stats = expand_markdown_inputs(
        as_list(data, "user file directory"),
        base_dir,
    )

    data["uploaded files by agent"] = uploaded_files
    data["user file directory"] = user_files
    user_confirmation_message = build_user_confirmation_message(data)

    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "input-manifest": str(manifest_path),
                "uploaded files by agent": uploaded_files,
                "user file directory": user_files,
                "stats": {
                    "uploaded files by agent": uploaded_stats,
                    "user file directory": user_stats,
                },
                "user confirmation message": user_confirmation_message,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
