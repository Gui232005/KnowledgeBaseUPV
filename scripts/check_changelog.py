"""
Log:
- 2026-10-15 - [AlexPT2k22]: Created the script that enforces the improvement log rule from the README.
"""

import re
import subprocess
import sys

LOG_ENTRY = re.compile(r"^\+\s*- \d{4}-\d{2}-\d{2} - \[.+?\]:")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    changed = git("diff", "--diff-filter=M", "--name-only", f"{base}...HEAD", "--", "*.py").split()

    missing = []
    for path in changed:
        diff = git("diff", f"{base}...HEAD", "--", path)
        if not any(LOG_ENTRY.match(line) for line in diff.splitlines()):
            missing.append(path)

    if missing:
        print("These files were changed without a new entry in their improvement log:")
        for path in missing:
            print(f"  - {path}")
        print('\nAdd a line like "- YYYY-MM-DD - [NAME]: Describe the improvement." to the log at the top of each file.')
        sys.exit(1)

    print(f"Improvement log OK ({len(changed)} modified Python file(s)).")


if __name__ == "__main__":
    main()
