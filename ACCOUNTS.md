# Set up the accounts

The workflow reads a support inbox, files tickets in Jira and posts to Slack. Before you
paste the Build prompt, you need one of each, connected to your UiPath account. All three
have free plans.

Use new accounts made for this sample, not your work or personal ones. The workflow reads
every email in the inbox and acts on it, so give it an inbox that holds nothing else.

> Tip: create the accounts in a separate browser profile. Otherwise Google and Atlassian
> may sign you in with an account you already use.

## 1. Create a Gmail inbox

1. Go to <https://accounts.google.com/signup> and create a new account.
1. Google asks for a phone number and a recovery email. Use your own; they're only for
   verifying and recovering the account.
1. Note the address. This is your support inbox, and you'll sign up for Jira and Slack
   with it.

## 2. Create a Jira project

Jira now calls a project a **space**. The UiPath connector and the Jira API still say project; they mean the same thing.

1. Sign up for Jira's free plan at <https://www.atlassian.com/software/jira/free>, using
   your new Gmail address.
1. Choose a site name. Your site is `https://<site-name>.atlassian.net`.
1. When asked for a template, choose **Kanban**. New tickets land on the board in
   **To Do**, where you can watch them arrive.
1. Name the space **Support**.
1. Keep the default statuses (To Do, In Progress, Done) and select **Next**.
1. When asked to invite teammates, select **Do this later**.
1. Clean up the sample data Jira creates, so the workflow has only one space to choose:
   - Delete the **(Example) ...** space from the sidebar (**⋯** > **Move to trash**).
   - In **Support**, select the sample work items (Task 1, Task 2, Subtask 2.1) and
     delete them.
1. Optional: change the space key. The Kanban template sets it to `KAN`. To use `SUP`
   instead, open **⋯** > **Space settings** > **Details** and edit **Key**.

## 3. Create a Slack workspace

1. Create a new workspace at <https://slack.com/get-started#/createnew>, using your new
   Gmail address.
1. Name the workspace. Any name works; this sample uses **Support Demo**.
1. When asked how you want to use Slack, choose **Other**.
1. When Slack offers Business+, select **Start with the Limited Free Version**. The free
   plan is all this sample needs.
1. Slack creates a channel called `#new-channel`. Rename it to `support`: select the
   pencil next to the channel name at the top of the window.

## 4. Connect the accounts to UiPath

Sign in to UiPath with the `uip` CLI first:

```bash
uip login
```

Then create one connection per account. Each command opens a browser and waits until you
approve access. In the connection window:

- Choose **Shared** in the folder dropdown, for all three connections. The workflow
  expects them in the same folder.
- Sign in as the account you just created, not your work or personal one.

```bash
uip is connections create uipath-google-gmail
uip is connections create uipath-atlassian-jira
uip is connections create uipath-salesforce-slack
```

Check that all three are there:

```bash
uip is connections list --all-folders
```

Each one should show the state **Enabled** and the folder **Shared**.

To run the finished steps in `SupportInbox/` instead of building your own, you also bind
these connections to that solution. See [Run the finished steps](README.md#run-the-finished-steps)
in the README.

## Troubleshooting

- **A connection landed in the wrong folder.** A connection can't be moved. Delete it with
  `uip is connections delete <id> --yes` and create it again, choosing **Shared**.
- **The Jira connection's name shows your email address.** Jira names a new connection after
  the account that created it, and the name shows in Studio Web and in run traces. Rename it:
  `uip is connections rename <id> --name "Jira (Support)"`.
- **The first debug run fails with "Cannot find a personal robot configured" (409).** A new
  account gets its personal robot only after you sign in to Studio Web and run a debug there
  once. Check with `uip or sessions list-user-executors`.
