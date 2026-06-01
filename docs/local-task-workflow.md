# Local Task Workflow

Use `scripts/deepswe-task` to create a normal host-side checkout for any DeepSWE
task, edit it with VS Code or Codex, and run the benchmark verifier in Docker.

## One Task

```bash
scripts/deepswe-task setup prometheus-typed-label-sorting
scripts/deepswe-task up prometheus-typed-label-sorting
scripts/deepswe-task exec prometheus-typed-label-sorting -- go test ./...
scripts/deepswe-task code prometheus-typed-label-sorting
scripts/deepswe-task codex prometheus-typed-label-sorting
scripts/deepswe-task verify prometheus-typed-label-sorting
scripts/deepswe-task down prometheus-typed-label-sorting
```

The editable repository is stored at:

```text
workspaces/prometheus-typed-label-sorting/app
```

The verifier runs against a disposable copy at
`workspaces/<task>/.verify-run/app`, so hidden test patches do not pollute the
source tree you are editing.

## Reuse A Previous Patch

After `setup`, you can apply a patch captured from an earlier trial before
opening Codex:

```bash
scripts/deepswe-task setup onedump-dump-encryption-pipeline
scripts/deepswe-task apply-patch onedump-dump-encryption-pipeline \
  jobs/full-run-8-concurrent-2026-05-31/onedump-dump-encryption-pipeline__Gmm5D2h
scripts/deepswe-task codex onedump-dump-encryption-pipeline
```

`apply-patch` accepts either a direct `artifacts/model.patch` path or a trial
directory containing `artifacts/model.patch`.

## Persistent Dev Container

```bash
scripts/deepswe-task up <task>
scripts/deepswe-task exec <task> -- go test ./...
scripts/deepswe-task down <task>
```

`up` starts a long-lived Docker container named `deepswe-<task>-dev` from the
task image. It bind-mounts your editable checkout at `/app`, so edits made on
the host are immediately visible inside the container. It also mounts task tests
read-only at `/tests` and log directories under `/logs`.

`exec` runs a command in that container with `/app` as the working directory.
The container is created automatically if it is missing, and restarted if it
exists but is stopped. The container lives until `down` removes it.

This keeps Codex authentication on the host. Codex edits normal host files, and
project build/test commands run in Docker through `scripts/deepswe-task exec`.

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
and starts the persistent dev container. It prepends a `deepswe-exec` wrapper to
`PATH`, and the prompt tells Codex to run project commands through that wrapper:

```bash
deepswe-exec go test ./...
deepswe-exec make test
deepswe-exec bash -lc 'pytest -q'
```

This lets Codex keep its auth/config on the host while command execution happens
inside the task image.

Codex's normal `workspace-write` sandbox cannot access the Docker socket, so
Docker-backed commands may ask for approval. For a task session where Codex
should freely run commands through Docker, use:

```bash
scripts/deepswe-task codex <task> --allow-docker
```

This uses Codex `danger-full-access`, so only use it for task workspaces you are
comfortable trusting.

```bash
scripts/deepswe-task dev-exec <task>
```

Creates the `deepswe-exec` wrapper for a manual terminal session. After it
prints the `export PATH=...` command, paste that into your shell.

```bash
scripts/deepswe-task proxy-tools <task>
```

Creates the legacy per-command `go`, `gofmt`, `goimports`, and `make` wrappers.
Each invocation uses a short-lived `docker run --rm` container instead of the
persistent dev container.

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
