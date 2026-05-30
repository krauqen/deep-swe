#!/usr/bin/env python3
"""Build a DeepSWE project inventory from task metadata and GitHub stats."""

from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import re
import time
import tomllib
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
OUT_JSON = ROOT / "analysis" / "dataset-projects.json"
OUT_MD = ROOT / "analysis" / "dataset-projects.md"


def normalize_repo(url: str) -> str:
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not match:
        raise ValueError(f"Could not parse GitHub repository URL: {url}")
    return f"{match.group(1)}/{match.group(2)}"


def read_task_repos() -> dict[str, dict[str, object]]:
    repos: dict[str, dict[str, object]] = {}
    for task_file in sorted(TASKS_DIR.glob("*/task.toml")):
        data = tomllib.loads(task_file.read_text())
        metadata = data["metadata"]
        repo = normalize_repo(metadata["repository_url"])
        entry = repos.setdefault(
            repo,
            {
                "repo": repo,
                "tasks": [],
                "dataset_languages": collections.Counter(),
            },
        )
        entry["tasks"].append(
            {
                "task_id": metadata["task_id"],
                "title": metadata["display_title"],
                "language": metadata["language"],
            }
        )
        entry["dataset_languages"][metadata["language"]] += 1
    return repos


def fetch_github_metadata(repos: list[str]) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    batches = [repos[i : i + 10] for i in range(0, len(repos), 10)]
    for index, batch in enumerate(batches, start=1):
        query = " ".join(f"repo:{repo}" for repo in batch)
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": query, "per_page": "100"}
        )
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "deep-swe-analysis",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        for item in payload.get("items", []):
            results[item["full_name"].lower()] = item
        if index < len(batches):
            time.sleep(7)
    for repo in repos:
        if repo.lower() in results:
            continue
        url = f"https://api.github.com/repos/{repo}"
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "deep-swe-analysis",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            item = json.loads(response.read().decode("utf-8"))
        results[item["full_name"].lower()] = item
    return results


def compact_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def main() -> None:
    repos = read_task_repos()
    github = fetch_github_metadata(sorted(repos))
    generated_at = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

    records = []
    for repo, local in sorted(repos.items(), key=lambda item: item[0].lower()):
        item = github.get(repo.lower(), {})
        languages = dict(sorted(local["dataset_languages"].items()))
        task_titles = [task["title"] for task in local["tasks"]]
        record = {
            "repo": repo,
            "url": item.get("html_url", f"https://github.com/{repo}"),
            "summary": item.get("description") or "No GitHub description available.",
            "github_language": item.get("language"),
            "dataset_languages": languages,
            "task_count": len(local["tasks"]),
            "stars": item.get("stargazers_count"),
            "forks": item.get("forks_count"),
            "open_issues": item.get("open_issues_count"),
            "license": (item.get("license") or {}).get("spdx_id"),
            "pushed_at": item.get("pushed_at"),
            "task_titles": task_titles,
        }
        records.append(record)

    payload = {
        "generated_at": generated_at,
        "task_count": sum(record["task_count"] for record in records),
        "project_count": len(records),
        "source": "DeepSWE task.toml files plus GitHub REST Search API",
        "records": records,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# DeepSWE Dataset Projects",
        "",
        f"Generated: {generated_at}",
        "",
        f"- Tasks: {payload['task_count']}",
        f"- Unique GitHub repositories: {payload['project_count']}",
        "- GitHub stats source: GitHub REST Search API",
        "",
        "| Repo | Dataset tasks | Dataset lang(s) | GitHub lang | Stars | Forks | Open issues | Summary |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        dataset_langs = ", ".join(
            f"{language} ({count})" for language, count in record["dataset_languages"].items()
        )
        summary = str(record["summary"]).replace("|", "\\|")
        lines.append(
            f"| [{record['repo']}]({record['url']}) | {record['task_count']} | "
            f"{dataset_langs} | {record['github_language'] or 'n/a'} | "
            f"{compact_int(record['stars'])} | {compact_int(record['forks'])} | "
            f"{compact_int(record['open_issues'])} | {summary} |"
        )
    lines.extend(
        [
            "",
            "## Task Titles By Project",
            "",
        ]
    )
    for record in records:
        lines.append(f"### {record['repo']}")
        for title in record["task_titles"]:
            lines.append(f"- {title}")
        lines.append("")
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
