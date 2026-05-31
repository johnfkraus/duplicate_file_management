
from pathlib import Path
import argparse

MAX_LEN = 30

def make_unique_name(parent: Path, stem: str, suffix: str, max_len: int, reserved_names: set[str]) -> str:
    allowed_stem_len = max_len - len(suffix)
    if allowed_stem_len <= 0:
        raise ValueError(f"Extension too long to fit within {max_len} characters: {suffix}")

    base_stem = stem[:allowed_stem_len]
    candidate = f"{base_stem}{suffix}"
    counter = 1

    while candidate in reserved_names or (parent / candidate).exists():
        tag = f"_{counter}"
        allowed = max_len - len(suffix) - len(tag)
        if allowed <= 0:
            raise ValueError(f"Cannot create unique name within {max_len} characters for: {stem}{suffix}")
        candidate = f"{stem[:allowed]}{tag}{suffix}"
        counter += 1

    reserved_names.add(candidate)
    return candidate

def shorten_filenames(root: Path, max_len: int = MAX_LEN, dry_run: bool = True):
    if not root.is_dir():
        raise NotADirectoryError(root)

    renamed = 0

    for parent, _, files in os_walk_sorted(root):
        reserved_names = {p.name for p in parent.iterdir() if p.is_file()}

        for file_path in files:
            old_name = file_path.name
            if len(old_name) <= max_len:
                continue

            reserved_names.discard(old_name)

            new_name = make_unique_name(
                parent=parent,
                stem=file_path.stem,
                suffix=file_path.suffix,
                max_len=max_len,
                reserved_names=reserved_names,
            )

            if dry_run:
                print(f"DRY RUN: {old_name}  ->  {new_name}")
            else:
                file_path.rename(parent / new_name)
                print(f"RENAMED: {old_name}  ->  {new_name}")

            renamed += 1

    print(f"\nTotal files renamed: {renamed}")

def os_walk_sorted(root: Path):
    for parent in sorted([p for p in root.rglob('*') if p.is_dir()] + [root]):
        files = sorted([p for p in parent.iterdir() if p.is_file()], key=lambda p: p.name)
        yield parent, None, files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shorten long filenames safely.")
    parser.add_argument("directory", type=Path, help="Directory to process")
    parser.add_argument("--max-len", type=int, default=30, help="Maximum filename length including extension")
    parser.add_argument("--apply", action="store_true", help="Actually rename files")
    args = parser.parse_args()

    shorten_filenames(
        root=args.directory,
        max_len=args.max_len,
        dry_run=not args.apply
    )