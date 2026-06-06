# find_dupes.py

A small command-line utility for finding duplicate files by content, keeping the oldest copy, and either previewing, moving, or scripting what happens to newer duplicates.

## What it does

The script scans one or more directories recursively, groups files by size, then confirms duplicates with SHA-256 hashing so matching files are identified by content rather than by filename alone.

It skips symbolic links, supports excluded directories, and automatically excludes its duplicate destination folder to avoid scanning files it just moved.
When duplicate files are found, it keeps the oldest file in each matching group and treats the newer copies as the files to process.

## Features

- Recursively scans one or more directories for duplicate files.
- Uses file size plus SHA-256 hashing to verify duplicates.
- Keeps the oldest copy in each duplicate set based on modification time.
- Supports three actions: `print`, `move`, and `script`.
- Moves newer duplicates to `~/Downloads/duplicates` in move mode.
- Can generate a Bash script with planned `mv` commands instead of moving files immediately.
- Avoids filename collisions in the destination directory by creating unique names such as `name_1.ext` when needed.
- Lets you exclude one or more directories with repeated `--exclude` flags.

## Requirements

- Python 3.8+ is recommended; the script uses modern Python features such as the assignment expression in file hashing.
- Standard library only; no third-party packages are required.

## Usage

```bash
python3 find_dupes.py <directory> [<directory> ...] [--action print|move|script] [--exclude PATH] [--script-name NAME]
```

### Arguments

- `directories`: One or more directories to scan recursively.
- `--action`: What to do with newer duplicates. Choices are `print`, `move`, or `script`. Default: `print`.
- `--exclude`: Directory to exclude from scanning. You can pass this option multiple times.
- `--script-name`: Filename for the generated Bash script when using `--action script`. Default: `move_duplicates.sh`.

## Actions

### `print`

Shows what would be moved without changing any files.
This mode prints duplicate groups in descending size order, shows the oldest file kept in each group, and shows the source-to-destination move plan for newer copies.

Example:

```bash
python3 find_dupes.py ~/Downloads --action print
```

### `move`

Creates `~/Downloads/duplicates` if needed and moves newer duplicate files there.
The script reports what it moved and which oldest file was preserved for each group.

Example:

```bash
python3 find_dupes.py ~/Downloads ~/Documents --action move
```

### `script`

Writes an executable Bash script in the current working directory instead of moving files immediately.
The generated script includes comments for each duplicate group, identifies the oldest file kept, creates the destination directory, and issues `mv` commands for the newer copies.

Example:

```bash
python3 find_dupes.py ~/Pictures --action script --script-name review_dupes.sh
```

## Examples

Scan two folders and preview the plan:

```bash
python3 find_dupes.py ~/Downloads ~/Desktop
```

Scan a folder but skip common archive locations:

```bash
python3 find_dupes.py ~/Documents --exclude ~/Documents/Archive --exclude ~/Documents/Backups
```

Generate a script, review it, then run it manually:

```bash
python3 find_dupes.py ~/Media --action script
./move_duplicates.sh
```

## How duplicates are decided

1. Files are collected from the requested directories with excluded paths filtered out.
2. Files are first grouped by size, which avoids hashing every file unnecessarily.
3. Files that share a size are hashed with SHA-256.
4. Only files with matching hashes are treated as duplicates.
5. Within each duplicate set, the oldest file by modification time is kept and the rest are selected for processing.

## Output behavior

If no duplicates are found, the script prints `No duplicate files found.`.
If duplicates exist but there are no newer copies to process, it prints `Duplicate files were found, but there were no newer copies to process.`.
In move mode, failed file moves are reported to standard error without stopping the whole run.

## Notes

- The destination folder is fixed in the script as `~/Downloads/duplicates`.
- Duplicate groups are sorted from largest to smallest file size before being printed, scripted, or moved.
- Files are considered duplicates by content, not by name.
- The oldest file is preserved; newer copies are the ones acted on.

## License

None.
