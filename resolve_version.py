#!/usr/bin/env -S uv run --no-project --script
# /// script
# requires-python = ">=3.10"
# ///
"""Resolve an upstream ref and assign the next append-only build version."""

import argparse
import datetime as dt
import json
import pathlib
import subprocess


def git(repo: pathlib.Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def existing_records(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for record_path in sorted(path.glob("*.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["_path"] = str(record_path)
        records.append(record)
    return records


def resolve(
    upstream: pathlib.Path,
    versions: pathlib.Path,
    builder_sha: str,
    mode: str,
) -> dict:
    upstream_sha = git(upstream, "rev-parse", "HEAD")
    committed_at = git(upstream, "show", "-s", "--format=%cI", "HEAD")
    stamp = dt.datetime.fromisoformat(committed_at).astimezone(dt.timezone.utc)
    prefix = f"{stamp.year}.{stamp.month}.{stamp.day}-g{upstream_sha[:7]}"

    matching = [
        record
        for record in existing_records(versions)
        if record.get("upstreamCommit") == upstream_sha
    ]
    revisions = [int(record.get("buildRevision", 1)) for record in matching]
    if len(revisions) != len(set(revisions)):
        raise SystemExit(f"duplicate build revision for upstream {upstream_sha}")

    same_builder = next(
        (record for record in matching if record.get("builderCommit") == builder_sha),
        None,
    )
    if mode == "schedule" and matching:
        return {
            "should_build": False,
            "reason": "latest upstream commit already has a published build",
            "upstream_sha": upstream_sha,
            "upstream_date": committed_at,
        }
    if same_builder:
        return {
            "should_build": False,
            "reason": f"same upstream and builder commits already recorded in {same_builder['_path']}",
            "upstream_sha": upstream_sha,
            "upstream_date": committed_at,
        }

    revision = max(revisions, default=0) + 1
    return {
        "should_build": True,
        "reason": "new upstream commit" if not matching else "new build recipe",
        "version": f"{prefix}-r{revision}",
        "build_revision": revision,
        "upstream_sha": upstream_sha,
        "upstream_date": committed_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True, type=pathlib.Path)
    parser.add_argument("--versions", default="versions", type=pathlib.Path)
    parser.add_argument("--builder-sha", required=True)
    parser.add_argument(
        "--mode", choices=("schedule", "push", "manual"), required=True
    )
    parser.add_argument("--github-output", type=pathlib.Path)
    args = parser.parse_args()

    result = resolve(args.upstream, args.versions, args.builder_sha, args.mode)
    print(json.dumps(result, indent=2))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            for key, value in result.items():
                if isinstance(value, bool):
                    value = str(value).lower()
                print(f"{key}={value}", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
