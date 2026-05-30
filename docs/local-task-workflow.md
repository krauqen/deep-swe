# Local Task Workflow

Use `scripts/deepswe-task` to create a normal host-side checkout for any DeepSWE
task, edit it with VS Code or Codex, and run the benchmark verifier in Docker.

## One Task

```bash
scripts/deepswe-task setup prometheus-typed-label-sorting
scripts/deepswe-task code prometheus-typed-label-sorting
scripts/deepswe-task codex prometheus-typed-label-sorting
scripts/deepswe-task verify prometheus-typed-label-sorting
```

The editable repository is stored at:

```text
workspaces/prometheus-typed-label-sorting/app
```

The verifier runs against a disposable copy at
`workspaces/<task>/.verify-run/app`, so hidden test patches do not pollute the
source tree you are editing.

## VS Code Over SSH

Create the workspace on the machine that has Docker and this DeepSWE repo. From
your client machine, open the generated app path with VS Code Remote SSH:

```bash
code --remote ssh-remote+<host> /path/to/deep-swe/workspaces/<task>/app
```

You can also print the exact command:

```bash
scripts/deepswe-task ssh-code prometheus-typed-label-sorting <host>
```

## Useful Commands

`scripts/deepswe-task codex <task>` starts interactive Codex with the task prompt
and prepends Docker-backed `go`, `gofmt`, `goimports`, and `make` wrappers to
`PATH`. This lets Codex run normal project commands without requiring those
language tools to be installed on the host.

Codex's normal `workspace-write` sandbox cannot access the Docker socket, so
Docker-backed tools may ask for approval. For a task session where Codex should
freely run `go test`, `gofmt`, and `make` through Docker, use:

```bash
scripts/deepswe-task codex <task> --allow-docker
```

This uses Codex `danger-full-access`, so only use it for task workspaces you are
comfortable trusting.

```bash
scripts/deepswe-task proxy-tools <task>
```

Creates the same wrappers for a manual terminal session. After it prints the
`export PATH=...` command, paste that into your shell and commands like
`go test ./...` will execute inside the task Docker image.

```bash
scripts/deepswe-task shell <task>
```

Starts an interactive shell in the task Docker image with your editable app
mounted as `/app`.

```bash
scripts/deepswe-task diff <task>
```

Prints a binary-safe diff from the task base commit.

```bash
scripts/deepswe-task status <task>
```

Shows the workspace paths and current git status.

## Recreate a Workspace

```bash
scripts/deepswe-task setup <task> --reset
```

This deletes and recreates only `workspaces/<task>/app`.
