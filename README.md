# From demo to production: a support inbox workflow

Sample code for the support inbox demo shown at AI Dev NYC (December 1, 2026).

Agents are easy to demo, but production is hard. This sample grows one workflow, a support
inbox, from a first build to something you can measure, fix and run. A coding agent builds it
with the UiPath skills and the `uip` CLI, and UiPath Maestro runs it.

> Reminder: This is sample code written to accompany a tutorial. It is not production-ready and is not covered by UiPath product support.

## What you will build

| Step | Problem | What changes |
| --- | --- | --- |
| Build | "It works on my laptop" | A workflow that classifies each support email, files it in Jira with its attachments, posts a summary to Slack with a link to the ticket, drafts a reply and marks the email as read. Spam is filed in Jira for a weekly review, with no Slack post or reply. |
| Evaluate | "How do you know it works?" | Eval sets of support emails with known answers score the workflow and show where it fails. |
| Fix | "Real inputs are messy" | First the workflow reads the attachments. Then an agent checks each refund request against the policy: refunds of $50 or less are approved automatically, and larger ones wait for a person to approve them. |

## Prerequisites

- UiPath account - get a free plan if you don't have one using [https://uipath.ly/start-free](https://uipath.ly/start-free).
- Installed locally - Git; Node.js; Python; VS Code; a coding agent; and UiPath `uip` CLI and the UiPath skills.   
*See [SETUP.md](SETUP.md)*
- Service accounts - A Gmail inbox, a Jira project and a Slack workspace to connect the workflow to. You can use free plans.   
*See [ACCOUNTS.md](ACCOUNTS.md)*

## Repo layout

| Folder          | Contents                                                                                                                                                                                                                                                                                                  |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `start-here/`   | This is where you build. Open this empty folder in your IDE and use your coding agent to run the Build prompt.                                                                                                                                                                                            |
| `prompts/`      | The prompts you paste into the coding agent. They are numbered using a `<stage>-<step>` convention: `0-1-setup`, `1-1-build`, `1-2-build-evals`, `2-1-fix` and `2-2-auto-approvals`.                                                                                                                      |
| `SupportInbox/` | The finished workflow snapshots after each step - useful if you want to skip to a particular spot in the workshop.<br>This folder is one UiPath solution, with one project per step. Each project is named after the prompt that produced it.<br><br>To add a step, see [MAINTAINING.md](MAINTAINING.md). |
| `company-data/` | Company data for Fernway (our fictitious company): its customer accounts and refund policy.<br><br>The auto-approvals workshop step uses both of these files.                                                                                                                                             |
| `fixtures/`     | The test email data with their attachments and expected answers, and the scripts that load them into your inbox.<br><br>See [fixtures/README.md](fixtures/README.md).                                                                                                                                     |

## Getting started

1. **Set up your local environment** and clone this repo.   
*See [SETUP.md](SETUP.md).*
2. **Set up the accounts** and connect them to UiPath.   
*See [ACCOUNTS.md](ACCOUNTS.md).*
3. **Load the test emails into your inbox.** The workflow is tested on emails already in the inbox, and the eval sets in step 5 run on these same emails. Start your coding agent in the repo root, not in `start-here/`, and paste [`prompts/0-1-setup.md`](prompts/0-1-setup.md).  
The agent checks your tools and connections, sends the 55 test emails, and points the eval sets in `SupportInbox/` at them. When it's done, close that session: the build should start without the test data in its context.

   Load the inbox before you deploy anything. A deployed workflow acts on every new email, so loading it afterwards runs the workflow 55 times, with an agent call each time. To do this step by hand instead, run these from the repo root:
   ```bash
   uip is connections list --all-folders        # find your Gmail connection ID
   python fixtures/tools/seed_inbox.py --connection-id <gmail-connection-id> --to <your-inbox> --all
   python fixtures/tools/refresh_evals.py --yes
   ```

   `seed_inbox.py` records each email's Gmail message ID in `fixtures/seeded-ids.json`.   
   `refresh_evals.py` writes those IDs into the eval sets in `SupportInbox/`, so git shows those files as changed.   
   *The emails are described in [fixtures/README.md](fixtures/README.md).*
4. **Build.** Start a new agent session in `start-here/` and paste [`prompts/1-1-build.md`](prompts/1-1-build.md). The agent builds the workflow as a UiPath solution in that folder and tests it on the emails in your inbox.
5. **Evaluate.** In the same session, paste [`prompts/1-2-build-evals.md`](prompts/1-2-build-evals.md). The agent builds two eval sets, **triage** and **refunds**, then stops and asks you to run them. Open the solution in VS Code and run the sets from its evaluation panel, one set at a time: start a set only once the one before it has finished. Sets started together share the solution's debug package and make each other fail. Don't run them with `uip maestro flow eval run start` either:  
it uploads its own copy of the solution over the one in Studio Web, which removes the connection bindings, and its runs fail with "Project not found".

   When the runs have finished, tell the agent, and it reports the scores.   
   NOTE - Expect the refunds eval set to fail at this point, because the workflow doesn't decide refunds yet. That's the baseline the next two steps improve on.
6. **Fix - Read the attachments.** In the same session, paste [`prompts/2-1-fix.md`](prompts/2-1-fix.md). The agent has the classifier read PDF and image attachments and use what's in them for the category and the reply. Run the **triage** set again and compare: emails whose details are only in an attachment should now pass. The refunds set still fails.
7. **Decide refunds.** In the same session, paste [`prompts/2-2-auto-approvals.md`](prompts/2-2-auto-approvals.md). The agent adds a refund check against the account and the policy in [`company-data/`](company-data/): refunds of $50 or less are approved automatically, larger ones wait for a person, and the rest are declined. Run both sets again, one at a time, and compare.

   The eval sets skip the approval step. When a live email asks for a refund over $50, the workflow files the ticket, sends the "under review" reply, and leaves an unassigned task in Action Center. Open Action Center in Automation Cloud, assign the task to yourself, and approve or reject it. Approving it issues the refund and adds the refund ID to the ticket as a comment.

### Deploy your build

Debug runs work without deploying. To have the workflow pick up new email on its own, deploy and activate the solution. Ask your coding agent to do it; the UiPath skills cover deploying.

Before deploying, check that every connection the workflow uses is listed in the solution.

Debug runs work without them, but deploying doesn't. From your solution's folder:

```bash
uip solution resources refresh
```

Once it's active, the workflow acts on every new email that reaches the inbox.

### Run the finished steps

[`SupportInbox/`](SupportInbox/) holds the workflow as it stood after each step, built from the prompts for the talk. To run those steps on your own accounts:

1. **Load the test emails into your inbox** (step 3 of [Getting started](#getting-started)).  
Each eval test case passes the workflow a Gmail message ID, and an ID only works on the inbox it was sent to. So the eval sets in `SupportInbox/` ship with placeholders, such as `SEED-E36` for ticket E36, and the setup step replaces them with your IDs. Without that, every test case fails, because no email has a placeholder ID.
2. **Upload the solution** to Studio Web, from `SupportInbox/`:
   ```bash
   uip solution upload .
   ```

   It arrives as a new solution in your tenant, and `uip` writes the new solution ID into your local `SupportInbox.uipx`.
3. **Bind the connections.** An uploaded solution has no connection bindings, so every connector step shows "No debug overwrite configured". In Studio Web, bind the Gmail, Jira and Slack connections to yours. Tickets are filed by the account behind your Jira connection.  
The Slack step and the Jira steps also keep the channel and work types picked in the original accounts, stored as IDs. If a Slack post or a Jira ticket fails after you bind your connections, open that step in VS Code and pick your `#support` channel or work type again.
4. **Send each email to the step you want.** Each step's Gmail trigger only picks up email sent to a plus-address of your inbox: `+step11@` for `1-1-build`, `+step12@` for `1-2-build-evals`, `+step21@` for `2-1-fix` and `+step22@` for `2-2-auto-approvals` (for example `your.name+step22@gmail.com`). Gmail delivers these to your inbox as usual, so all four steps can be deployed at once and each email starts only the step it's addressed to.  
The setup step sends to the plain address, so it doesn't start any of them.
5. **Edit** `2-1-fix` **and** `2-2-auto-approvals` **in VS Code, not Studio Web.** Their classifier takes the email's attachments as a list, and saving the flow in Studio Web can retype that input, which makes the agent fail when it starts.

To add a step of your own, don't copy a project folder as it is. The platform looks up a project's ID, its eval set and evaluator IDs and its inline agent IDs across the whole solution, and a copied folder keeps all of them. Two projects sharing an ID show each other's eval runs, and one can silently run the other's agent. [MAINTAINING.md](MAINTAINING.md) has a script that copies a step with new IDs.

### Start over

To clear what earlier runs left behind, [`fixtures/tools/reset_inbox.py`](fixtures/tools/reset_inbox.py) archives the inbox, moves drafts to Trash and deletes every ticket in a Jira project. It previews until you add `--yes`, and the Jira deletes can't be undone. It can't clear Slack. See [Start over](fixtures/README.md#start-over) in the fixtures README.

A reset doesn't break the eval sets, because archived emails can still be fetched by their message ID. If you want the workflow to see the emails as new again, load the inbox again. The new emails get new IDs, so run `python fixtures/tools/refresh_evals.py --yes` afterwards: it updates every eval set in the repo, including the ones your build made in `start-here/`.

## Tested with

| Component      | Version                                                               |
| -------------- | --------------------------------------------------------------------- |
| `uip` CLI      | 1.206.0                                                               |
| IDE            | Visual Studio Code                                                    |
| Coding Agent   | Claude Code, using Opus 5.5                                           |
| UiPath Maestro | November 23, 2026; tested on both a paid tenant and on a free account |

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first. **Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)**.

---

## License

This sample code is licensed under the MIT License. See the [LICENSE](LICENSE) file.
