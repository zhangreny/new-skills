#!/usr/bin/env python3
"""Export a TestRail subsection tree and its cases to an indented Markdown file.

The script reads the target subsection URL from `download_testrail_url.txt`
located next to this script.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import requests
from requests.auth import HTTPBasicAuth

DEFAULT_TESTRAIL_USER = "renyu.zhang@smartx.com"
DEFAULT_TESTRAIL_API_KEY = "Zhangry-2001"
DEFAULT_TIMEOUT = 30
PAGE_SIZE = 250
INDENT = " " * 4
URL_INPUT_FILENAME = "download_testrail_url.txt"
WINDOWS_RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


@dataclass
class TestRailClient:
    base_url: str
    user: str
    api_key: str
    timeout: int = DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.user, self.api_key)
        self.session.headers.update({"Content-Type": "application/json"})

    def _api_url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/index.php?/api/v2/{path}"

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:
        response = self.session.get(self._api_url(path), params=params or {}, timeout=self.timeout)
        if response.status_code != 200:
            raise RuntimeError(f"TestRail GET failed: {response.status_code} {response.text[:300]}")
        response.encoding = "utf-8"
        return response.json()

    def get_suite(self, suite_id: int) -> dict[str, Any]:
        result = self.get(f"get_suite/{suite_id}")
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected suite payload for suite {suite_id}: {type(result)!r}")
        return result

    def get_section(self, section_id: int) -> dict[str, Any]:
        result = self.get(f"get_section/{section_id}")
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected section payload for section {section_id}: {type(result)!r}")
        return result

    def get_sections(self, project_id: int, suite_id: int) -> list[dict[str, Any]]:
        result = self.get(f"get_sections/{project_id}&suite_id={suite_id}")
        if not isinstance(result, list):
            raise RuntimeError(f"Unexpected sections payload for suite {suite_id}: {type(result)!r}")
        return result

    def get_cases(self, project_id: int, suite_id: int, section_id: int) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        offset = 0
        while True:
            path = f"get_cases/{project_id}&suite_id={suite_id}&section_id={section_id}&limit={PAGE_SIZE}&offset={offset}"
            result = self.get(path)
            if not isinstance(result, list):
                raise RuntimeError(f"Unexpected cases payload for section {section_id}: {type(result)!r}")
            cases.extend(result)
            if len(result) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
        return cases


def parse_testrail_subsection_url(url: str) -> tuple[str, int, int]:
    suite_match = re.search(r"/suites/view/(\d+)", url)
    if not suite_match:
        raise SystemExit("Could not parse `suite_id` from the TestRail URL. Expecting `/suites/view/<suite_id>`.")

    section_match = re.search(r"(?:[?&]|^)group_id=(\d+)", url)
    if not section_match:
        raise SystemExit("Could not parse `group_id` from the TestRail URL in download_testrail_url.txt.")

    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise SystemExit("The TestRail URL is invalid. Please provide the full URL, including `http://`.")

    base_url = f"{parsed.scheme}://{parsed.netloc}"
    suite_id = int(suite_match.group(1))
    section_id = int(section_match.group(1))
    return base_url, suite_id, section_id


def read_testrail_url(input_path: Path) -> str:
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        return line.strip("\"'")

    raise SystemExit(f"No valid TestRail URL found in {input_path}")


def sanitize_filename(name: str, fallback: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    cleaned = cleaned.rstrip(" .")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        cleaned = fallback
    if cleaned.upper() in WINDOWS_RESERVED_FILENAMES:
        cleaned = f"{cleaned}_"
    return cleaned


def build_children_map(sections: list[dict[str, Any]]) -> dict[int | None, list[dict[str, Any]]]:
    by_parent: dict[int | None, list[dict[str, Any]]] = {}
    for section in sections:
        by_parent.setdefault(section.get("parent_id"), []).append(section)
    for siblings in by_parent.values():
        siblings.sort(key=lambda item: (int(item.get("display_order") or 0), int(item.get("id") or 0)))
    return by_parent


def collect_subtree_ids(root_id: int, by_parent: dict[int | None, list[dict[str, Any]]]) -> set[int]:
    result: set[int] = set()

    def visit(section_id: int) -> None:
        result.add(section_id)
        for child in by_parent.get(section_id, []):
            visit(int(child["id"]))

    visit(root_id)
    return result


def render_markdown_lines(
    root_section: dict[str, Any],
    by_parent: dict[int | None, list[dict[str, Any]]],
    cases_by_section: dict[int, list[dict[str, Any]]],
    level: int = 0,
) -> list[str]:
    indent = INDENT * level
    section_title = (root_section.get("name") or "").strip() or f"Section {root_section['id']}"
    lines = [f"{indent}- {section_title}"]

    section_id = int(root_section["id"])
    for case_item in cases_by_section.get(section_id, []):
        case_indent = INDENT * (level + 1)
        case_title = (case_item.get("title") or "").strip() or f"Case {case_item.get('id')}"
        lines.append(f"{case_indent}- [C] {case_title}")

    for child in by_parent.get(section_id, []):
        lines.extend(render_markdown_lines(child, by_parent, cases_by_section, level + 1))

    return lines


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    input_path = script_dir / URL_INPUT_FILENAME
    url = read_testrail_url(input_path)

    base_url, suite_id, section_id = parse_testrail_subsection_url(url)
    client = TestRailClient(base_url=base_url, user=DEFAULT_TESTRAIL_USER, api_key=DEFAULT_TESTRAIL_API_KEY)

    suite = client.get_suite(suite_id)
    project_id = int(suite["project_id"])
    sections = client.get_sections(project_id=project_id, suite_id=suite_id)
    sections_by_id = {int(section["id"]): section for section in sections}
    if section_id not in sections_by_id:
        section = client.get_section(section_id)
        if int(section["suite_id"]) != suite_id:
            raise SystemExit(f"Section {section_id} belongs to suite {section['suite_id']}, not suite {suite_id}.")
        sections.append(section)
        sections_by_id[int(section["id"])] = section

    root_section = sections_by_id[section_id]
    by_parent = build_children_map(sections)
    subtree_ids = collect_subtree_ids(section_id, by_parent)

    cases_by_section: dict[int, list[dict[str, Any]]] = {}
    total_cases = 0
    for current_section_id in sorted(subtree_ids):
        raw_cases = client.get_cases(project_id=project_id, suite_id=suite_id, section_id=current_section_id)
        filtered_cases = [
            case_item
            for case_item in raw_cases
            if int(case_item.get("is_deleted") or 0) == 0
        ]
        filtered_cases.sort(key=lambda item: (int(item.get("display_order") or 0), int(item.get("id") or 0)))
        if filtered_cases:
            cases_by_section[current_section_id] = filtered_cases
            total_cases += len(filtered_cases)

    lines = render_markdown_lines(root_section=root_section, by_parent=by_parent, cases_by_section=cases_by_section)
    content = "\n".join(lines).rstrip() + "\n"

    section_title = (root_section.get("name") or "").strip()
    output_filename = sanitize_filename(
        f"测试用例-{section_title}" if section_title else "",
        fallback=f"testrail_suite_{suite_id}_section_{section_id}",
    )
    output_path = Path(__file__).resolve().with_name(f"{output_filename}.md")
    output_path.write_text(content, encoding="utf-8")

    display_name = output_path.name
    escaped_name = display_name.encode("unicode_escape").decode("ascii")
    print(f"Exported {total_cases} case(s) from section {section_id} to {output_path}")
    if escaped_name != display_name:
        print(f"Filename (unicode): {escaped_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
