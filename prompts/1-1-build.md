Build a Maestro Automate workflow for our Gmail support inbox. When a new email arrives in
the inbox, classify it using only its sender, subject and body as billing (anything about an
invoice, charge or payment), bug, how-to, other or spam. File every email as a Jira ticket in the Support space, with the category as the work
type and, if the email has attachments, those attached to the ticket. For anything that isn't spam, also post a short
summary to #support in Slack with a link to the ticket, and save a draft reply in Gmail;
spam waits in Jira for a weekly review. Finish by marking the email as read. Return the
category, the reply text and whether the customer asked for a refund as the workflow's
outputs, so we can evaluate it.

Follow the flow notes in this repo's AGENTS.md.

Guidance for a faster, more predictable build (optional; without it the build takes longer
and varies more):

- Add a manual trigger to the same workflow that takes a Gmail message ID, so you can test
  it on any email in the inbox.
- Attach the download step's whole output to the Jira ticket
  (`$vars.<download step id>.output`). The skill's example binds `.Response`, which fails.
- Run `uip maestro flow format` before the last validate.
