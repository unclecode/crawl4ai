<!-- ---
!-- Timestamp: 2025-05-25 23:21:15
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/command/tree.md
!-- --- -->

# Tree Command Guidelines

## Table of Contents
- [Overview](#overview)
- [Common Usage Patterns](#common-usage-patterns)
- [Examples](#examples)
- [Full Command Reference](#full-command-reference)

## Overview
The `tree` command displays the directory structure in a visual tree format, making it easier to understand project organization. Use this command regularly to maintain awareness of the codebase structure.

## Common Usage Patterns

| Option | Description | Example |
|--------|-------------|---------|
| `-a` | Show all files, including hidden files | `tree -a` |
| `-d` | Show only directories | `tree -d` |
| `-L n` | Limit depth to n levels | `tree -L 2` |
| `-I pattern` | Exclude files/directories matching pattern | `tree -I "node_modules\|.git"` |
| `--gitignore` | Honor gitignore patterns | `tree -a --gitignore` |
| `-h` | Print sizes in human-readable format | `tree -h` |
| `-C` | Enable colorization | `tree -C` |

## Examples

| Use Case | Command | Description |
|----------|---------|-------------|
| Project Overview | `tree -L 2` | View top-level directories and immediate subdirectories |
| Code Navigation | `tree -L 3 src` | View source code structure to 3 levels deep |
| Full Directory Analysis | `tree -a -h --du` | Show all files with human-readable sizes and calculate directory sizes |
| Exclude Build Artifacts | `tree -I "node_modules\|build\|dist\|__pycache__"` | Show only relevant source files |
| Find Large Directories | `tree -d -h --du \| grep -B 3 -A 1 "[GM]"` | Identify directories with large content |
| JSON Output | `tree -J > structure.json` | Output structure in JSON format for parsing |

## Example Outputs

### Basic Project Structure
```
.
├── docs
│   ├── api
│   └── user-guide
├── src
│   ├── components
│   ├── services
│   └── utils
├── tests
│   ├── integration
│   └── unit
├── README.md
└── package.json
```

### Detailed Source Analysis
```
src
├── components
│   ├── Button
│   │   ├── Button.jsx
│   │   ├── Button.test.js
│   │   └── index.js
│   └── Header
│       ├── Header.jsx
│       ├── Header.test.js
│       └── index.js
├── services
│   ├── api.js
│   └── auth.js
└── utils
    ├── formatters.js
    └── validators.js
```

## Full Command Reference

``` plaintext
usage: tree [-acdfghilnpqrstuvxACDFJQNSUX] [-L level [-R]] [-H  baseHREF]
    [-T title] [-o filename] [-P pattern] [-I pattern] [--gitignore]
    [--gitfile[=]file] [--matchdirs] [--metafirst] [--ignore-case]
    [--nolinks] [--hintro[=]file] [--houtro[=]file] [--inodes] [--device]
    [--sort[=]<n>] [--dirsfirst] [--filesfirst] [--filelimit #] [--si]
    [--du] [--prune] [--charset[=]X] [--timefmt[=]format] [--fromfile]
    [--fromtabfile] [--fflinks] [--info] [--infofile[=]file] [--noreport]
    [--version] [--help] [--] [directory ...]
  ------- Listing options -------
  -a            All files are listed.
  -d            List directories only.
  -l            Follow symbolic links like directories.
  -f            Print the full path prefix for each file.
  -x            Stay on current filesystem only.
  -L level      Descend only level directories deep.
  -R            Rerun tree when max dir level reached.
  -P pattern    List only those files that match the pattern given.
  -I pattern    Do not list files that match the given pattern.
  --gitignore   Filter by using .gitignore files.
  --gitfile X   Explicitly read gitignore file.
  --ignore-case Ignore case when pattern matching.
  --matchdirs   Include directory names in -P pattern matching.
  --metafirst   Print meta-data at the beginning of each line.
  --prune       Prune empty directories from the output.
  --info        Print information about files found in .info files.
  --infofile X  Explicitly read info file.
  --noreport    Turn off file/directory count at end of tree listing.
  --charset X   Use charset X for terminal/HTML and indentation line output.
  --filelimit # Do not descend dirs with more than # files in them.
  -o filename   Output to file instead of stdout.
  ------- File options -------
  -q            Print non-printable characters as '?'.
  -N            Print non-printable characters as is.
  -Q            Quote filenames with double quotes.
  -p            Print the protections for each file.
  -u            Displays file owner or UID number.
  -g            Displays file group owner or GID number.
  -s            Print the size in bytes of each file.
  -h            Print the size in a more human readable way.
  --si          Like -h, but use in SI units (powers of 1000).
  --du          Compute size of directories by their contents.
  -D            Print the date of last modification or (-c) status change.
  --timefmt <f> Print and format time according to the format <f>.
  -F            Appends '/', '=', '*', '@', '|' or '>' as per ls -F.
  --inodes      Print inode number of each file.
  --device      Print device ID number to which each file belongs.
  ------- Sorting options -------
  -v            Sort files alphanumerically by version.
  -t            Sort files by last modification time.
  -c            Sort files by last status change time.
  -U            Leave files unsorted.
  -r            Reverse the order of the sort.
  --dirsfirst   List directories before files (-U disables).
  --filesfirst  List files before directories (-U disables).
  --sort X      Select sort: name,version,size,mtime,ctime.
  ------- Graphics options -------
  -i            Don't print indentation lines.
  -A            Print ANSI lines graphic indentation lines.
  -S            Print with CP437 (console) graphics indentation lines.
  -n            Turn colorization off always (-C overrides).
  -C            Turn colorization on always.
  ------- XML/HTML/JSON options -------
  -X            Prints out an XML representation of the tree.
  -J            Prints out an JSON representation of the tree.
  -H baseHREF   Prints out HTML format with baseHREF as top directory.
  -T string     Replace the default HTML title and H1 header with string.
  --nolinks     Turn off hyperlinks in HTML output.
  --hintro X    Use file X as the HTML intro.
  --houtro X    Use file X as the HTML outro.
  ------- Input options -------
  --fromfile    Reads paths from files (.=stdin)
  --fromtabfile Reads trees from tab indented files (.=stdin)
  --fflinks     Process link information when using --fromfile.
  ------- Miscellaneous options -------
  --version     Print version and exit.
  --help        Print usage and this help message and exit.
  --            Options processing terminator.
```

<!-- EOF -->