#!/usr/bin/env python3
import argparse
from pathlib import Path


def iter_md_files(root: Path):
    for p in root.rglob("*.md"):
        if p.is_file():
            yield p


def main():
    parser = argparse.ArgumentParser(
        description="Rename .md files by replacing spaces with underscores."
    )
    parser.add_argument("directory", nargs="?", default=".", help="Root directory to search.  Default = '.' (current working directory)")
    parser.add_argument("-y", "--yes", action="store_true", help="Rename automatically without prompting")
    args = parser.parse_args()

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    for src in iter_md_files(root):
        new_name = src.name.replace(" ", "_")
        if new_name == src.name:
            continue

        dst = src.with_name(new_name)
        print(f"Proposed: {src} -> {dst}")

        if not args.yes:
            while True:
                resp = input("Rename? [y/n]: ").strip().lower()
                if resp in {"y", "yes"}:
                    break
                if resp in {"n", "no"}:
                    print("Skipped")
                    dst = None
                    break
                print("Please enter y or n.")
            if dst is None:
                continue

        if dst.exists():
            print(f"Skipped: destination already exists: {dst}")
            continue

        src.rename(dst)
        print("Renamed")


if __name__ == "__main__":
    main()