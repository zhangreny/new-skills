#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import json
import os

MANIFEST = {
    "google doc url": [],
    "uploaded files by agent": [],
    "figma url": [],
    "user file directory": [],
}


def downloads_dir():
    home = Path.home()
    if os.name != "nt":
        config = home / ".config" / "user-dirs.dirs"
        if config.exists():
            for line in config.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("XDG_DOWNLOAD_DIR="):
                    value = line.split("=", 1)[1].strip().strip('"')
                    return Path(value.replace("$HOME", str(home))).expanduser()
    return home / "Downloads"


target = downloads_dir()
target.mkdir(parents=True, exist_ok=True)
workdir = target / f"testcase-generate-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
workdir.mkdir(parents=True, exist_ok=False)
(workdir / "input-manifest.json").write_text(
    json.dumps(MANIFEST, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "workdir": str(workdir),
            "input_manifest": str(workdir / "input-manifest.json"),
        },
        ensure_ascii=False,
    )
)
