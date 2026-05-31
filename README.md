# find_dupes.py

A small command-line utility for finding duplicate files by content, keeping the oldest copy, and either previewing, moving, or scripting what happens to newer duplicates.[file:1]

## What it does

The script scans one or more directories recursively, groups files by size, then confirms duplicates with SHA-256 hashing so matching files are identified by content rather than by filename alone.[file:1]
It skips symbolic links, supports excluded directories, and automatically excludes its duplicate destination folder to avoid scanning files it just moved.[file:1]
When duplicate files are found, it keeps the oldest file in each matching group and treats the newer copies as the files to process.[file:1]

## Features

- Recursively scans one or more directories for duplicate files.[file:1]
- Uses file size plus SHA-256 hashing to verify duplicates.[file:1]
- Keeps the oldest copy in each duplicate set based on modification time.[file:1]
- Supports three actions: `print`, `move`, and `script`.[file:1]
- Moves newer duplicates to `~/Downloads/duplicates` in move mode.[file:1]
- Can generate a Bash script with planned `mv` commands instead of moving files immediately.[file:1]
- Avoids filename collisions in the destination directory by creating unique names such as `name_1.ext` when needed.[file:1]
- Lets you exclude one or more directories with repeated `--exclude` flags.[file:1]

## Requirements

- Python 3.8+ is recommended; the script uses modern Python features such as the assignment expression in file hashing.[file:1]
- Standard library only; no third-party packages are required.[file:1]

## Usage

```bash
python3 find_dupes.py <directory> [<directory> ...] [--action print|move|script] [--exclude PATH] [--script-name NAME]
```

### Arguments

- `directories`: One or more directories to scan recursively.[file:1]
- `--action`: What to do with newer duplicates. Choices are `print`, `move`, or `script`. Default: `print`.[file:1]
- `--exclude`: Directory to exclude from scanning. You can pass this option multiple times.[file:1]
- `--script-name`: Filename for the generated Bash script when using `--action script`. Default: `move_duplicates.sh`.[file:1]

## Actions

### `print`

Shows what would be moved without changing any files.[file:1]
This mode prints duplicate groups in descending size order, shows the oldest file kept in each group, and shows the source-to-destination move plan for newer copies.[file:1]

Example:

```bash
python3 find_dupes.py ~/Downloads --action print
```

### `move`

Creates `~/Downloads/duplicates` if needed and moves newer duplicate files there.[file:1]
The script reports what it moved and which oldest file was preserved for each group.[file:1]

Example:

```bash
python3 find_dupes.py ~/Downloads ~/Documents --action move
```

### `script`

Writes an executable Bash script in the current working directory instead of moving files immediately.[file:1]
The generated script includes comments for each duplicate group, identifies the oldest file kept, creates the destination directory, and issues `mv` commands for the newer copies.[file:1]

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

1. Files are collected from the requested directories with excluded paths filtered out.[file:1]
2. Files are first grouped by size, which avoids hashing every file unnecessarily.[file:1]
3. Files that share a size are hashed with SHA-256.[file:1]
4. Only files with matching hashes are treated as duplicates.[file:1]
5. Within each duplicate set, the oldest file by modification time is kept and the rest are selected for processing.[file:1]

## Output behavior

If no duplicates are found, the script prints `No duplicate files found.`.[file:1]
If duplicates exist but there are no newer copies to process, it prints `Duplicate files were found, but there were no newer copies to process.`.[file:1]
In move mode, failed file moves are reported to standard error without stopping the whole run.[file:1]

## Notes

- The destination folder is fixed in the script as `~/Downloads/duplicates`.[file:1]
- Duplicate groups are sorted from largest to smallest file size before being printed, scripted, or moved.[file:1]
- Files are considered duplicates by content, not by name.[file:1]
- The oldest file is preserved; newer copies are the ones acted on.[file:1]

## License

None.
