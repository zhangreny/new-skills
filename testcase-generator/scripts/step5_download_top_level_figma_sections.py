#!/usr/bin/env python3

'''
**脚本行为**：
- 脚本会读取 `input_manifest.json` 中的 `figma_url`
- 脚本优先使用环境变量 `FIGMA_PAT` / `FIGMA_TOKEN`；如果都不存在，则回退读取 `scripts/step5_figma_token.md` 中的 token
- 如果 Figma 链接中的目标 node 本身是可见 `SECTION`，则直接下载该 `SECTION`
- 否则优先下载目标 node 下所有可见的直接子 `SECTION`
- 如果没有可见的直接子 `SECTION`，则回退下载目标 node 下所有可见的直接子 `FRAME`
- 下载得到的 png 文件统一保存到 `<workdir>/figma_top_level_sections`
'''

from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen
import json
import os
import re
import sys


API_BASE = "https://api.figma.com/v1"
TOKEN_FILE = Path(__file__).with_name("step5_figma_token.md")
OUTPUT_DIRNAME = "figma_top_level_sections"
SECTION_SCALE = "2"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def load_token() -> str:
    for env_key in ("FIGMA_PAT", "FIGMA_TOKEN"):
        value = os.environ.get(env_key, "").strip()
        if value:
            return value
    if TOKEN_FILE.is_file():
        value = TOKEN_FILE.read_text(encoding="utf-8", errors="ignore").strip()
        if value:
            return value
    raise RuntimeError("missing Figma token: set FIGMA_PAT/FIGMA_TOKEN or fill scripts/step5_figma_token.md")


def slugify(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", " ", name)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned[:80] or "section"


def parse_figma_url(url: str) -> dict[str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or "figma.com" not in parsed.netloc:
        raise ValueError(f"unsupported Figma URL: {url}")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"failed to extract file key from URL: {url}")

    file_key = ""
    if parts[0] in {"design", "file", "board", "make"} and len(parts) >= 2:
        file_key = parts[1]
    if "branch" in parts:
        branch_index = parts.index("branch")
        if branch_index + 1 < len(parts):
            file_key = parts[branch_index + 1]
    if not file_key:
        raise ValueError(f"failed to extract file key from URL: {url}")

    query = parse_qs(parsed.query)
    raw_node_id = (query.get("node-id", [""]) or [""])[0].strip()
    if not raw_node_id:
        raw_node_id = "0:1"
    node_id = raw_node_id.replace("-", ":")

    return {
        "url": url,
        "file_key": file_key,
        "node_id": node_id,
    }


def figma_get_json(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "X-Figma-Token": token,
            "User-Agent": "testcase-generator-step5/1.0",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"HTTP {exc.code} for {url}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"request failed for {url}: {exc.reason}") from exc


def download_binary(url: str, target: Path) -> None:
    request = Request(url, headers={"User-Agent": "testcase-generator-step5/1.0"})
    try:
        with urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"HTTP {exc.code} while downloading image: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"image download failed: {exc.reason}") from exc


def fetch_root_document(file_key: str, node_id: str, token: str) -> dict:
    query = urlencode({"ids": node_id, "depth": "2"})
    payload = figma_get_json(f"{API_BASE}/files/{quote(file_key)}/nodes?{query}", token)
    node_payload = (payload.get("nodes") or {}).get(node_id) or {}
    document = node_payload.get("document")
    if not document:
        raise RuntimeError(f"node not found in Figma response: {node_id}")
    return document


def is_visible(node: dict) -> bool:
    return node.get("visible", True) is not False


def select_top_level_business_nodes(root: dict) -> tuple[list[dict], str]:
    root_type = str(root.get("type", "")).upper()
    if root_type == "SECTION" and is_visible(root):
        return [root], "target node is a visible SECTION, export it directly"

    children = [child for child in root.get("children", []) if isinstance(child, dict) and is_visible(child)]
    sections = [child for child in children if str(child.get("type", "")).upper() == "SECTION"]
    if sections:
        return sections, "export visible direct SECTION children under the selected node"

    frames = [child for child in children if str(child.get("type", "")).upper() == "FRAME"]
    if frames:
        return frames, "no SECTION child found, fallback to visible direct FRAME children"

    if is_visible(root):
        return [root], "no visible SECTION/FRAME child found, fallback to the selected node itself"
    return [], "selected node is hidden and has no visible SECTION/FRAME child"


def fetch_image_urls(file_key: str, node_ids: list[str], token: str) -> dict[str, str]:
    if not node_ids:
        return {}
    query = urlencode(
        {
            "ids": ",".join(node_ids),
            "format": "png",
            "scale": SECTION_SCALE,
        }
    )
    payload = figma_get_json(f"{API_BASE}/images/{quote(file_key)}?{query}", token)
    return {key: value for key, value in (payload.get("images") or {}).items() if value}


def export_one_url(entry: dict[str, str], target_dir: Path, token: str) -> dict:
    root = fetch_root_document(entry["file_key"], entry["node_id"], token)
    nodes, selection_rule = select_top_level_business_nodes(root)
    if not nodes:
        return {
            "source_url": entry["url"],
            "file_key": entry["file_key"],
            "target_node_id": entry["node_id"],
            "selection_rule": selection_rule,
            "downloaded": [],
            "failed": [{"error": "no exportable top-level business section found"}],
        }

    image_urls = fetch_image_urls(entry["file_key"], [str(node.get("id", "")) for node in nodes], token)
    downloaded: list[dict] = []
    failed: list[dict] = []

    for index, node in enumerate(nodes, start=1):
        section_id = str(node.get("id", "")).strip()
        section_name = str(node.get("name", "")).strip() or f"section_{index}"
        image_url = image_urls.get(section_id, "")
        if not image_url:
            failed.append(
                {
                    "section_node_id": section_id,
                    "section_name": section_name,
                    "error": "Figma did not return an image URL for this section",
                }
            )
            continue

        filename = f"{index:02d}_{slugify(section_name)}_{section_id.replace(':', '-')}.png"
        output_path = target_dir / filename
        try:
            download_binary(image_url, output_path)
        except Exception as exc:  # noqa: BLE001
            failed.append(
                {
                    "section_node_id": section_id,
                    "section_name": section_name,
                    "error": str(exc),
                }
            )
            continue

        downloaded.append(
            {
                "section_node_id": section_id,
                "section_name": section_name,
                "png_path": str(output_path),
                "png_file_name": filename,
            }
        )

    return {
        "source_url": entry["url"],
        "file_key": entry["file_key"],
        "target_node_id": entry["node_id"],
        "selection_rule": selection_rule,
        "downloaded": downloaded,
        "failed": failed,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/step5_download_top_level_figma_sections.py <workdir>")
        sys.exit(1)

    workdir = Path(sys.argv[1]).expanduser().resolve(strict=False)
    manifest_path = workdir / "input_manifest.json"
    if not manifest_path.is_file():
        print(f"input manifest not found: {manifest_path}")
        sys.exit(1)

    manifest = read_json(manifest_path)
    figma_urls = as_list(manifest, "figma_url")
    token = load_token()

    output_dir = workdir / OUTPUT_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[dict] = []
    failed: list[dict] = []
    skipped: list[dict] = []

    for url in figma_urls:
        try:
            parsed = parse_figma_url(url)
            result = export_one_url(parsed, output_dir, token)
            if result["downloaded"]:
                downloaded.append(result)
            if result["failed"]:
                failed.append(result)
            if not result["downloaded"] and not result["failed"]:
                skipped.append(result)
        except Exception as exc:  # noqa: BLE001
            failed.append(
                {
                    "source_url": url,
                    "error": str(exc),
                }
            )

    output = {
        "workdir": str(workdir),
        "input_manifest": str(manifest_path),
        "figma_url": figma_urls,
        "output_dir": str(output_dir),
        "downloaded": downloaded,
        "skipped": skipped,
        "download_failed": failed,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
