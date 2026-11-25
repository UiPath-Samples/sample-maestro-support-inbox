# Set up your laptop

This sample has you paste prompts into a coding agent, which builds the workflow with the
UiPath skills and the `uip` CLI. This page installs those tools. Setting up the Gmail, Jira and
Slack accounts the workflow connects to is a separate step, in [ACCOUNTS.md](ACCOUNTS.md).

The steps are written for Windows, macOS and Linux, but so far only Windows has been
tested.

## 1. Install the basics

| Tool | Version | Why you need it |
| --- | --- | --- |
| [Git](https://git-scm.com/downloads) | Any recent | Cloning the repo. On Windows it also installs Git Bash, which you'll use to run `uip` (see [Windows](#windows)). |
| [Node.js](https://nodejs.org/) | LTS | The `uip` CLI is an npm package. |
| [Python](https://www.python.org/downloads/) | 3.9 or later | The scripts in `fixtures/tools/` that load test emails into your inbox and clear it afterwards. They need nothing beyond the standard library. |
| [VS Code](https://code.visualstudio.com/) | Any recent | Opening the workflow in the flow editor and running evals from the evaluation panel. |

Check them:

```bash
git --version
node --version
python --version    # on macOS and Linux this may be python3
code --version
```

On Windows, use `python`, not `python3`: `python3` usually opens the Microsoft Store stub
("Python was not found") even when Python is installed.

## 2. Install the VS Code extension

In VS Code, open the Extensions view, search for **UiPath Maestro** and install it.

Or from a terminal:

```bash
code --install-extension uipath.uipath-maestro
```

## 3. Install a coding agent

Any coding agent the UiPath skills support works. This sample was built and tested with
[Claude Code](https://code.claude.com/docs/en/setup).

The other agents the skills support are Cursor, GitHub Copilot, Codex, OpenCode, Kiro,
Windsurf, Antigravity CLI, Devin and UiPath Autopilot.

## 4. Install the `uip` CLI and the UiPath skills

```bash
npm install -g @uipath/cli
uip --version
```

This sample was tested with `uip` 1.206.0.

Sign in to your UiPath Automation Cloud account. A browser opens; pick the organization and
tenant you'll build in.

```bash
uip login
```

Install the UiPath skills for your coding agent. For Claude Code:

```bash
uip skills install --agent claude
```

For another agent, pass its name instead: `cursor`, `copilot`, `codex`, `opencode`, `kiro`,
`windsurf`, `antigravity`, `devin` or `autopilot`.

## 5. Clone the repo

```bash
git clone https://github.com/UiPath-Samples/sample-maestro-support-inbox.git
```

Clone it somewhere with no agent instruction files in the folders above it, such as a new
folder in your home directory. A coding agent reads instruction files (`CLAUDE.md`,
`AGENTS.md` and the like) from every folder above the one it starts in, so a clone inside
another project picks up that project's instructions too.

## 6. Check what your agent loads

Start your coding agent in `start-here/` and ask what context it has loaded. In Claude Code,
run `/context`. You should see this repo's `CLAUDE.md` and the UiPath skills.

Your own user-level instructions, memory and plugins load as well. If they're about other
work, they can change what the agent builds. For a clean run in Claude Code, start it with a
separate configuration folder that holds only the UiPath skills:

```bash
CLAUDE_CONFIG_DIR=~/.claude-workshop claude
```

A new configuration folder signs in again and needs the skills installed into it
(`uip skills install --agent claude`, run with the same `CLAUDE_CONFIG_DIR`).
Run Claude Code in a terminal for this. The VS Code side panel ignores `CLAUDE_CONFIG_DIR`
and loads your usual configuration.

## Windows

Run `uip` from Git Bash, not Windows PowerShell. PowerShell 5.1 strips the quotes from JSON
arguments, so commands that take JSON fail or receive mangled values. Your coding agent
runs `uip` for you, so point its shell at Git Bash if it lets you choose.

The `CLAUDE_CONFIG_DIR=... claude` form above is Git Bash syntax. In PowerShell:

```powershell
$env:CLAUDE_CONFIG_DIR = "$HOME\.claude-workshop"; claude
```

## Next

[Set up the accounts](ACCOUNTS.md), then go back to [Getting started](README.md#getting-started).
