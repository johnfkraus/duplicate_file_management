#!/usr/bin/env python3

import os
import sys
import shutil
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict


def file_hash(path, chunk_size=1024 * 1024):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(paths):
    size_map = defaultdict(list)

    for root_path in paths:
        for dirpath, _, filenames in os.walk(root_path):
            for name in filenames:
                full_path = os.path.join(dirpath, name)
                try:
                    if not os.path.islink(full_path) and os.path.isfile(full_path):
                        size = os.path.getsize(full_path)
                        size_map[size].append(full_path)
                except OSError:
                    pass

    duplicates = []

    for size, files in size_map.items():
        if len(files) < 2:
            continue

        hash_map = defaultdict(list)
        for path in files:
            try:
                hash_map[file_hash(path)].append(path)
            except OSError:
                pass

        for matched_files in hash_map.values():
            if len(matched_files) > 1:
                duplicates.append((size, matched_files))

    duplicates.sort(key=lambda item: item[0], reverse=True)
    return duplicates


def format_size(num_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


def unique_destination(dest_dir, filename):
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1

    while True:
        new_candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not new_candidate.exists():
            return new_candidate
        counter += 1


def move_newest_duplicates(duplicate_groups, destination_dir, dry_run=False):
    if not dry_run:
        destination_dir.mkdir(parents=True, exist_ok=True)

    moved_files = []

    for size, group in duplicate_groups:
        try:
            sorted_group = sorted(group, key=os.path.getmtime)
        except OSError:
            continue

        keep_file = sorted_group[0]
        files_to_move = sorted_group[1:]

        for src in files_to_move:
            try:
                dest = unique_destination(destination_dir, Path(src).name)

                if not dry_run:
                    final_path = shutil.move(src, str(dest))
                else:
                    final_path = str(dest)

                moved_files.append((size, src, final_path, keep_file, dry_run))
            except OSError as e:
                print(f"Could not process {src}: {e}", file=sys.stderr)

    return moved_files


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate files, keep the oldest copy, and move newer duplicates."
    )
    parser.add_argument(
        "directories",
        nargs="+",
        help="One or more directories to scan recursively"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without moving any files"
    )

    args = parser.parse_args()

    destination = Path("~/Downloads/duplicates").expanduser()
    duplicate_groups = find_duplicates(args.directories)

    if not duplicate_groups:
        print("No duplicate files found.")
        return

    moved = move_newest_duplicates(
        duplicate_groups,
        destination,
        dry_run=args.dry_run
    )

    if not moved:
        print("Duplicate files were found, but none were processed.")
        return

    if args.dry_run:
        print(f"[DRY RUN] Newest duplicates would be moved to: {destination}\n")
    else:
        print(f"Moved newest duplicates to: {destination}\n")

    current_size = None
    group_num = 0

    for size, src, dest, kept, dry_run in sorted(moved, key=lambda x: x[0], reverse=True):
        if size != current_size:
            current_size = size
            group_num += 1
            print(f"Group {group_num} - {format_size(size)} each:")
            print(f"  Kept oldest: {kept}")

        action = "Would move" if dry_run else "Moved"
        print(f"  {action}: {src} -> {dest}")
        print()


if __name__ == "__main__":
    main()