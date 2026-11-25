Update the workflow as follows:

- For refund requests, including emails that dispute a charge and ask us to fix it without
  saying "refund", look up the customer's account with a "Billing lookup (mock)" step, using
  the account ID the classifier extracts. Then add an agent that checks the request against
  that account and our refund policy (in `company-data/`): whether it's allowed, for which
  charge, the amount and the reason.
    - Route allowed refunds on the amount with a decision step, not in the agent:
      $50 or less go to an Accounts Payable step automatically; over $50 wait for a
      person to approve or reject them in Action Center, and the reply says once that the
      refund is under review. File the
      ticket and send the "under review" reply right away, without waiting for the
      approval. Once approved, they go to Accounts Payable too, and the refund ID is added
      to the ticket as a comment; if rejected, add a comment saying so to the ticket.
    - Decline the rest, and give the reason in the reply.
- When there's a refund ID, include it in the reply and the Jira ticket.
- Add the refund decision (auto_approve, human_approval or decline) and its reason to the
  workflow's outputs, so the refunds eval can score them.
- Give the manual trigger an autoApprove input (default false). When it's true, a
  decision step skips the Action Center task and continues as if a person had approved
  the refund, so an eval run doesn't wait for a person. The refund decision stays
  human_approval. Set it to true in the existing eval sets' inputs.

Follow the known-issue workarounds in this repo's AGENTS.md.

For a predictable demo:

- We don't have a billing system in this demo, so make "Billing lookup (mock)" a script
  step with the data from `company-data/accounts.json` copied into it. Put the refund
  policy in the instructions of the agent that checks the request.
- We don't have an Accounts Payable system either, so make the Accounts Payable step a
  script named "Accounts Payable (mock)" that returns a refund ID made from the invoice
  number, such as RF-INV-2026-11-0032.
- The demo data is from November 2026, so when the refund check applies the policy's time
  limits, use 2026-12-01 as today's date.
- Leave the Action Center approval task unassigned.
