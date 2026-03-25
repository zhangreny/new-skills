#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import json
import sys


def as_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/step5_check_figma_url_whether_blank.py <input_manifest.json>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1]).expanduser().resolve(strict=False)
    if not manifest_path.is_file():
        print(f"input manifest not found: {manifest_path}")
        sys.exit(1)

    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    figma_urls = as_list(data, "figma_url")
    is_empty = len(figma_urls) == 0

    print(
        json.dumps(
            {
                "input_manifest": str(manifest_path),
                "figma_url": figma_urls,
                "figma_url_is_empty": is_empty,
                "should_try_download_top_level_sections_png": not is_empty,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
