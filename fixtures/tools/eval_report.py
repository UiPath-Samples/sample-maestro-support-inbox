r"""Summarise eval runs of the support inbox workflow, split by tickets with and without attachments.

Reads each eval set's latest run (or the run you name) with the `uip` CLI, matches every test
case to its ticket in fixtures/tickets by the ID at the start of its name (E36-billing ->
E36), and prints, for each set:

- each evaluator's pass rate, split by tickets with and without attachments;
- for an exact-match evaluator, the result per expected category, with the same split;
- the failing test cases, with the judge's reason.

An exact-match evaluator passes at a score of 1; an LLM judge passes at --threshold (0.7 by
default). With --compare, it also shows each test case's scores in the run before, so a fix can
be read as before and after.

Run it from the solution folder or anywhere else; it only reads. Runs started from VS Code's
evaluation panel are listed like any other. The results don't include the workflow's actual
outputs, so a category miss shows that it missed, not where the email went: open the run in
VS Code for that.

Needs Python 3.9+ and the `uip` CLI, signed in to the tenant (`uip login`). No other packages.

Examples:

    # Latest run of each set in the checkpoint project
    python fixtures/tools/eval_report.py --project SupportInbox/1-2-build-evals

    # One set, a named run, and the run before it for comparison
    python fixtures/tools/eval_report.py --project SupportInbox/2-1-fix --set triage \
        --run <evalSetRunId> --compare

    # Wait for a run that's still going
    python fixtures/tools/eval_report.py --project SupportInbox/1-2-build-evals --wait
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

TICKETS = Path(__file__).resolve().parent.parent / "tickets"
WAITING = {"pending", "running", "queued", "inprogress"}


def uip_cli() -> str:
    uip = shutil.which("uip.cmd") or shutil.which("uip")
    if not uip:
        sys.exit("The uip CLI isn't on PATH. Install it and run `uip login` first.")
    return uip


def uip_json(uip: str, *args: str) -> dict:
    """Run a uip command and return its Data, skipping any [WARN] lines before the JSON."""
    out = subprocess.run([uip, *args, "--output", "json"], capture_output=True, text=True,
                         encoding="utf-8", check=False)
    text = out.stdout
    start = text.find("{")
    try:
        envelope = json.loads(text[start:]) if start >= 0 else {}
    except json.JSONDecodeError:
        envelope = {}
    if envelope.get("Result") != "Success":
        message = envelope.get("Message") or (out.stderr or text).strip()[:300]
        sys.exit(f"`uip {' '.join(args[:4])}` failed: {message}")
    return envelope.get("Data")


def load_tickets() -> dict[str, dict]:
    tickets = {}
    for path in TICKETS.glob("*/ticket.json"):
        ticket = json.loads(path.read_text(encoding="utf-8"))
        tickets[ticket["id"]] = {
            "category": ticket["expected"]["category"],
            "attachments": bool(ticket.get("attachments")),
        }
    if not tickets:
        sys.exit(f"No tickets found under {TICKETS}.")
    return tickets


def load_evaluators(project: Path) -> dict[str, str]:
    """Map each evaluator's display name to 'exact' or 'judge' from the project's eval files."""
    kinds = {}
    for path in glob.glob(str(project / "evals" / "*" / "evaluators" / "*.json")):
        ev = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        kind = "exact" if "exact-match" in ev.get("evaluatorTypeId", "") else "judge"
        kinds[ev.get("name", ev.get("id"))] = kind
    return kinds


def set_names(project: Path) -> list[str]:
    names = []
    for path in sorted(glob.glob(str(project / "evals" / "*" / "eval-sets" / "*.json"))):
        names.append(json.loads(Path(path).read_text(encoding="utf-8-sig"))["name"])
    return names


def parse_scores(text: str) -> dict[str, float | None]:
    scores = {}
    for part in (text or "").split(","):
        if ":" not in part:
            continue
        name, value = part.rsplit(":", 1)
        try:
            scores[name.strip()] = float(value)
        except ValueError:
            scores[name.strip()] = None  # "Error"
    return scores


def parse_reasons(text: str) -> dict[str, str]:
    reasons = {}
    for chunk in (text or "").split(" | ["):
        chunk = chunk.lstrip("[")
        if "] " in chunk:
            name, reason = chunk.split("] ", 1)
            reasons[name.strip()] = reason.strip()
    return reasons


def passed(kind: str, score: float | None, threshold: float) -> bool:
    if score is None:
        return False
    return score >= 1 if kind == "exact" else score >= threshold


def pick_runs(uip: str, project: Path, eval_set: str, run_id: str | None, compare: bool,
              wait: bool) -> tuple[dict, dict | None]:
    runs = uip_json(uip, "maestro", "flow", "eval", "runs", "list", "--set", eval_set,
                    "--path", str(project)) or []
    if not runs:
        sys.exit(f"No runs of set '{eval_set}' yet. Run it from VS Code's evaluation panel first.")
    index = next((i for i, r in enumerate(runs) if r["EvalSetRunId"] == run_id), None) \
        if run_id else 0
    if index is None:
        sys.exit(f"Run {run_id} isn't a run of set '{eval_set}'.")
    run = runs[index]
    while wait and str(run.get("Status", "")).lower() in WAITING:
        print(f"{eval_set}: run {run['EvalSetRunId'][:8]} is {run['Status']}, waiting...",
              file=sys.stderr)
        time.sleep(20)
        run = uip_json(uip, "maestro", "flow", "eval", "runs", "status", run["EvalSetRunId"],
                       "--set", eval_set, "--path", str(project))
    previous = None
    if compare:
        previous = next((r for r in runs[index + 1:]
                         if str(r.get("Status", "")).lower() == "completed"), None)
    return run, previous


def results(uip: str, project: Path, eval_set: str, run_id: str) -> list[dict]:
    return uip_json(uip, "maestro", "flow", "eval", "runs", "results", run_id, "--set", eval_set,
                    "--path", str(project), "--verbose") or []


def report(eval_set: str, run: dict, rows: list[dict], previous_rows: list[dict] | None,
           tickets: dict, kinds: dict, threshold: float) -> None:
    split_name = {True: "with attachments", False: "no attachments"}
    print(f"\n## {eval_set}: run {run['EvalSetRunId'][:8]} ({run.get('Status')}, "
          f"{len(rows)} test cases)\n")
    if str(run.get("Status", "")).lower() == "failed":
        print("This run failed before scoring. To report a different run, pass its ID with --run "
              "(`uip maestro flow eval runs list` lists them).\n")
    evaluator_pass = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    category = defaultdict(lambda: [0, 0])
    failures = []
    for row in sorted(rows, key=lambda r: r["DataPoint"]):
        ticket_id = row["DataPoint"].split("-")[0]
        ticket = tickets.get(ticket_id)
        if ticket is None:
            print(f"- {row['DataPoint']}: no ticket {ticket_id} in fixtures, skipped")
            continue
        split = split_name[ticket["attachments"]]
        scores = parse_scores(row.get("EvaluatorScores"))
        reasons = parse_reasons(row.get("Justifications"))
        if str(row.get("Status")) != "completed":
            failures.append((row["DataPoint"], "run", row.get("Status"), row.get("Error", "")))
        for name, score in scores.items():
            kind = kinds.get(name, "judge")
            ok = passed(kind, score, threshold)
            evaluator_pass[name][split][0] += ok
            evaluator_pass[name][split][1] += 1
            if kind == "exact":
                key = (ticket["category"], split)
                category[key][0] += ok
                category[key][1] += 1
            if not ok:
                failures.append((row["DataPoint"], name, score, reasons.get(name, "")))

    print("| Evaluator | No attachments | With attachments |")
    print("|---|---|---|")
    for name, splits in evaluator_pass.items():
        cells = [f"{splits[s][0]}/{splits[s][1]}" if splits[s][1] else "-"
                 for s in ("no attachments", "with attachments")]
        print(f"| {name} | {cells[0]} | {cells[1]} |")

    if category:
        print("\n| Expected category | No attachments | With attachments |")
        print("|---|---|---|")
        for cat in sorted({c for c, _ in category}):
            cells = [f"{category[(cat, s)][0]}/{category[(cat, s)][1]}"
                     if category[(cat, s)][1] else "-"
                     for s in ("no attachments", "with attachments")]
            print(f"| {cat} | {cells[0]} | {cells[1]} |")

    if failures:
        print("\nFailing:")
        for point, name, score, reason in failures:
            short = " ".join(str(reason).split())[:200]
            print(f"- {point}, {name} ({score}): {short}")

    if previous_rows == []:
        print("\nNo earlier completed run of this set to compare with.")
    elif previous_rows is not None:
        before = {r["DataPoint"]: r.get("EvaluatorScores", "") for r in previous_rows}
        print("\nCompared with the run before:")
        print("| Test case | Before | Now |")
        print("|---|---|---|")
        for row in sorted(rows, key=lambda r: r["DataPoint"]):
            now = row.get("EvaluatorScores", "")
            if before.get(row["DataPoint"]) != now:
                print(f"| {row['DataPoint']} | {before.get(row['DataPoint'], '-')} | {now} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project", required=True,
                        help="Flow project folder, for example SupportInbox/1-2-build-evals")
    parser.add_argument("--set", action="append", dest="sets",
                        help="Eval set name; repeatable (default: every set in the project)")
    parser.add_argument("--run", help="Eval set run ID (default: the latest run of each set)")
    parser.add_argument("--compare", action="store_true",
                        help="Also show what changed since the previous completed run")
    parser.add_argument("--wait", action="store_true", help="Wait for a running run to finish")
    parser.add_argument("--threshold", type=float, default=0.7,
                        help="Pass mark for LLM judges (default 0.7)")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")

    project = Path(args.project).resolve()
    if not (project / "project.uiproj").exists():
        sys.exit(f"{project} isn't a Flow project folder (no project.uiproj).")
    uip = uip_cli()
    tickets = load_tickets()
    kinds = load_evaluators(project)
    for eval_set in args.sets or set_names(project):
        run, previous = pick_runs(uip, project, eval_set, args.run, args.compare, args.wait)
        rows = results(uip, project, eval_set, run["EvalSetRunId"])
        previous_rows = results(uip, project, eval_set, previous["EvalSetRunId"]) \
            if previous else ([] if args.compare else None)
        report(eval_set, run, rows, previous_rows, tickets, kinds, args.threshold)


if __name__ == "__main__":
    main()
