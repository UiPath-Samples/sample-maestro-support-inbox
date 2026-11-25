# Maintaining this sample

Notes for whoever changes or extends the workshop: adding a step, editing a step, or
refreshing the test data. If you're following the tutorial, you don't need this file; start
with the [README](README.md).

## How the steps are laid out

`SupportInbox/` is one UiPath solution with a project per step: `1-1-build`, `1-2-build-evals`,
`2-1-fix` and `2-2-auto-approvals`. Each project is named after the prompt in `prompts/` that
produced it, and each one comes from a real run of that prompt. Anything changed by hand
afterwards is described in the commit that made the change.

One solution, rather than one per step, because:

- the Gmail, Jira and Slack connections are bound once and shared by every step;
- in VS Code you switch steps with a tab, not a window, which matters on stage;
- each step's Gmail trigger listens on its own plus-address tag (`+step11@`, `+step12@`,
  `+step21@`, `+step22@`), so all of them can be deployed at once and an email only starts
  the step it's addressed to.

## Adding a step

A new step starts as a copy of the step before it, and the step's prompt then runs on the
copy. Don't copy the folder by hand: **a copied project keeps every internal ID of the
original**, and the platform looks those IDs up across the whole solution. If two projects
share an ID:

- **Project ID:** each project's eval runs show up in the other's evaluation panel, listed by
  eval set ID instead of name.
- **Eval set IDs:** a run of one project's set is the same record as the other's. Deleting it
  in one panel deletes it in both.
- **Inline agent IDs:** a run can use the other project's agent definition, silently. The run
  completes and gives plausible but wrong answers.

`fixtures/tools/copy_checkpoint.py` makes the copy with new IDs for all of these, plus the
agents' tool resources, and gives it its own trigger tag and project name. It also leaves out
the Flow SDK's working files. From the repo root, then from `SupportInbox/`:

```bash
python fixtures/tools/copy_checkpoint.py SupportInbox/<from> SupportInbox/<new> --tag +stepNN@

cd SupportInbox
uip solution projects add ./<new> ./SupportInbox.uipx
uip solution resources refresh
uip maestro flow validate <new>/SupportInbox.flow
```

Then run the step's prompt on the new project, and upload the solution
(`uip solution upload .`). Uploading over the existing Studio Web solution keeps its
connection bindings.

**Check it worked:** `uip maestro flow eval runs list --set <name> --path <new>` returns no
runs, and a run of the new project's sets doesn't show up in the evaluation panel of the
project you copied. The script already checks that no old ID is left in the copy. An ID that
appears in two projects is a bug waiting to happen even when the two definitions are identical
today, because the next change to either one is silently shared.

## Editing a step

**After a prompt recompiles a step.** A prompt that edits the flow through the SDK rebuilds it
from source, which loses changes made afterwards in an editor. Check and redo:

- the steps that `AGENTS.md` says to add with the CLI, after the last compile: the Gmail trigger
  (folder INBOX) and the attachment download step, with its retry settings;
- the trigger's plus-address tag;
- the canvas layout, groups, colors and notes.

**Edit in the VS Code flow editor, not Studio Web.** Opening and saving a flow in Studio Web can
change an agent's list input to a string, and the agent then fails at startup.

**Check which tenant you're signed in to before you save.** The VS Code extension uses the
`uip` CLI's sign-in. Saving a flow while it's signed in to a tenant that doesn't have the
flow's connections clears those connections from the flow's steps. Run
`uip maestro flow validate` after any save; a cleared connection shows as "A connection is
required to run this activity".

**Change agents in their node, not in `agent.json`.** Saving the canvas regenerates each inline
agent's `agent.json` from its node in the `.flow` file, so a change made only in `agent.json` is
lost on the next save. Change an agent's prompt or inputs in its node (or in the SDK source)
instead, and afterwards check that the agent's user prompt in `agent.json` still lists the
attachments it reads.

## Eval sets

**Commit them with placeholder message IDs.** The eval sets in `SupportInbox/` carry
placeholders (`SEED-E36` for ticket E36), because a real Gmail message ID only works on the
inbox it was sent to. Any run of the evals prompt, and any `refresh_evals.py --yes`, writes your
inbox's IDs into the sets. Put the placeholders back before you commit, and refresh again to
keep working:

```bash
python fixtures/tools/refresh_evals.py SupportInbox --placeholders   # before committing
python fixtures/tools/refresh_evals.py SupportInbox --yes            # to use the sets again
```

Both commands change only the local files, never the solution in Studio Web.

**Run them one set at a time**, from VS Code's evaluation panel. Sets started together share the
solution's debug package and fail each other.

## Test data and scripts

The fictional company's data is in `company-data/`. The test emails, their expected results
and the scripts that generate, send, reset and report on them are in `fixtures/`; see
[fixtures/README.md](fixtures/README.md).
