Get my accounts and inbox ready for this workshop. Use the scripts in fixtures/tools/ for
anything that touches the inbox or the eval sets: don't send email or edit eval sets
yourself, and don't open the tickets in fixtures/tickets.

1. Check the tools: the `uip` CLI (`uip --version`), that I'm signed in (`uip login status`),
   and Python 3.9 or later. If anything is missing, tell me what and stop.
2. List my connections with `uip is connections list --all-folders`. I need one Gmail, one
   Jira and one Slack connection, each enabled and in the Shared folder. Tell me if one is
   missing, disabled or in another folder. If there's more than one of a kind, ask me which
   to use.
3. Ask me for my support inbox's email address.
4. Load the test emails into my inbox with fixtures/tools/seed_inbox.py and --all. Run it
   with --dry-run first and tell me how many emails it will send. If fixtures/seeded-ids.json
   already has IDs, ask me before sending again: each send is a new email with a new ID, and
   a workflow I've already deployed would run on every one of them.
5. Check the eval sets with fixtures/tools/refresh_evals.py. The ones in SupportInbox/ ship
   with placeholder IDs, so expect them to show as stale the first time. If any test case is
   stale, show me which and, once I agree, run it again with --yes. If any ticket isn't seeded, go back
   to step 4 for those tickets.
6. Finish with a short summary: the connections, the emails sent, and the state of the eval
   sets. Then tell me to start a new session in start-here/ for the Build prompt.
