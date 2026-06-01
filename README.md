# [DeepSWE](https://deepswe.datacurve.ai/)

DeepSWE is a benchmark for measuring frontier coding agents on original, long-horizon software engineering tasks drawn from active open-source repositories. The benchmark includes 113 tasks across TypeScript, Go, Python, JavaScript, and Rust, with isolated environments and program-based verifiers.

## Task format

DeepSWE tasks use the [Harbor](https://www.harborframework.com/docs/tasks) task format:

```text
task.toml         Metadata: repository, base commit, language, prebuilt image, resource limits
instruction.md    The prompt the agent sees
environment/      Dockerfile that reproduces the prebuilt image (fallback if the image is unavailable)
tests/            Verifier: test.sh (entry point) + test.patch (test additions, applied at grading time)
solution/         Reference solution (held out from the agent; for human and AI reviewers)
```

The verifier exercises the behavior the prompt describes. It accepts any solution whose observable behavior is correct, regardless of internal symbol names or structure.
The reference patch in `solution/` is never used at grading time; it exists so reviewers can spot-check correctness offline.

## Quickstart

Use [Pier](https://github.com/datacurve-ai/pier) to run the benchmark:

```bash
git clone https://github.com/datacurve-ai/deep-swe
uv tool install datacurve-pier

# Claude Opus 4.7 via Claude Code
export ANTHROPIC_API_KEY=...
pier run -p deep-swe/tasks --agent mini-swe-agent --model anthropic/claude-opus-4-7

# GPT-5.5 via Codex
export OPENAI_API_KEY=...
pier run -p deep-swe/tasks --agent mini-swe-agent --model openai/gpt-5.5
```

## What is Pier

[Pier](https://github.com/datacurve-ai/pier) is a [Harbor](https://www.harborframework.com/docs/tasks)-compatible framework for sandboxed coding-agent evals. It began as a fork of Harbor to support CLI agents in air-gapped tasks: Harbor blocks all outbound traffic in `allow_internet = false` tasks, including dependency installs and LLM API calls. Pier adds per-agent network allowlists, giving agents only the network access they need while keeping the task environment isolated.

Pier also adds more complete trajectory metadata, a better trajectory viewer, and `pier critique run` for analyzing agent trajectories. All leaderboard scores were produced with Pier running `mini-swe-agent` on Modal.

### Agents and models

`mini-swe-agent` is model-agnostic. Pier also drives `claude-code`, `codex`, `gemini-cli`, and `opencode` directly. Pass `--env modal` to run in parallel sandboxes on Modal.

### Subsets and single tasks

Deterministic random subset of the 113-task corpus:

```bash
pier run -p deep-swe/tasks --agent mini-swe-agent --n-tasks 10 --sample-seed 0
```

Single task:

```bash
pier run -p deep-swe/tasks/<task-id> --agent mini-swe-agent
```

## Local human workflow

For editing a task directly with VS Code/Codex and then running the verifier:

```bash
scripts/deepswe-task setup prometheus-typed-label-sorting
scripts/deepswe-task up prometheus-typed-label-sorting
scripts/deepswe-task exec prometheus-typed-label-sorting -- go test ./...
scripts/deepswe-task code prometheus-typed-label-sorting
scripts/deepswe-task codex prometheus-typed-label-sorting
scripts/deepswe-task verify prometheus-typed-label-sorting
scripts/deepswe-task down prometheus-typed-label-sorting
```

This stores editable source at `workspaces/<task-id>/app` and runs verification
inside the task Docker image against a disposable copy. The persistent dev
container lets host-side Codex keep its auth outside Docker while project
commands run inside the task image. See `docs/local-task-workflow.md` for the
SSH and repeatable per-task workflow.
