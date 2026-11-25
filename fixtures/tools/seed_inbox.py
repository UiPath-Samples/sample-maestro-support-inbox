"""Send fixture emails into the demo support inbox.

Each ticket in fixtures/tickets/ is sent as a new email, with its attachments, through
your Gmail connection in UiPath Integration Service. The email goes from the connected
inbox to itself, so it lands in the inbox the workflow watches. The fictional customer's
address goes in Reply-To, because Gmail only sends from the connected account.

Needs Python 3.9+ and the `uip` CLI, signed in to the tenant that holds the connection
(`uip login`). No other packages.

Examples:

    # Preview what would be sent
    python fixtures/tools/seed_inbox.py --connection-id <id> --ids E01 E08 --dry-run

    # Send four emails
    python fixtures/tools/seed_inbox.py --connection-id <id> --to you@gmail.com --ids E01 E08 E17 E33

    # Send every ticket
    python fixtures/tools/seed_inbox.py --connection-id <id> --to you@gmail.com --all

Find the connection ID with `uip is connections list --all-folders`.

Each send records the ticket's Gmail message ID in fixtures/seeded-ids.json (ticket ID ->
message ID). Eval sets use it to run each ticket through the workflow's manual trigger.
The IDs belong to your inbox, so the file is not committed.
"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent
TICKETS = FIXTURES / "tickets"


def uip_session() -> dict:
    """Return the uip session (base URL, org, tenant, access token)."""
    uip = shutil.which("uip.cmd") or shutil.which("uip")
    if not uip:
        sys.exit("The uip CLI isn't on PATH. Install it and run `uip login` first.")
    out = subprocess.run(
        [uip, "login", "refresh", "--output", "json"],
        capture_output=True, text=True, check=False,
    )
    try:
        data = json.loads(out.stdout)["Data"]
        if not data.get("AccessToken"):
            raise KeyError("AccessToken")
    except (json.JSONDecodeError, KeyError, TypeError):
        sys.exit("Couldn't read a uip session. Run `uip login` and try again.\n" + out.stderr)
    return data


def multipart(fields: dict[str, str], files: list[tuple[str, Path, str]]) -> tuple[bytes, str]:
    """Encode form fields and files as multipart/form-data."""
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n'
            f"Content-Type: application/json\r\n\r\n".encode() + value.encode() + b"\r\n"
        )
    for name, path, content_type in files:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{path.name}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
            + path.read_bytes() + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def send(session: dict, connection_id: str, ticket: dict, to: str) -> str:
    url = (
        f"{session['BaseUrl']}/{session['OrganizationId']}/{session['TenantName']}"
        f"/elements_/v3/element/instances/{connection_id}/SendEmail"
    )
    fields = {
        "body": json.dumps({
            "To": to,
            "Subject": ticket["subject"],
            # The connector sends the body as HTML, so keep the line breaks
            "Body": html.escape(ticket["body"]).replace("\n", "<br>\n"),
            "ReplyTo": ticket["from"]["email"],
        })
    }
    files = []
    for att in ticket.get("attachments", []):
        path = FIXTURES / att["file"]
        content_type = att.get("content_type") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        files.append(("file", path, content_type))
    payload, content_type = multipart(fields, files)
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {session['AccessToken']}",
        "Content-Type": content_type,
        # The default Python user agent is blocked at the edge (403, error code 1010)
        "User-Agent": "support-inbox-sample-seeder/1.0",
        "x-uipath-source": "UiPath.CodingAgent",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"HTTP {err.code}: {err.read().decode(errors='replace')[:500]}") from err
    return body.get("id", "(no id returned)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--connection-id", required=True, help="Gmail connection ID in Integration Service")
    parser.add_argument("--to", help="The connected inbox's address (required unless --dry-run)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ids", nargs="+", help="Ticket IDs to send, for example E01 E33")
    group.add_argument("--all", action="store_true", help="Send every ticket")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between emails (default 2)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent, send nothing")
    parser.add_argument("--ids-file", default=str(FIXTURES / "seeded-ids.json"),
                        help="Where to record ticket ID -> Gmail message ID (default fixtures/seeded-ids.json). "
                             "Existing entries are kept and updated.")
    args = parser.parse_args()

    ids = sorted(p.parent.name for p in TICKETS.glob("E*/ticket.json")) if args.all else args.ids
    tickets = []
    for tid in ids:
        path = TICKETS / tid / "ticket.json"
        if not path.exists():
            sys.exit(f"No ticket {tid} at {path}")
        tickets.append(json.loads(path.read_text(encoding="utf-8")))

    if args.dry_run:
        for t in tickets:
            atts = ", ".join(Path(a["file"]).name for a in t.get("attachments", [])) or "none"
            print(f"{t['id']}  {t['subject']!r}  reply-to {t['from']['email']}  attachments: {atts}")
        return
    if not args.to:
        sys.exit("--to is required when sending")

    session = uip_session()
    ids_path = Path(args.ids_file)
    try:
        seeded = json.loads(ids_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        seeded = {}
    for i, t in enumerate(tickets):
        if i:
            time.sleep(args.delay)
        try:
            msg_id = send(session, args.connection_id, t, args.to)
            print(f"{t['id']}  sent  {msg_id}  {t['subject']!r}")
            seeded[t["id"]] = msg_id
        except RuntimeError as err:
            print(f"{t['id']}  FAILED  {err}", file=sys.stderr)
    # Ticket ID -> Gmail message ID, for eval sets that run tickets through the manual trigger
    ids_path.write_text(json.dumps(dict(sorted(seeded.items())), indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"Message IDs written to {ids_path}")


if __name__ == "__main__":
    main()
