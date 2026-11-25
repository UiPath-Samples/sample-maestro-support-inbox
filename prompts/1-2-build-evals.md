Create evals for the support inbox workflow, using tickets from fixtures/tickets as test
cases, one for each kind of email we get. Make two eval sets, both on the manual trigger:

1. **triage**, with E01, E08, E17, E26, E29, E33, E35, E36, E39, E42, E44, E47 and E51. Score the
   category with an exact-match evaluator on the category output, against
   expected.category. Score the reply text with an LLM-judge evaluator on the reply output,
   against expected.reply_points. Spam gets no reply, so for E51 the expected reply says that.
2. **refunds**, with E01, E29, E33 and E35. Score the refund decision with an LLM-judge
   evaluator on the whole output, against expected.refund.route (auto_approve,
   human_approval or decline) and expected.refund.reason. The output must state the decision:
   a reply that only says someone will review the request doesn't count. The workflow doesn't decide
   refunds yet, so this set will fail for now. That's the baseline.

For each test case:

- Name it with the ticket ID and expected category, for example E36-billing.
- Pass the ticket's Gmail message ID from fixtures/seeded-ids.json as the manual trigger's
  input.
- Simulate the Jira, Slack, draft-reply and mark-as-read steps with static responses, so a
  run creates nothing real.

Use gpt-4.1-2025-04-14 as the model for both LLM judges. Follow the eval notes in this
repo's AGENTS.md. When the sets are ready, tell me, and I'll run them from VS Code.

When I tell you the runs have finished, show me:

- For each expected category, how many tickets landed in the right category, split by
  tickets with and without attachments.
- The pass rate for the reply and refund evaluators, split the same way.
- The failing ticket IDs, with the reason for each.
