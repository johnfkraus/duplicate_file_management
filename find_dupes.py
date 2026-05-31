#!/usr/bin/env python3

import os
import sys
import shlex
import shutil
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict


def normalize_path(path_str):
    return Path(path_str).expanduser().resolve()


def is_excluded(path, excluded_paths):
    try:
        path = Path(path).resolve()
        return any(path == ex or ex in path.parents for ex in excluded_paths)
    except OSError:
        return False


def file_hash(path, chunk_size=1024 * 1024):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(paths, excluded_paths):
    size_map = defaultdict(list)

    for root_path in paths:
        root_path = str(normalize_path(root_path))

        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            current_dir = Path(dirpath).resolve()

            dirnames[:] = [
                d for d in dirnames
                if not is_excluded(current_dir / d, excluded_paths)
            ]

            if is_excluded(current_dir, excluded_paths):
                continue

            for name in filenames:
                full_path = os.path.join(dirpath, name)
                try:
                    if is_excluded(full_path, excluded_paths):
                        continue
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


def unique_destination(dest_dir, filename, reserved_paths=None):
    reserved_paths = reserved_paths or set()

    candidate = dest_dir / filename
    if candidate not in reserved_paths and not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1

    while True:
        new_candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if new_candidate not in reserved_paths and not new_candidate.exists():
            return new_candidate
        counter += 1


def plan_moves(duplicate_groups, destination_dir):
    planned = []
    reserved_destinations = set()

    for size, group in duplicate_groups:
        try:
            sorted_group = sorted(group, key=os.path.getmtime)
        except OSError:
            continue

        keep_file = sorted_group[0]
        files_to_move = sorted_group[1:]

        for src in files_to_move:
            try:
                dest = unique_destination(
                    destination_dir,
                    Path(src).name,
                    reserved_paths=reserved_destinations
                )
                reserved_destinations.add(dest)
                planned.append((size, src, str(dest), keep_file))
            except OSError:
                pass

    return planned


def execute_moves(planned_moves, destination_dir):
    destination_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for size, src, dest, kept in planned_moves:
        try:
            final_path = shutil.move(src, dest)
            results.append((size, src, final_path, kept))
        except OSError as e:
            print(f"Could not move {src}: {e}", file=sys.stderr)

    return results


def write_move_script(planned_moves, destination_dir, script_path):
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f'mkdir -p {shlex.quote(str(destination_dir))}',
        "",
    ]

    current_size = None
    group_num = 0

    for size, src, dest, kept in sorted(planned_moves, key=lambda x: x[0], reverse=True):
        if size != current_size:
            current_size = size
            group_num += 1
            lines.append(f"# Group {group_num} - {format_size(size)} each")
            lines.append(f"# Keep oldest: {kept}")

        lines.append(f"mv {shlex.quote(src)} {shlex.quote(dest)}")
        lines.append("")

    script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script_path.chmod(0o755)


def print_plan(planned_moves, destination):
    print(f"[PRINT MODE] Newest duplicates would be moved to: {destination}\n")

    current_size = None
    group_num = 0

    for size, src, dest, kept in sorted(planned_moves, key=lambda x: x[0], reverse=True):
        if size != current_size:
            current_size = size
            group_num += 1
            print(f"Group {group_num} - {format_size(size)} each:")
            print(f"  Kept oldest: {kept}")

        print(f"  Would move: {src} -> {dest}")
        print()


def print_results(moved, destination):
    print(f"Moved newest duplicates to: {destination}\n")

    current_size = None
    group_num = 0

    for size, src, dest, kept in sorted(moved, key=lambda x: x[0], reverse=True):
        if size != current_size:
            current_size = size
            group_num += 1
            print(f"Group {group_num} - {format_size(size)} each:")
            print(f"  Kept oldest: {kept}")

        print(f"  Moved: {src} -> {dest}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate files, keep the oldest copy, and handle newer duplicates."
    )
    parser.add_argument(
        "directories",
        nargs="+",
        help="One or more directories to scan recursively"
    )
    parser.add_argument(
        "--action",
        choices=["move", "script", "print"],
        default="print",
        help="What to do with newer duplicates: move them, print the plan, or write a bash script"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Directory to exclude from scanning; may be given multiple times"
    )
    parser.add_argument(
        "--script-name",
        default="move_duplicates.sh",
        help="Name of the generated bash script written in the current project directory"
    )

    args = parser.parse_args()

    destination = Path("~/Downloads/duplicates").expanduser().resolve()

    # the destination is an excluded path to prevent an infinite loop.
    excluded_paths = {destination}
    excluded_paths.update(normalize_path(p) for p in args.exclude)

    duplicate_groups = find_duplicates(args.directories, excluded_paths)

    if not duplicate_groups:
        print("No duplicate files found.")
        return

    planned_moves = plan_moves(duplicate_groups, destination)

    if not planned_moves:
        print("Duplicate files were found, but there were no newer copies to process.")
        return

    if args.action == "print":
        print_plan(planned_moves, destination)
        return

    if args.action == "script":
        script_path = Path.cwd() / args.script_name
        write_move_script(planned_moves, destination, script_path)
        print(f"Wrote bash script: {script_path}")
        print(f"Destination directory in script: {destination}")
        return

    if args.action == "move":
        moved = execute_moves(planned_moves, destination)
        if not moved:
            print("Duplicate files were found, but no files were moved.")
            return
        print_results(moved, destination)
        return


if __name__ == "__main__":
    main()