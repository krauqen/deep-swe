#!/usr/bin/env python3
"""Build the static data bundle for the DeepSWE repo visualization."""

from __future__ import annotations

import json
import os
import re
import tomllib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"
ANALYSIS = ROOT / "analysis"
OUT = ROOT / "analysis" / "repo-viz" / "data.js"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def clean_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines()]


def extract_clone_url(text: str) -> str | None:
    match = re.search(r"git\s+clone\s+(?:--depth\s+\d+\s+)?([^\s]+)", text)
    return match.group(1) if match else None


def extract_checkout(text: str) -> str | None:
    match = re.search(r"git\s+checkout\s+([0-9a-fA-F]{7,40}|[^\s&;]+)", text)
    return match.group(1) if match else None


def base_image(text: str) -> str | None:
    for line in clean_lines(text):
        if line.startswith("FROM "):
            return line.removeprefix("FROM ").strip()
    return None


def run_commands(text: str) -> list[str]:
    return [line.strip() for line in clean_lines(text) if line.strip().startswith("RUN ")]


def install_commands(commands: list[str]) -> list[str]:
    installs: list[str] = []
    for command in commands:
        lower = command.lower()
        is_clone = "git clone" in lower and "git checkout" in lower
        warms_deps = any(
            marker in lower
            for marker in [
                "go mod download",
                "pip install",
                "uv sync",
                "npm ",
                "pnpm ",
                "yarn ",
                "bun ",
                "cargo fetch",
                "cargo test",
                "apt-get",
                "deno",
                "playwright install",
            ]
        )
        if warms_deps or not is_clone:
            installs.append(command)
    return installs


def classify_install(command: str) -> list[str]:
    lower = command.lower()
    labels = []
    checks = [
        ("go mod download", "go mod"),
        ("pip install", "pip"),
        ("uv sync", "uv"),
        ("npm ", "npm"),
        ("pnpm ", "pnpm"),
        ("yarn ", "yarn"),
        ("bun ", "bun"),
        ("cargo fetch", "cargo"),
        ("cargo test", "cargo"),
        ("apt-get", "apt-get"),
        ("playwright install", "playwright"),
        ("deno", "deno"),
    ]
    for needle, label in checks:
        if needle in lower:
            labels.append(label)
    return labels or ["custom RUN"]


def line_bucket(line_count: int) -> str:
    if line_count <= 10:
        return "<=10"
    if line_count <= 20:
        return "11-20"
    return ">20"


def load_task(task_dir: Path) -> dict | None:
    toml_path = task_dir / "task.toml"
    docker_path = task_dir / "environment" / "Dockerfile"
    if not toml_path.exists() or not docker_path.exists():
        return None

    task = tomllib.loads(read_text(toml_path))
    metadata = task.get("metadata", {})
    environment = task.get("environment", {})
    docker = read_text(docker_path)
    commands = run_commands(docker)
    installs = install_commands(commands)
    line_count = len(clean_lines(docker))

    return {
        "id": task_dir.name,
        "title": metadata.get("display_title") or metadata.get("original_title") or task_dir.name,
        "description": metadata.get("display_description", ""),
        "category": metadata.get("category", ""),
        "language": metadata.get("language", "unknown"),
        "repo": (metadata.get("repository_url") or "").removeprefix("https://github.com/"),
        "repoUrl": metadata.get("repository_url", ""),
        "baseCommit": metadata.get("base_commit_hash", ""),
        "dockerImage": environment.get("docker_image", ""),
        "allowInternet": environment.get("allow_internet"),
        "cpus": environment.get("cpus"),
        "memoryMb": environment.get("memory_mb"),
        "storageMb": environment.get("storage_mb"),
        "agentTimeoutSec": task.get("agent", {}).get("timeout_sec"),
        "verifierTimeoutSec": task.get("verifier", {}).get("timeout_sec"),
        "path": rel(task_dir),
        "instructionPath": rel(task_dir / "instruction.md"),
        "dockerfilePath": rel(docker_path),
        "testPatchPath": rel(task_dir / "tests" / "test.patch"),
        "solutionPatchPath": rel(task_dir / "solution" / "solution.patch"),
        "dockerfile": docker,
        "dockerLineCount": line_count,
        "dockerLineBucket": line_bucket(line_count),
        "baseImage": base_image(docker),
        "cloneUrl": extract_clone_url(docker),
        "checkout": extract_checkout(docker),
        "runCommands": commands,
        "installCommands": installs,
        "installLabels": sorted({label for command in installs for label in classify_install(command)}),
    }


def load_projects() -> list[dict]:
    path = ANALYSIS / "dataset-projects.json"
    if not path.exists():
        return []
    data = json.loads(read_text(path))
    return data.get("records", [])


def load_jobs() -> list[dict]:
    if os.environ.get("DEEPSWE_REPO_VIZ_INCLUDE_JOBS") != "1":
        return []

    jobs_root = ROOT / "jobs"
    if not jobs_root.exists():
        return []

    jobs = []
    for job_dir in sorted(jobs_root.iterdir()):
        result_path = job_dir / "result.json"
        if not result_path.exists():
            continue
        result = json.loads(read_text(result_path))
        trials = []
        for trial_result in sorted(job_dir.glob("*/result.json")):
            trial = json.loads(read_text(trial_result))
            reward_path = trial_result.parent / "verifier" / "reward.txt"
            reward = read_text(reward_path).strip() if reward_path.exists() else None
            trials.append(
                {
                    "taskName": trial.get("task_name"),
                    "trialName": trial.get("trial_name"),
                    "agent": trial.get("agent_info", {}).get("name"),
                    "model": trial.get("agent_info", {}).get("model_info", {}).get("name"),
                    "reward": reward,
                    "exceptionType": (trial.get("exception_info") or {}).get("exception_type"),
                    "exceptionMessage": (trial.get("exception_info") or {}).get("exception_message"),
                    "inputTokens": (trial.get("agent_result") or {}).get("n_input_tokens"),
                    "outputTokens": (trial.get("agent_result") or {}).get("n_output_tokens"),
                    "costUsd": (trial.get("agent_result") or {}).get("cost_usd"),
                    "steps": trial.get("n_agent_steps"),
                    "startedAt": trial.get("started_at"),
                    "finishedAt": trial.get("finished_at"),
                    "path": rel(trial_result.parent),
                }
            )

        jobs.append(
            {
                "id": result.get("id"),
                "name": job_dir.name,
                "startedAt": result.get("started_at"),
                "finishedAt": result.get("finished_at"),
                "totalTrials": result.get("n_total_trials"),
                "stats": result.get("stats", {}),
                "trials": trials,
                "path": rel(job_dir),
            }
        )
    return jobs


def file_inventory() -> dict:
    ignored_parts = {".git", "jobs", "workspaces", "__pycache__"}
    ignored_names = {".DS_Store"}
    files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not ignored_parts.intersection(path.parts)
        and path.name not in ignored_names
        and path.suffix != ".pyc"
    ]
    by_top = Counter(path.relative_to(ROOT).parts[0] for path in files)
    by_suffix = Counter(path.suffix.lower() or "[none]" for path in files)
    return {
        "totalFiles": len(files),
        "byTopLevel": dict(sorted(by_top.items())),
        "bySuffix": dict(by_suffix.most_common(14)),
    }


def main() -> None:
    tasks = [task for path in sorted(TASKS.iterdir()) if path.is_dir() for task in [load_task(path)] if task]
    projects = load_projects()
    jobs = load_jobs()

    language_counts = Counter(task["language"] for task in tasks)
    category_counts = Counter(task["category"] or "uncategorized" for task in tasks)
    base_counts = Counter(task["baseImage"] or "unknown" for task in tasks)
    line_buckets = Counter(task["dockerLineBucket"] for task in tasks)
    install_counts = Counter(label for task in tasks for label in task["installLabels"])

    data = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repoRoot": "deep-swe",
        "summary": {
            "taskCount": len(tasks),
            "projectCount": len(projects),
            "jobCount": len(jobs),
            "languageCounts": dict(language_counts.most_common()),
            "categoryCounts": dict(category_counts.most_common()),
            "fileInventory": file_inventory(),
        },
        "docker": {
            "taskCount": len(tasks),
            "baseImages": dict(base_counts.most_common()),
            "allUseSameBase": len(base_counts) == 1,
            "cloneCount": sum(1 for task in tasks if task["cloneUrl"]),
            "checkoutCount": sum(1 for task in tasks if task["checkout"]),
            "lineBuckets": {bucket: line_buckets.get(bucket, 0) for bucket in ["<=10", "11-20", ">20"]},
            "installPatterns": dict(install_counts.most_common()),
            "longest": sorted(
                [
                    {
                        "id": task["id"],
                        "title": task["title"],
                        "language": task["language"],
                        "dockerLineCount": task["dockerLineCount"],
                        "dockerfilePath": task["dockerfilePath"],
                        "installLabels": task["installLabels"],
                    }
                    for task in tasks
                ],
                key=lambda task: task["dockerLineCount"],
                reverse=True,
            )[:10],
        },
        "tasks": tasks,
        "projects": projects,
        "jobs": jobs,
        "notes": [
            {
                "title": "Benchmark shape",
                "body": "DeepSWE is task data plus local run output. The runner is external, usually Pier, and each task follows Harbor's metadata, prompt, environment, tests, and reference-solution layout.",
            },
            {
                "title": "Environment pattern",
                "body": "The fallback environments are simple Docker recipes: shared base image, upstream clone at a fixed commit, dependency warm-up, and a bash entrypoint.",
            },
            {
                "title": "Verifier model",
                "body": "The verifier applies hidden task tests after the agent finishes, then writes a reward. Reference solutions are for review and are not part of grading.",
            },
            {
                "title": "Local run signal",
                "body": "The included job output shows a tiny local Pier run using the Docker backend and Codex, including reward, exception, token, and cost metadata.",
            },
        ],
    }

    OUT.write_text(
        "window.REPO_VIZ_DATA = " + json.dumps(data, indent=2, ensure_ascii=True) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(tasks)} tasks and {len(projects)} projects")


if __name__ == "__main__":
    main()
