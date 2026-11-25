Update the workflow as follows:

- Give the agent that classifies the email its PDF and image attachments, and have it read
  them with the Analyze Files tool to extract the account ID, amount and error code. The
  agent should use what it extracts to decide the category and the reply. Other attachments
  aren't read, but they're still attached to the ticket.
- Leave refund requests handled as they are for now. Deciding refunds is the next step.

Follow the known-issue workarounds in this repo's AGENTS.md.
