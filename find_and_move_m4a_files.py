#!/usr/bin/env python3

import shutil
import subprocess
from pathlib import Path

source_dir = Path.home() / "Downloads" / "duplicates"
target_dir = source_dir / "m4a"
target_dir.mkdir(parents=True, exist_ok=True)

for path in source_dir.iterdir():
    if not path.is_file():
        continue

    if path.suffix:
        continue

    result = subprocess.run(
        ["file", str(path)],
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()

    if "ISO Media, Apple iTunes ALAC/AAC-LC (.M4A) Audio" in output:
        destination = target_dir / path.name
        print(f"Moving: {path} -> {destination}")
        shutil.move(str(path), str(destination))