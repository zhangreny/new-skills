#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import json
import sys


MARKDOWN_SUFFIXES = {".md", ".markdown"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".svg"}
IGNORED_FILE_NAMES = {
    "input_manifest.json",
}
GENERATED_OUTPUT_FILE_NAMES = {
    "step6_subagent_a_ui_cases.md",
    "step6_subagent_b_ui_cases.md",
    "step7_ui_cases_merged.md",
    "step8_ui_cases_review.md",
    "step8_ui_cases_final.md",
}


def collect_files(root: Path, suffixes: set[str]) -> tuple[list[str], list[str]]:
    files: list[str] = []
    ignored_generated_files: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in GENERATED_OUTPUT_FILE_NAMES:
            ignored_generated_files.append(str(path.resolve()))
            continue
        if path.name in IGNORED_FILE_NAMES:
            continue
        if path.suffix.lower() not in suffixes:
            continue
        files.append(str(path.resolve()))
    return files, ignored_generated_files


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/step6_collect_materials.py <workdir>")
        sys.exit(1)

    workdir = Path(sys.argv[1]).expanduser().resolve(strict=False)
    if not workdir.is_dir():
        print(f"workdir not found: {workdir}")
        sys.exit(1)

    markdown_files, ignored_markdown_outputs = collect_files(workdir, MARKDOWN_SUFFIXES)
    image_files, ignored_image_outputs = collect_files(workdir, IMAGE_SUFFIXES)
    ignored_generated_files = sorted(set(ignored_markdown_outputs + ignored_image_outputs))

    print(
        json.dumps(
            {
                "workdir": str(workdir),
                "markdown_files": markdown_files,
                "image_files": image_files,
                "ignored_generated_files": ignored_generated_files,
                "markdown_count": len(markdown_files),
                "image_count": len(image_files),
                "total_material_count": len(markdown_files) + len(image_files),
                "should_spawn_two_subagents": bool(markdown_files or image_files),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
