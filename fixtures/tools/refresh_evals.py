"""Check that eval sets point at the emails in your inbox, and refresh them if not.

Each test case in an eval set passes the workflow a Gmail message ID. The evals prompt copies
those IDs from fixtures/seeded-ids.json when it builds the sets, and the sets never read the
file again. So eval sets go stale when the inbox is seeded again, and the finished steps in
SupportInbox/ hold IDs from the inbox they were built on.

This script finds every eval set under the paths you give it (the whole repo by default),
matches each test case to its ticket by name (E36-billing is ticket E36), and compares its
messageId with fixtures/seeded-ids.json. It only reports until you add --yes, which rewrites
the stale IDs and changes nothing else in the file.

The eval sets in SupportInbox/ are committed with placeholder IDs (SEED-E36 for ticket E36),
because real IDs only work on the inbox they were seeded into. A placeholder counts as stale,
so --yes replaces it with your ID. Maintainers put the placeholders back with --placeholders
before committing.

Needs Python 3.9+. No other packages, and no sign-in: it only reads and writes local files.

Examples:

    # Check every eval set in the repo
    python fixtures/tools/refresh_evals.py

    # Check only the finished steps
    python fixtures/tools/refresh_evals.py SupportInbox

    # Rewrite the stale IDs
    python fixtures/tools/refresh_evals.py --yes

    # Before committing the finished steps: put the placeholders back
    python fixtures/tools/refresh_evals.py SupportInbox --placeholders

Exit code 0 when every test case matches (or was refreshed), 1 when any test case is stale
or its ticket has no ID in seeded-ids.json. Seed missing tickets with seed_inbox.py first.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent
REPO = FIXTURES.parent
TICKET = re.compile(r"^(E\d+)\b")
PLACEHOLDER = "SEED-{}"
SKIP_DIRS = {".git", "node_modules"}


def eval_sets(roots: list[Path]) -> list[Path]:
    found = set()
    for root in roots:
        for path in root.rglob("eval-sets/*.json"):
            if path.parent.parent.parent.name == "evals" and not SKIP_DIRS & set(path.parts):
                found.add(path.resolve())
    return sorted(found)


def shown(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="Folders to search for eval sets (default: the whole repo)")
    parser.add_argument("--ids-file", default=str(FIXTURES / "seeded-ids.json"),
                        help="Ticket ID -> Gmail message ID, as seed_inbox.py writes it (default fixtures/seeded-ids.json)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--yes", action="store_true", help="Rewrite stale message IDs (default is a check)")
    mode.add_argument("--placeholders", action="store_true",
                      help="Replace every message ID with its placeholder (SEED-E36), for committing")
    args = parser.parse_args()

    if args.placeholders:
        seeded = None
    else:
        try:
            seeded = json.loads(Path(args.ids_file).read_text(encoding="utf-8"))
        except FileNotFoundError:
            sys.exit(f"No {args.ids_file}. Load your inbox with seed_inbox.py first.")

    roots = [Path(p) for p in args.paths] or [REPO]
    for root in roots:
        if not root.is_dir():
            sys.exit(f"Not a folder: {root}")
    files = eval_sets(roots)
    if not files:
        print("No eval sets found.")
        return

    stale_total = missing_total = 0
    for path in files:
        with path.open(encoding="utf-8", newline="") as f:   # keep the file's line endings
            text = f.read()
        data = json.loads(text)
        stale: dict[str, str] = {}   # old message ID -> new
        missing, current, placeholders, unmatched = [], 0, 0, []
        for case in data.get("evaluations", []):
            old = (case.get("inputs") or {}).get("messageId")
            if old is None:
                continue
            m = TICKET.match(case.get("name", ""))
            if not m:
                unmatched.append(case.get("name", "(no name)"))
                continue
            ticket = m.group(1)
            placeholders += old == PLACEHOLDER.format(ticket)
            new = PLACEHOLDER.format(ticket) if args.placeholders else seeded.get(ticket)
            if new is None:
                missing.append(ticket)
            elif new == old:
                current += 1
            else:
                stale[old] = new

        if args.placeholders:
            status = f"{len(stale) + current} test cases"
        else:
            status = f"{len(stale)} stale ({placeholders} of them placeholders), {current} current"
            if missing:
                status += f", {len(missing)} not seeded ({' '.join(missing)})"
        print(f"{shown(path)}  [{data.get('name', '?')}]  {status}")
        for name in unmatched:
            print(f"  skipped {name!r}: no ticket ID at the start of its name")

        if stale and (args.yes or args.placeholders):
            for old, new in stale.items():
                pattern = re.compile(r'("messageId"\s*:\s*")' + re.escape(old) + '"')
                text = pattern.sub(lambda m, new=new: m.group(1) + new + '"', text)
            with path.open("w", encoding="utf-8", newline="") as f:
                f.write(text)
            print(f"  {'set placeholders for' if args.placeholders else 'refreshed'} {len(stale)} message IDs")
        else:
            stale_total += len(stale)
        missing_total += len(missing)

    if stale_total:
        print(f"\n{stale_total} stale message IDs. Run again with --yes to refresh them.")
    if missing_total:
        print(f"\n{missing_total} test cases have no seeded email. Seed those tickets with seed_inbox.py, then run this again.")
    sys.exit(1 if stale_total or missing_total else 0)


if __name__ == "__main__":
    main()
