"""
Log:
- 2026-10-15 - [AlexPT2k22]: Created the script that enforces the improvement log rule from the README.
- 2026-10-15 - [AlexPT2k22]: Only read the log from the module docstring, detect removed entries, and handle renamed files and paths with spaces.
"""

import ast
import re
import subprocess
import sys

LOG_ENTRY = re.compile(r"^- \d{4}-\d{2}-\d{2} - \[.+?\]:")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def changed_files(merge_base):
    # -z keeps paths with spaces intact; renames come as "R<score>", old path, new path
    fields = git("diff", "-z", "-M", "--name-status", "--diff-filter=MR", merge_base, "HEAD", "--", "*.py").split("\0")
    fields = [f for f in fields if f]
    files = []
    i = 0
    while i < len(fields):
        status = fields[i]
        if status.startswith("R"):
            files.append((fields[i + 1], fields[i + 2]))
            i += 3
        else:
            files.append((fields[i + 1], fields[i + 1]))
            i += 2
    return files


def log_entries(source):
    """Return the log entries in the module docstring, or None if the file can't be parsed."""
    try:
        docstring = ast.get_docstring(ast.parse(source), clean=False) or ""
    except SyntaxError:
        return None
    return [line.strip() for line in docstring.splitlines() if LOG_ENTRY.match(line.strip())]


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    merge_base = git("merge-base", base, "HEAD").strip()

    problems = []
    files = changed_files(merge_base)
    for old_path, new_path in files:
        old_entries = log_entries(git("show", f"{merge_base}:{old_path}")) or []
        new_entries = log_entries(git("show", f"HEAD:{new_path}"))

        if new_entries is None:
            problems.append(f"{new_path}: could not be parsed")
            continue
        if [e for e in old_entries if e not in new_entries]:
            problems.append(f"{new_path}: previous log entries were removed")
        if not [e for e in new_entries if e not in old_entries]:
            problems.append(f"{new_path}: no new entry in the improvement log")

    if problems:
        print("Improvement log check failed:")
        for problem in problems:
            print(f"  - {problem}")
        print('\nAdd a line like "- YYYY-MM-DD - [NAME]: Describe the improvement." to the log at the top of each file,')
        print("without removing previous entries.")
        sys.exit(1)

    print(f"Improvement log OK ({len(files)} modified Python file(s)).")


if __name__ == "__main__":
    main()
