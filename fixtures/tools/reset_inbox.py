r"""Reset the demo accounts between runs: archive the inbox, trash drafts, delete Jira tickets.

Run it before seeding (seed_inbox.py) so a test or a dry run starts from an empty inbox:

- **Inbox:** archives every email in INBOX. Archived mail stays in All Mail.
- **Drafts:** moves every Gmail draft to Trash (Gmail empties Trash after 30 days).
- **Jira:** deletes every ticket in one project. This can't be undone, and Jira doesn't
  reuse ticket numbers, so the next ticket keeps counting from the last one. The Jira
  account behind the connection needs permission to delete work items in that space;
  without it every delete fails with 403 Forbidden.

Slack isn't covered. The Slack connector can't read channel history (its sign-in has no
`channels:history` scope), so there's no way to find the workflow's posts. Delete them in
Slack, or leave them.

It changes nothing unless you pass --yes. Without it, it lists what it would do.

Needs Python 3.9+ and the `uip` CLI, signed in to the tenant that holds the connections
(`uip login`). No other packages.

Examples:

    # Preview: what's in the inbox and drafts, and which tickets would go
    python fixtures/tools/reset_inbox.py --gmail-connection <id> --inbox --drafts \
        --jira-connection <id> --jira-project SUP

    # Archive the inbox and trash the drafts
    python fixtures/tools/reset_inbox.py --gmail-connection <id> --inbox --drafts --yes

Find connection IDs with `uip is connections list --all-folders`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

GMAIL = "uipath-google-gmail"
JIRA = "uipath-atlassian-jira"
# ListEmails returns about 10 emails per call whatever the page size, and its next-page
# token repeats earlier results, so each target is cleared in passes until a list comes back
# empty. MAX_PASSES stops a loop if something can't be removed.
MAX_PASSES = 50


def uip_cli() -> str:
    uip = shutil.which("uip.cmd") or shutil.which("uip")
    if not uip:
        sys.exit("The uip CLI isn't on PATH. Install it and run `uip login` first.")
    return uip


def run(uip: str, verb: str, connector: str, resource: str, connection: str, query: str,
        body: str | None = None) -> dict:
    """Run `uip is resources run <verb>` and return its parsed JSON envelope."""
    cmd = [uip, "is", "resources", "run", verb, connector, resource,
           "--connection-id", connection, "--query", query, "--output", "json"]
    if body is not None:
        cmd += ["--body", body]
    if verb == "delete":
        cmd.append("--yes")  # the CLI refuses irreversible deletes without it
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"Result": "Failure", "Message": (out.stdout or out.stderr).strip()[:300]}


def items(envelope: dict) -> list[dict]:
    if envelope.get("Result") != "Success":
        sys.exit(f"List failed: {envelope.get('Message')} {envelope.get('Instructions', '')}"[:600])
    data = envelope.get("Data") or {}
    return data.get("items", []) if isinstance(data, dict) else data


def clear(name: str, list_page, describe, act, apply: bool, workers: int) -> None:
    """List a page, act on every item, repeat until the list is empty."""
    page = list_page()
    if not apply:
        print(f"{name}: would clear these, and any more that follow:")
        for it in page:
            print(f"  {describe(it)}")
        if not page:
            print("  (nothing)")
        return
    done = failed = 0
    seen_failed: set[str] = set()
    for _ in range(MAX_PASSES):
        todo = [it for it in page if describe(it) not in seen_failed]
        if not todo:
            break
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(act, todo))
        for it, (ok, msg) in zip(todo, results):
            if ok:
                done += 1
            else:
                failed += 1
                seen_failed.add(describe(it))
                print(f"  FAILED {describe(it)}: {msg}", file=sys.stderr)
        page = list_page()
    else:
        print(f"{name}: stopped after {MAX_PASSES} passes; run it again", file=sys.stderr)
    print(f"{name}: {done} cleared, {failed} failed")


def ok(envelope: dict) -> tuple[bool, str]:
    return envelope.get("Result") == "Success", str(envelope.get("Message", ""))[:200]


def main() -> None:
    # Subjects can hold emoji, which a Windows console (cp1252) can't print
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    parser =argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gmail-connection", help="Gmail connection ID (for --inbox and --drafts)")
    parser.add_argument("--inbox", action="store_true", help="Archive every email in the inbox")
    parser.add_argument("--drafts", action="store_true", help="Move every draft to Trash")
    parser.add_argument("--jira-connection", help="Jira connection ID (for --jira-project)")
    parser.add_argument("--jira-project", help="Delete every ticket in this project key, for example SUP")
    parser.add_argument("--yes", action="store_true", help="Make the changes (default is a preview)")
    parser.add_argument("--workers", type=int, default=4, help="Calls in parallel (default 4)")
    args = parser.parse_args()

    if not (args.inbox or args.drafts or args.jira_project):
        parser.error("choose at least one of --inbox, --drafts, --jira-project")
    if (args.inbox or args.drafts) and not args.gmail_connection:
        parser.error("--inbox and --drafts need --gmail-connection")
    if args.jira_project and not args.jira_connection:
        parser.error("--jira-project needs --jira-connection")

    uip = uip_cli()
    g, j = args.gmail_connection, args.jira_connection

    def email(it: dict) -> str:
        return f"{it.get('ID')}  {it.get('Subject', '')!r}"

    if args.inbox:
        clear("Inbox",
              lambda: items(run(uip, "list", GMAIL, "ListEmails", g, "emailFolder=INBOX")),
              email,
              lambda it: ok(run(uip, "create", GMAIL, "ArchiveEmail", g, f"id={it['ID']}", "{}")),
              args.yes, args.workers)
    if args.drafts:
        clear("Drafts",
              lambda: items(run(uip, "list", GMAIL, "ListEmails", g, "emailFolder=DRAFT")),
              email,
              lambda it: ok(run(uip, "create", GMAIL, "DeleteEmail", g, f"id={it['ID']}", "{}")),
              args.yes, args.workers)
    if args.jira_project:
        clear(f"Jira {args.jira_project}",
              lambda: items(run(uip, "list", JIRA, "search_issues_with_fields", j,
                                f"project={args.jira_project}&pageSize=20")),
              lambda it: f"{it.get('key')}  {(it.get('fields') or {}).get('summary', '')!r}",
              lambda it: ok(run(uip, "delete", JIRA, "issue", j, f"issueId={it['id']}")),
              args.yes, args.workers)
    if not args.yes:
        print("\nPreview only. Run again with --yes to make these changes.")


if __name__ == "__main__":
    main()
