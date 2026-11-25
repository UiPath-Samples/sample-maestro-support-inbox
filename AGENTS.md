<!-- AGENTS.md and CLAUDE.md are kept identical: Claude Code reads CLAUDE.md, other coding
agents read AGENTS.md. In testing, an @AGENTS.md import in CLAUDE.md didn't load when the
agent started in a subfolder, so CLAUDE.md carries the full text. Edit both together. -->

# Notes for coding agents

This repo is a tutorial. People paste the prompts in `prompts/` into a coding agent and build
the workflow themselves, starting from the empty `start-here/` folder.

## When you're building from `start-here/`

If you were started in `start-here/`, or asked to build what one of the prompts describes:

- Work only in the folder you were started in. Build from the prompt you were given, the
  UiPath skills and the user's own tenant and accounts.
- Don't read or copy from `SupportInbox/`, `fixtures/` or the other prompts in `prompts/`,
  unless the prompt you were given names them (the evals prompt uses `fixtures/tickets`
  as its test cases). `SupportInbox/` holds the finished builds and `fixtures/` holds the answers
  the evals score against, so using them otherwise skips the exercise and makes the evals
  meaningless. `company-data/` is the company's own data, and fine to read when a prompt
  points you there.
- Test against the emails already in the user's inbox. Seeding the inbox is the user's step,
  not part of the build.
- Don't hardcode user or account IDs, such as a Jira reporter. The Jira connector marks
  Reporter as required, and an empty value fails with "Reporter is required", so read the
  connection's own account at run time (Jira's current user, the `myself` object) and pass its
  account ID as the reporter.
- Before you finish, run `uip solution resources refresh` and check that every connection
  the flow uses is listed in the solution. Debug runs work without them, but deploying and
  importing the solution don't.

When you're maintaining the repo itself (fixtures, prompts, docs), these limits don't apply. To add a step or copy a checkpoint
in `SupportInbox/`, follow [MAINTAINING.md](MAINTAINING.md).

## Known issues in the Flow tooling

These apply to every flow in this repo, whichever folder you're working in. They work around
issues in the Flow tooling and are needed until those are fixed. Without them the flow
validates, but the Gmail trigger never fires and attachments can't be downloaded.

These workarounds, and the eval notes below, were tested with `uip` 1.206.0 and
`@uipath/maestro-builder-sdk` 6.117.1. On a later version, apply them anyway, and tell the user
if one of them no longer matches what the tooling does.

- Add the Gmail email trigger and the attachment download step with
  `uip maestro flow node add` and `uip maestro flow node configure`, not in SDK source.
- Set the trigger's folder to INBOX: `"eventParameters": {"ParentFolders[*].ID": "INBOX"}`.
- An SDK compile removes steps added this way. Add them after the last compile, and add
  them again after any later SDK change.
- Loop over the bare path `$vars.getEmail.output.Attachments`, behind a decision on
  `$vars.getEmail.output.HasAttachments`. An email with no attachments has no list to loop
  over, and a loop over a missing list faults.
- Give the download step retries, because it fails now and then with a 502 even when it's set
  up correctly. In the node's `inputs`: `"retryEnabled": true, "retryMaxCount": 4,
  "retryInitialDelay": "PT1S", "retryBackoffType": "Exponential", "retryMaxDuration": "PT30S",
  "retryExponentialBase": 2`. Set them again whenever the step is re-added.

- Pass inline agents text, apart from the attachments for the Analyze Files tool. A number or
  an object in an agent's inputs makes the agent fail at startup with "Input validation
  failed". Turn them into strings in a script step before the agent.

- An inline agent that reads attachments with the Analyze Files tool needs them in its prompt,
  not only in its inputs. The model passes each attachment's ID to the tool; if the IDs aren't
  in front of it, it makes one up and the run faults with "Invalid attachment id" (or the
  agent reports the files as unreadable). Put the attachment objects (ID, FullName, MimeType,
  as the download step returns them) in the agent's user prompt, and check that the prompt in
  the compiled `agent.json` refers to the input by its actual name.

- On Windows, run `uip` from Git Bash, not Windows PowerShell. PowerShell 5.1 strips the
  quotes from JSON arguments, so commands that take JSON (node configure, eval data points,
  debug inputs) fail or receive mangled values.

## Known issues in Flow evals

These apply when you build evals for a flow in this repo. Without them the eval sets look
fine, but the runs fail or every step reads an empty output.

- Don't start eval runs with `uip maestro flow eval run start`. It uploads its own copy of the
  solution over the one in Studio Web, which removes the connection bindings, and its runs
  fail with "Project not found". When the sets are ready, stop and ask the user to run them
  from the evaluation panel in VS Code, one set at a time. Sets started together share the
  solution's debug package and fail each other (instances stay Pending, then "Unable to find
  file .bpmn in debug package" or "Failure in the Orchestrator Job"). Read the results
  afterwards with `uip maestro flow eval runs list` and
  `uip maestro flow eval runs results --verbose`.
- Wrap every connector simulation's mock value in `response`, for example
  `--mock-value '{"response": {"key": "SUP-EVAL"}}'`. A connector step reads its output from
  the response, so an unwrapped mock leaves the step's output empty and the next step that
  reads it fails.
- Give each test case its expected output with `--expected`, using all of the workflow's
  outputs (`category`, `replyText` and `refundRequested`). Each evaluator reads its own key
  from it. Use `--criteria` only for an evaluator that scores something the workflow
  doesn't output.
- Never leave an expected value empty. An empty string counts as missing, and the run won't
  start. For a spam email, write out that no reply is expected.
- Pass evaluators to `eval set add --evaluators` by the ID `eval evaluator add` returns, not
  by name. A name is saved as is and doesn't match the evaluator.
- Keep any helper scripts you write outside the repo, in a temporary folder. Scripts left in
  the repo show up as untracked files in the user's clone.
- Run results give each test case's scores and the judges' reasons, but not the workflow's
  actual outputs. For a test case that failed on category, the actual category is in the
  run's trace in VS Code.
