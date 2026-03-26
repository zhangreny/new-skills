#!/usr/bin/env python3

import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import json
import sys
import time
from urllib.parse import parse_qs, urlparse

try:
    import pty
except ModuleNotFoundError:
    pty = None


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
URL_INPUT_FILENAMES = ("download_googledoc_url", "download_googledoc_url.txt")


def extract_file_id(url: str) -> str:
    parsed = urlparse(url.strip())
    file_id = parse_qs(parsed.query).get("id", [""])[0].strip()
    if file_id:
        return file_id
    parts = [part for part in parsed.path.split("/") if part]
    return parts[parts.index("d") + 1].strip() if "d" in parts and parts.index("d") + 1 < len(parts) else ""


def run_gog(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    resolved_cmd = cmd[:]
    gog_executable = shutil.which(cmd[0])
    if gog_executable:
        resolved_cmd[0] = gog_executable

    if pty is None:
        try:
            proc = subprocess.run(
                resolved_cmd,
                input=b"\n\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            output = (proc.stdout + proc.stderr).decode("utf-8", errors="replace").strip()
            return proc.returncode, output
        except subprocess.TimeoutExpired:
            return -1, "timeout"

    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(resolved_cmd, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        slave = None
        time.sleep(0.1)
        os.write(master, b"\n\n")
        chunks = []
        deadline = time.monotonic() + timeout
        while True:
            ready, _, _ = select.select([master], [], [], max(0.01, deadline - time.monotonic()))
            if not ready:
                proc.kill()
                proc.wait()
                return proc.returncode or -1, "timeout"
            try:
                buf = os.read(master, 4096)
            except OSError:
                break
            if not buf:
                break
            chunks.append(buf)
            if proc.poll() is not None:
                break
        proc.wait()
        return proc.returncode or 0, b"".join(chunks).decode("utf-8", errors="replace").strip()
    finally:
        if slave is not None:
            try:
                os.close(slave)
            except OSError:
                pass
        try:
            os.close(master)
        except OSError:
            pass


def looks_like_base64(line: str) -> bool:
    line = line.strip()
    return len(line) >= 80 and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for ch in line)


def clean_markdown(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = DATA_URI_MARKDOWN_RE.sub("", original)
    text = DATA_URI_HTML_RE.sub("", text)
    text = DATA_URI_BARE_RE.sub("", text)
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and (lines[-1].strip().startswith("data:image/") or looks_like_base64(lines[-1])):
        lines.pop()
        while lines and (not lines[-1].strip() or lines[-1].strip().startswith(("![", "<img"))):
            lines.pop()
    cleaned = "\n".join(lines)
    if cleaned and text.endswith(("\n", "\r")):
        cleaned += "\n"
    if cleaned == original:
        return False
    path.write_text(cleaned, encoding="utf-8")
    return True


def get_unique_path(target: Path) -> Path:
    if not target.exists():
        return target

    counter = 2
    while True:
        candidate = target.with_name(f"{target.stem} ({counter}){target.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def rename_downloaded_files(directory: Path, file_id: str) -> list[dict[str, str]]:
    renamed: list[dict[str, str]] = []
    prefix = f"{file_id}_"
    for path in sorted(list(directory.glob(f"{prefix}*.md")) + list(directory.glob(f"{prefix}*.markdown"))):
        new_name = path.name[len(prefix):].strip()
        if not new_name:
            continue
        target = get_unique_path(path.with_name(new_name))
        if target != path:
            path.rename(target)
            renamed.append({"from": path.name, "to": target.name})
    return renamed


def read_google_doc_urls(input_path: Path) -> list[str]:
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    urls: list[str] = []
    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line.strip("\"'"))

    if not urls:
        raise SystemExit(f"No valid Google Doc URLs found in {input_path}")
    return urls


def resolve_input_path(script_dir: Path) -> Path:
    for filename in URL_INPUT_FILENAMES:
        candidate = script_dir / filename
        if candidate.exists():
            return candidate
    raise SystemExit(f"Input file not found. Expected one of: {', '.join(URL_INPUT_FILENAMES)}")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    input_path = resolve_input_path(script_dir)
    directory = script_dir
    urls = read_google_doc_urls(input_path)

    downloaded = []
    failed = []
    for url in urls:
        file_id = extract_file_id(url)
        if not file_id:
            failed.append({"url": url, "error": "failed to extract Google file ID"})
            continue
        code, output = run_gog(["gog", "drive", "download", file_id, "--output", str(directory), "--format", "md"])
        if code != 0:
            failed.append({"url": url, "file_id": file_id, "error": output or f"exit code {code}"})
            continue
        renamed_files = rename_downloaded_files(directory, file_id)
        downloaded.append({"url": url, "file_id": file_id, "renamed_files": renamed_files})

    cleaned = 0
    for path in list(directory.glob("*.md")) + list(directory.glob("*.markdown")):
        if clean_markdown(path):
            cleaned += 1

    print(
        json.dumps(
            {
                "directory": str(directory),
                "downloaded": downloaded,
                "download_failed": failed,
                "cleaned_markdown_files": cleaned,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
