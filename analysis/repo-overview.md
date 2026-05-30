# DeepSWE Repository Overview

## Purpose

DeepSWE is a benchmark corpus for evaluating coding agents on long-horizon software engineering tasks from active open-source repositories. The repo itself is mostly task data and local benchmark run output; the runner is external, typically `pier`.

## Top-Level Layout

- `README.md`: benchmark overview, task format, and Pier quickstart.
- `tasks/`: the 113 benchmark tasks.
- `jobs/`: local Pier run outputs.
- `.pier-codex-chatgpt-allowlist.toml`: local Codex/Pier allowlist config, currently untracked.

## Task Structure

Each task under `tasks/<task-id>/` follows the Harbor/Pier task format:

- `task.toml`: metadata including task id, target repository, base commit, language, Docker image, timeouts, resources, and internet policy.
- `instruction.md`: prompt shown to the coding agent.
- `environment/Dockerfile`: fallback Docker build recipe for the target repo at the required base commit.
- `tests/test.sh`: verifier entry point.
- `tests/test.patch`: tests applied at grading time.
- `solution/solve.sh`: helper that applies the reference solution patch.
- `solution/solution.patch`: reference solution for reviewers; not used for grading.

## Evaluation Flow

1. Pier selects tasks from `tasks/`.
2. Pier creates an isolated Docker environment for each task.
3. The target upstream repo is available inside the task container, usually at `/app`.
4. The agent receives `instruction.md` and edits the checked-out target repo.
5. The verifier captures the agent diff as `model.patch`.
6. The verifier applies `tests/test.patch`.
7. The verifier runs baseline tests and new task-specific tests.
8. The verifier writes reward output, usually `1` for pass or `0` for fail.

## Task Environment Model

The DeepSWE task payloads are Docker-based. Each `task.toml` points at a prebuilt
Docker image in `[environment].docker_image`, and each task also includes an
`environment/Dockerfile` that can reproduce that image if the prebuilt image is
not used or a forced rebuild is requested. The Dockerfile clones the upstream
repository, checks out the task's base commit, installs dependencies, and leaves
the repo ready for the agent under `/app`.

The per-task Dockerfiles are mostly simple and templated, not deeply bespoke
container systems. All 113 task Dockerfiles currently use the same base image,
`public.ecr.aws/x8v8d7g8/mars-base:latest`, and all 113 clone an upstream GitHub
repository at a fixed commit. Most are short: 83 are 10 lines or fewer, 22 are
11-20 lines, and only 8 are longer than 20 lines. The common shape is
`FROM mars-base`, `WORKDIR /app`, `git clone ... && git checkout ...`, one or
two dependency warm-up commands, then `CMD ["/bin/bash"]`.

The repo-specific tailoring is mainly dependency installation. Go tasks usually
run `go mod download`; Python tasks run `pip install`/editable installs; JS/TS
tasks run `npm`, `pnpm`, or occasionally `bun`; Rust tasks run `cargo fetch`.
Outliers install system packages or generated assets needed by a specific repo,
for example MongoDB/Node setup in `eicrud-keyset-pagination-cursor`, a long
pinned dependency list in `aiomonitor-task-snapshots-diff`, browser deps for a
Playwright-based task, or Deno bootstrapping for `cliffy-config-file-parsing`.

`public.ecr.aws/x8v8d7g8/mars-base:latest` is the shared Datacurve base image
used by every fallback task Dockerfile. Registry metadata labels it
`Mars Quest base image for project submissions`, maintained by `datacurve.ai`,
with OCI source `https://github.com/datacurve-ai/orion` and version `3.0.0`.
As of the registry metadata inspected on 2026-05-30, `latest` is a linux
multi-arch manifest for `amd64` and `arm64`; the amd64 manifest digest is
`sha256:9c024d5dc46f32cee946353232ef99d8f714841ed08bba9b8fb9bb237c77f1ba`.

The image is a general multi-language development base built on Debian
Bookworm/Python. Its config/history show Python 3.12.12 as the default Python,
Python 3.11 also installed, Node.js from Nodesource 24.x, Go 1.25.5, Rust
toolchain 1.92.0, and package managers/tools including pip, poetry, pdm, pipx,
uv/uvx, rye, pnpm, yarn, and bun. It also preinstalls common build and shell
tools such as bash, curl, wget, git, jq, openssh-client, make, gcc/g++, and
Python build dependencies. `/app` is the workdir and default command is
`/bin/bash`.

Pier is the runner/orchestrator rather than the task environment itself. It
understands the Harbor task format, selects tasks, starts an environment backend,
runs agent setup and execution, uploads `tests/` after the agent finishes, runs
the verifier, collects `/logs/{agent,verifier,artifacts}`, and writes job/trial
metadata under `jobs/`.

The local run in `jobs/2026-05-30__00-59-31/` used Pier's `docker` environment
backend. Pier generated Docker Compose overlays for log mounts, resource limits,
agent installation, and filtered egress. For Codex with `allow_internet = false`,
Pier added a Squid egress-proxy container and only allowed the agent to reach
OpenAI/ChatGPT auth domains declared by `.pier-codex-chatgpt-allowlist.toml`.

Pier also has other environment backends such as `modal` and `daytona`, selected
with `pier run --env ...`. For this dataset, though, the task definition remains
container-oriented: prebuilt image or Dockerfile, optional Docker Compose support,
resource limits, internet policy, and Linux/Windows OS selection. Modal is best
understood as a remote sandbox backend for running the same containerized task
shape at scale, not as a different task packaging format.

## Task Corpus

There are 113 tasks total.

Language distribution:

- TypeScript: 35
- Python: 34
- Go: 34
- JavaScript: 5
- Rust: 5

## Local Job Output

The current `jobs/2026-05-30__00-59-31/` directory contains one local Pier run with two Codex trials using model `gpt-5.5`.

Observed results:

- `python-statemachine-state-data-scoping`: completed with reward `0.0`.
- `prometheus-typed-label-sorting`: errored with `RewardFileNotFoundError`, meaning the verifier did not produce `reward.txt` or `reward.json`.

Aggregate job stats reported:

- Total trials: 2
- Completed trials: 2
- Errored trials: 1
- Input tokens: 14,525,944
- Cache tokens: 14,112,256
- Output tokens: 56,657
- Cost: `$10.824278`
