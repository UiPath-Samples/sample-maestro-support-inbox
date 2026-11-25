"""Copy a step in SupportInbox/ to a new project folder with new internal IDs.

The platform looks up a project's IDs across the whole solution, so a copied folder that keeps
the original's IDs shares eval runs with it and can silently run its agents. This script makes
the copy and gives it new IDs in one go:

- the project ID (operate.json) and the evals/<projectId>/ folder named after it;
- each eval set and evaluator ID, and the 8-character suffix in their file names;
- each inline agent ID (a folder holding agent.json) and each of its tool resource IDs;
- the plus-address tag in the Gmail trigger's filter (for example +step21@ to +step22@);
- the project's Name in project.uiproj.

It leaves out the Flow SDK's working files in .flow-sdk/, keeping only the source
(SupportInbox.flow.ts) and bindings.json, and checks that no old ID is left in the copy.

Needs Python 3.9+. No other packages; it only reads and writes local files.

Example, from the repo root:

    python fixtures/tools/copy_checkpoint.py SupportInbox/2-2-auto-approvals SupportInbox/3-1-run --tag +step31@

Then register the copy and refresh the solution's resources (see MAINTAINING.md).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TAG = re.compile(r"\+step\d+@")
SUFFIX = re.compile(r"-([0-9a-f]{8})\.json")
KEEP_IN_FLOW_SDK = {"SupportInbox.flow.ts", "bindings.json"}
TEXT_SUFFIXES = {".json", ".flow", ".ts", ".uiproj", ".md", ""}


def new_ids(dst: Path) -> dict[str, str]:
    ids = {}
    pid = json.loads((dst / "operate.json").read_text(encoding="utf-8"))["projectId"]
    ids[pid] = str(uuid.uuid4())
    for kind in ("eval-sets", "evaluators"):
        for f in (dst / "evals").glob(f"*/{kind}/*.json"):
            old = json.loads(f.read_text(encoding="utf-8"))["id"]
            # Evaluator IDs are readable names with a hex suffix (category-exact-match-d614e9a5)
            ids[old] = str(uuid.uuid4()) if UUID.match(old) else re.sub(r"[0-9a-f]{8}$", uuid.uuid4().hex[:8], old)
    for agent in dst.glob("*/agent.json"):
        ids[agent.parent.name] = str(uuid.uuid4())
        for res in agent.parent.glob("resources/*/"):
            if UUID.match(res.name):
                ids[res.name] = str(uuid.uuid4())
    return ids


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="The step to copy, for example SupportInbox/2-2-auto-approvals")
    parser.add_argument("dest", help="The new project folder, for example SupportInbox/3-1-run")
    parser.add_argument("--tag", required=True, help="The new step's plus-address tag, for example +step31@")
    args = parser.parse_args()

    src, dst = Path(args.source), Path(args.dest)
    if not (src / "operate.json").is_file():
        sys.exit(f"{src} isn't a Flow project (no operate.json)")
    if dst.exists():
        sys.exit(f"{dst} already exists")
    if not TAG.fullmatch(args.tag):
        sys.exit("--tag must look like +step31@")

    shutil.copytree(src, dst)
    flow_sdk = dst / ".flow-sdk"
    if flow_sdk.is_dir():
        for p in flow_sdk.iterdir():
            if p.name not in KEEP_IN_FLOW_SDK:
                shutil.rmtree(p) if p.is_dir() else p.unlink()

    ids = new_ids(dst)
    short = {old[:8]: new[:8] for old, new in ids.items() if UUID.match(old)}
    old_tags = set()
    for f in [p for p in dst.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES]:
        with f.open(encoding="utf-8", newline="") as fh:   # keep the file's line endings
            text = fh.read()
        new = text
        for old, nid in ids.items():
            new = new.replace(old, nid)
        new = SUFFIX.sub(lambda m: "-" + short.get(m.group(1), m.group(1)) + ".json", new)
        old_tags.update(TAG.findall(new))
        new = TAG.sub(args.tag, new)
        if new != text:
            with f.open("w", encoding="utf-8", newline="") as fh:
                fh.write(new)

    for p in sorted(dst.rglob("*"), key=lambda p: len(p.parts), reverse=True):   # deepest first
        name = p.name
        for old, nid in ids.items():
            name = name.replace(old, nid)
        name = SUFFIX.sub(lambda m: "-" + short.get(m.group(1), m.group(1)) + ".json", name)
        if name != p.name:
            p.rename(p.with_name(name))

    uiproj = dst / "project.uiproj"
    data = json.loads(uiproj.read_text(encoding="utf-8"))
    data["Name"] = dst.name
    uiproj.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    left = sorted({old for old in ids for p in dst.rglob("*")
                   if old in str(p.relative_to(dst)) or (p.is_file() and old in p.read_text(encoding="utf-8", errors="ignore"))})
    print(f"Copied {src} to {dst} with {len(ids)} new IDs; tag {', '.join(sorted(old_tags)) or '(none found)'} -> {args.tag}")
    if left:
        sys.exit(f"Old IDs still in the copy: {', '.join(left)}")


if __name__ == "__main__":
    main()
