#!/usr/bin/env python3
"""Summarize DeepSWE job token usage and cost from ./jobs artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Usage:
    input_tokens: int = 0
    cache_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = 0.0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.cache_tokens += other.cache_tokens
        self.output_tokens += other.output_tokens
        if self.cost_usd is None or other.cost_usd is None:
            self.cost_usd = None
        else:
            self.cost_usd += other.cost_usd

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class Trial:
    path: Path
    model: str | None
    status: str
    usage: Usage
    source: str


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def int_field(data: dict[str, Any], name: str) -> int:
    value = data.get(name, 0)
    return value if isinstance(value, int) else 0


def usage_from_agent_result(result: dict[str, Any]) -> Usage | None:
    agent_result = result.get("agent_result")
    if not isinstance(agent_result, dict):
        return None
    return Usage(
        input_tokens=int_field(agent_result, "n_input_tokens"),
        cache_tokens=int_field(agent_result, "n_cache_tokens"),
        output_tokens=int_field(agent_result, "n_output_tokens"),
        cost_usd=agent_result.get("cost_usd")
        if isinstance(agent_result.get("cost_usd"), (int, float))
        else None,
    )


def model_from_config(config: dict[str, Any] | None) -> str | None:
    if not config:
        return None
    agent = config.get("agent")
    if not isinstance(agent, dict):
        return None
    model = agent.get("model_name")
    return model if isinstance(model, str) else None


def usage_from_session_logs(trial_dir: Path) -> Usage | None:
    sessions = sorted((trial_dir / "agent" / "sessions").glob("**/*.jsonl"))
    if not sessions:
        return None

    total = Usage(cost_usd=None)
    found = False
    for session in sessions:
        last_usage: dict[str, Any] | None = None
        try:
            with session.open() as f:
                for line in f:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    payload = event.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue
                    info = payload.get("info")
                    if not isinstance(info, dict):
                        continue
                    usage = info.get("total_token_usage")
                    if isinstance(usage, dict):
                        last_usage = usage
        except OSError:
            continue

        if last_usage:
            found = True
            total.input_tokens += int_field(last_usage, "input_tokens")
            total.cache_tokens += int_field(last_usage, "cached_input_tokens")
            total.output_tokens += int_field(last_usage, "output_tokens")

    return total if found else None


def estimate_cost(
    usage: Usage,
    input_per_mtok: float | None,
    cached_input_per_mtok: float | None,
    output_per_mtok: float | None,
    empirical_per_mtok: float | None,
) -> float | None:
    if usage.cost_usd is not None:
        return usage.cost_usd
    if (
        input_per_mtok is not None
        and cached_input_per_mtok is not None
        and output_per_mtok is not None
    ):
        uncached_input = max(usage.input_tokens - usage.cache_tokens, 0)
        return (
            uncached_input * input_per_mtok
            + usage.cache_tokens * cached_input_per_mtok
            + usage.output_tokens * output_per_mtok
        ) / 1_000_000
    if empirical_per_mtok is not None:
        return usage.total_tokens * empirical_per_mtok / 1_000_000
    return None


def find_trial_dirs(job_dir: Path) -> list[Path]:
    trial_dirs = []
    for child in sorted(job_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "config.json").exists() or (child / "result.json").exists():
            trial_dirs.append(child)
    return trial_dirs


def read_trial(trial_dir: Path, include_running: bool) -> Trial | None:
    result = load_json(trial_dir / "result.json")
    config = load_json(trial_dir / "config.json")
    model = model_from_config(config)

    if result:
        model = model or model_from_config(result.get("config") if isinstance(result.get("config"), dict) else None)
        usage = usage_from_agent_result(result)
        if usage:
            status = "finished" if result.get("finished_at") else "result"
            return Trial(trial_dir, model, status, usage, "result.json")

    if include_running:
        usage = usage_from_session_logs(trial_dir)
        if usage:
            return Trial(trial_dir, model, "partial", usage, "agent/sessions")

    return None


def money(value: float | None) -> str:
    return "n/a" if value is None else f"${value:,.4f}"


def tokens(value: int) -> str:
    return f"{value:,}"


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for i, row in enumerate(rows):
        print("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)))
        if i == 0:
            print("  ".join("-" * width for width in widths))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate total tokens and cost for DeepSWE jobs under ./jobs."
    )
    parser.add_argument("jobs_dir", nargs="?", default="jobs", type=Path)
    parser.add_argument(
        "--include-running",
        action="store_true",
        help="Include partial usage from agent session JSONL files when a trial has no agent_result.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Print per-trial rows in addition to per-job totals.",
    )
    parser.add_argument("--input-per-mtok", type=float, help="Uncached input price per 1M tokens.")
    parser.add_argument("--cached-input-per-mtok", type=float, help="Cached input price per 1M tokens.")
    parser.add_argument("--output-per-mtok", type=float, help="Output price per 1M tokens.")
    args = parser.parse_args()

    jobs_dir = args.jobs_dir
    if not jobs_dir.exists():
        raise SystemExit(f"{jobs_dir} does not exist")

    job_dirs = sorted(path for path in jobs_dir.iterdir() if path.is_dir())
    by_job: dict[Path, list[Trial]] = {}
    completed = Usage()

    for job_dir in job_dirs:
        trials = []
        for trial_dir in find_trial_dirs(job_dir):
            trial = read_trial(trial_dir, args.include_running)
            if not trial:
                continue
            trials.append(trial)
            if trial.usage.cost_usd is not None:
                completed.add(trial.usage)
        by_job[job_dir] = trials

    empirical_per_mtok = None
    if completed.cost_usd and completed.total_tokens:
        empirical_per_mtok = completed.cost_usd / completed.total_tokens * 1_000_000

    grand = Usage(cost_usd=0.0)
    rows = [["job", "trials", "input", "cached", "output", "total", "cost"]]

    for job_dir, trials in by_job.items():
        job_usage = Usage(cost_usd=0.0)
        for trial in trials:
            estimated = estimate_cost(
                trial.usage,
                args.input_per_mtok,
                args.cached_input_per_mtok,
                args.output_per_mtok,
                empirical_per_mtok,
            )
            usage = Usage(
                input_tokens=trial.usage.input_tokens,
                cache_tokens=trial.usage.cache_tokens,
                output_tokens=trial.usage.output_tokens,
                cost_usd=estimated,
            )
            job_usage.add(usage)
        grand.add(job_usage)
        rows.append(
            [
                str(job_dir),
                str(len(trials)),
                tokens(job_usage.input_tokens),
                tokens(job_usage.cache_tokens),
                tokens(job_usage.output_tokens),
                tokens(job_usage.total_tokens),
                money(job_usage.cost_usd),
            ]
        )

    rows.append(
        [
            "TOTAL",
            str(sum(len(trials) for trials in by_job.values())),
            tokens(grand.input_tokens),
            tokens(grand.cache_tokens),
            tokens(grand.output_tokens),
            tokens(grand.total_tokens),
            money(grand.cost_usd),
        ]
    )
    print_table(rows)

    if args.details:
        print()
        detail_rows = [["trial", "status", "source", "model", "input", "cached", "output", "cost"]]
        for trials in by_job.values():
            for trial in trials:
                estimated = estimate_cost(
                    trial.usage,
                    args.input_per_mtok,
                    args.cached_input_per_mtok,
                    args.output_per_mtok,
                    empirical_per_mtok,
                )
                detail_rows.append(
                    [
                        str(trial.path),
                        trial.status,
                        trial.source,
                        trial.model or "",
                        tokens(trial.usage.input_tokens),
                        tokens(trial.usage.cache_tokens),
                        tokens(trial.usage.output_tokens),
                        money(estimated),
                    ]
                )
        print_table(detail_rows)

    if empirical_per_mtok is not None:
        print()
        print(f"Empirical completed-trial blended rate: ${empirical_per_mtok:,.4f}/1M total tokens")
    if args.include_running and not (
        args.input_per_mtok and args.cached_input_per_mtok and args.output_per_mtok
    ):
        print("Partial trial costs use that blended rate unless explicit --*-per-mtok rates are supplied.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
