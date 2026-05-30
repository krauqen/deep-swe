#!/usr/bin/env python3
"""Serve the repo visualization with live Pier trajectory endpoints."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = Path(__file__).resolve().parent
JOBS_DIR = ROOT / "jobs"
MAX_TEXT = 6000


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def newest_mtime(paths: list[Path]) -> float | None:
    existing = [path.stat().st_mtime for path in paths if path.exists()]
    return max(existing) if existing else None


def text_from_content(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            text = item.get("text") or item.get("input_text")
            if text:
                parts.append(str(text))
    return "\n".join(parts)


def truncate(text: str, limit: int = MAX_TEXT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n\n... truncated {len(text) - limit:,} chars"


def normalize_jsonl_event(row: dict, index: int) -> dict | None:
    timestamp = row.get("timestamp")
    row_type = row.get("type", "event")
    payload = row.get("payload") or {}

    event = {
        "index": index,
        "timestamp": timestamp,
        "rawType": row_type,
        "kind": "event",
        "role": "event",
        "title": row_type,
        "text": "",
    }

    if row_type == "session_meta":
        event.update(
            {
                "kind": "meta",
                "role": "meta",
                "title": "Session started",
                "text": f"{payload.get('model_provider', '')}/{payload.get('model', '')} in {payload.get('cwd', '')}".strip("/ "),
            }
        )
        return event

    if row_type == "turn_context":
        event.update(
            {
                "kind": "meta",
                "role": "meta",
                "title": "Turn context",
                "text": f"{payload.get('model', '')} · {payload.get('cwd', '')}",
            }
        )
        return event

    if row_type == "event_msg":
        payload_type = payload.get("type", "event")
        event["rawType"] = payload_type
        event["title"] = payload_type.replace("_", " ")
        if payload_type == "user_message":
            event.update(
                {
                    "kind": "message",
                    "role": "user",
                    "title": "User",
                    "text": payload.get("message", ""),
                }
            )
        elif payload_type == "agent_message":
            event.update(
                {
                    "kind": "message",
                    "role": "assistant",
                    "title": "Assistant final",
                    "text": payload.get("message", ""),
                }
            )
        elif payload_type == "token_count":
            usage = (payload.get("info") or {}).get("total_token_usage") or {}
            event.update(
                {
                    "kind": "meta",
                    "role": "meta",
                    "title": "Token count",
                    "text": (
                        f"input {usage.get('input_tokens', 0):,} · "
                        f"cached {usage.get('cached_input_tokens', 0):,} · "
                        f"output {usage.get('output_tokens', 0):,}"
                    ),
                }
            )
        elif payload_type == "task_complete":
            event.update(
                {
                    "kind": "complete",
                    "role": "event",
                    "title": "Task complete",
                    "text": f"Duration: {payload.get('duration_ms', 0)} ms",
                }
            )
        else:
            event["text"] = json.dumps(payload, ensure_ascii=True, indent=2)
        event["text"] = truncate(event["text"])
        return event

    if row_type == "response_item":
        payload_type = payload.get("type", "response_item")
        event["rawType"] = payload_type

        if payload_type == "message":
            role = payload.get("role", "assistant")
            event.update(
                {
                    "kind": "message",
                    "role": role,
                    "title": role.title(),
                    "text": text_from_content(payload.get("content")),
                }
            )
        elif payload_type == "reasoning":
            summary = payload.get("summary") or []
            text = "\n".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in summary
            ).strip()
            event.update(
                {
                    "kind": "meta",
                    "role": "meta",
                    "title": "Reasoning",
                    "text": text or "Encrypted reasoning item",
                }
            )
        elif payload_type in {"function_call", "tool_call"}:
            event.update(
                {
                    "kind": "tool",
                    "role": "tool",
                    "title": payload.get("name") or "Tool call",
                    "text": payload.get("arguments")
                    if isinstance(payload.get("arguments"), str)
                    else json.dumps(payload, ensure_ascii=True, indent=2),
                }
            )
        elif payload_type in {"function_call_output", "tool_call_output"}:
            event.update(
                {
                    "kind": "tool",
                    "role": "tool",
                    "title": "Tool output",
                    "text": payload.get("output", ""),
                }
            )
        elif payload_type == "token_count":
            usage = (payload.get("info") or {}).get("total_token_usage") or {}
            event.update(
                {
                    "kind": "meta",
                    "role": "meta",
                    "title": "Token count",
                    "text": (
                        f"input {usage.get('input_tokens', 0):,} · "
                        f"cached {usage.get('cached_input_tokens', 0):,} · "
                        f"output {usage.get('output_tokens', 0):,}"
                    ),
                }
            )
        elif payload_type == "agent_message":
            event.update(
                {
                    "kind": "message",
                    "role": "assistant",
                    "title": "Assistant final",
                    "text": payload.get("message", ""),
                }
            )
        else:
            event.update(
                {
                    "kind": "event",
                    "role": "event",
                    "title": payload_type.replace("_", " "),
                    "text": json.dumps(payload, ensure_ascii=True, indent=2),
                }
            )
        event["text"] = truncate(event["text"])
        return event

    event["text"] = truncate(json.dumps(row, ensure_ascii=True, indent=2))
    return event


def normalize_trajectory_step(step: dict, index: int) -> dict:
    source = step.get("source", "event")
    message = step.get("message", "")
    return {
        "index": index,
        "timestamp": step.get("timestamp"),
        "rawType": "trajectory_step",
        "kind": "message" if source in {"user", "assistant", "system"} else "event",
        "role": source,
        "title": str(source).title(),
        "text": truncate(message if isinstance(message, str) else json.dumps(message, ensure_ascii=True, indent=2)),
    }


def trial_dirs(job_dir: Path) -> list[Path]:
    if not job_dir.exists():
        return []
    return sorted(
        [
            child
            for child in job_dir.iterdir()
            if child.is_dir() and (child / "agent").exists()
        ],
        key=lambda path: path.name,
    )


def latest_session_file(trial_dir: Path) -> Path | None:
    files = sorted(
        (trial_dir / "agent" / "sessions").glob("**/*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def live_jobs() -> dict:
    jobs = []
    if not JOBS_DIR.exists():
        return {"jobs": jobs}

    for job_dir in sorted(JOBS_DIR.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True):
        if not job_dir.is_dir():
            continue
        result = read_json(job_dir / "result.json")
        trials = []
        for trial_dir in trial_dirs(job_dir):
            result_path = trial_dir / "result.json"
            trial_result = read_json(result_path)
            session = latest_session_file(trial_dir)
            trajectory = trial_dir / "agent" / "trajectory.json"
            changed = newest_mtime([result_path, trajectory, session] if session else [result_path, trajectory])
            exception = trial_result.get("exception_info") or {}
            trials.append(
                {
                    "name": trial_dir.name,
                    "taskName": trial_result.get("task_name") or trial_dir.name.rsplit("__", 1)[0],
                    "finishedAt": trial_result.get("finished_at"),
                    "exceptionType": exception.get("exception_type"),
                    "reward": _reward_for(trial_dir),
                    "eventsPath": relative(session) if session else None,
                    "trajectoryPath": relative(trajectory) if trajectory.exists() else None,
                    "updatedAt": changed,
                }
            )

        jobs.append(
            {
                "name": job_dir.name,
                "finishedAt": result.get("finished_at"),
                "totalTrials": result.get("n_total_trials") or len(trials),
                "updatedAt": newest_mtime([job_dir / "result.json", *[job_dir / trial["name"] / "result.json" for trial in trials]]),
                "trials": trials,
            }
        )

    return {"jobs": jobs}


def _reward_for(trial_dir: Path) -> str | None:
    reward_txt = trial_dir / "verifier" / "reward.txt"
    if reward_txt.exists():
        return reward_txt.read_text(encoding="utf-8", errors="replace").strip()
    reward_json = trial_dir / "verifier" / "reward.json"
    if reward_json.exists():
        return json.dumps(read_json(reward_json), ensure_ascii=True)
    return None


def live_events(job_name: str, trial_name: str, limit: int) -> dict:
    job_dir = (JOBS_DIR / job_name).resolve()
    trial_dir = (job_dir / trial_name).resolve()
    if JOBS_DIR.resolve() not in trial_dir.parents or not trial_dir.exists():
        raise FileNotFoundError("Unknown trial")

    session = latest_session_file(trial_dir)
    events: list[dict] = []
    source = None
    updated_at = None

    if session:
        source = relative(session)
        updated_at = session.stat().st_mtime
        lines = session.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, len(lines) - limit)
        for offset, line in enumerate(lines[start:], start=start + 1):
            try:
                event = normalize_jsonl_event(json.loads(line), offset)
            except Exception as exc:
                event = {
                    "index": offset,
                    "timestamp": None,
                    "rawType": "parse_error",
                    "kind": "event",
                    "role": "event",
                    "title": "Parse error",
                    "text": str(exc),
                }
            if event:
                events.append(event)
    else:
        trajectory = trial_dir / "agent" / "trajectory.json"
        if trajectory.exists():
            source = relative(trajectory)
            updated_at = trajectory.stat().st_mtime
            steps = read_json(trajectory).get("steps", [])
            start = max(0, len(steps) - limit)
            events = [normalize_trajectory_step(step, index) for index, step in enumerate(steps[start:], start=start + 1)]

    return {
        "job": job_name,
        "trial": trial_name,
        "source": source,
        "updatedAt": updated_at,
        "events": events,
    }


class RepoVizHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("repo-viz: " + fmt % args + "\n")

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/live/jobs":
            self.send_json(live_jobs())
            return

        if parsed.path == "/api/live/events":
            query = parse_qs(parsed.query)
            job = unquote((query.get("job") or [""])[0])
            trial = unquote((query.get("trial") or [""])[0])
            limit = int((query.get("limit") or ["200"])[0])
            try:
                self.send_json(live_events(job, trial, max(1, min(limit, 1000))))
            except FileNotFoundError as exc:
                self.send_json({"error": str(exc)}, status=404)
            return

        if parsed.path == "/api/live/health":
            self.send_json({"status": "ok", "root": str(ROOT)})
            return

        return super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve repo-viz with live Pier trajectory endpoints.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    mimetypes.add_type("text/javascript", ".js")
    os.chdir(WEB_DIR)
    server = ThreadingHTTPServer((args.host, args.port), RepoVizHandler)
    print(f"Repo viz server: http://{args.host}:{args.port}")
    print(f"Watching jobs under {JOBS_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
