#!/usr/bin/env python3
"""Token measurement for the SDD evening.

Reconstructs the full token-usage time series from Claude Code session
transcripts. No checkpoints, nothing to remember along the way - every
message is already timestamped.

    python metrics/tokens.py            # write timeline.json + summary.md
    python metrics/tokens.py --quiet    # same, without output (for hooks)

Standard library only. No install.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BUCKETS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)
SHORT_NAMES = {
    "input_tokens": "input",
    "output_tokens": "output",
    "cache_creation_input_tokens": "cache_write",
    "cache_read_input_tokens": "cache_read",
}
FIELDS = tuple(SHORT_NAMES.values())

TRACK_FILE = "track.json"


DEFAULT_ASSISTANT = "claude-code"


def read_track(out: Path, repo_root: Path) -> tuple[dict, bool]:
    """Read the track's identity from metrics/track.json.

    The file is committed per track branch and is what separates a run that
    used an SDD framework from one that did not. Without it the track is
    still measured, but cannot be attributed.

    Args:
        out: Directory holding the metrics files.
        repo_root: Used for the fallback name.

    Returns:
        The track's name, framework and assistant, and whether track.json
        was actually found.
    """
    fallback = {
        "name": repo_root.name,
        "framework": None,
        "assistant": DEFAULT_ASSISTANT,
    }
    try:
        doc = json.loads((out / TRACK_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback, False
    framework = doc.get("framework")
    return {
        "name": str(doc.get("name") or repo_root.name),
        "framework": str(framework) if framework else None,
        "assistant": str(doc.get("assistant") or DEFAULT_ASSISTANT),
    }, True


def read_events(projects_dir: Path, repo_root: Path) -> list[dict]:
    """Every assistant message that belonged to this repo, sorted by time.

    Filters on 'cwd' rather than guessing how Claude Code encoded the repo
    path into the directory name. Deduplicates on uuid, because the same
    message can be written several times while streaming.

    Args:
        projects_dir: Root of the Claude Code transcript store.
        repo_root: Only messages with a cwd inside this path are counted.

    Returns:
        Events sorted by timestamp, one per assistant message with usage data.
    """
    repo_root = repo_root.resolve()
    seen: set[str] = set()
    events: list[dict] = []

    for path in sorted(projects_dir.rglob("*.jsonl")):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("type") != "assistant":
                continue

            cwd = rec.get("cwd")
            if not cwd:
                continue
            try:
                if not Path(cwd).resolve().is_relative_to(repo_root):
                    continue
            except (OSError, ValueError):
                continue

            uuid = rec.get("uuid")
            if uuid and uuid in seen:
                continue
            if uuid:
                seen.add(uuid)

            msg = rec.get("message") or {}
            usage = msg.get("usage") or {}
            if not usage:
                continue

            events.append({
                "time": rec.get("timestamp"),
                "session": rec.get("sessionId"),
                "model": msg.get("model", "unknown"),
                **{SHORT_NAMES[b]: int(usage.get(b) or 0) for b in BUCKETS},
            })

    events.sort(key=lambda e: e["time"] or "")
    return events


def claude_code_dir() -> Path:
    """Where Claude Code keeps its session transcripts."""
    return Path.home() / ".claude" / "projects"


# Each assistant contributes one entry: a function giving its default
# transcript directory, and a reader.
#
# A reader takes (transcripts_dir, repo_root) and returns a list of events,
# sorted by time. Each event must carry:
#
#     time         ISO timestamp string
#     session      session id, or None
#     model        model name, or "unknown"
#     input        prompt tokens NOT served from cache
#     output       generated tokens
#     cache_write  tokens written to cache (0 when the vendor has no such cost)
#     cache_read   prompt tokens served from cache
#
# Only messages whose working directory lies under repo_root count, so a
# track is never credited with another track's work.
#
# Adding an assistant means writing one reader and one line here. Note that
# token counts are NOT comparable across vendors - see the warning in
# compare.py.
READERS = {
    "claude-code": (claude_code_dir, read_events),
}


def build_timeline(events: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Attach a running sum, so the series can be cut at a given clock time.

    Args:
        events: Events in chronological order.

    Returns:
        The series with a 'cumulative' field per event, and the grand total.
    """
    running = dict.fromkeys(FIELDS, 0)
    series = []
    for event in events:
        for field in FIELDS:
            running[field] += event[field]
        series.append({**event, "cumulative": dict(running)})
    return series, running


def cache_hit_rate(total: dict[str, int]) -> float | None:
    """Share of prompt tokens served from cache.

    Args:
        total: Summed token counts per field.

    Returns:
        The ratio rounded to four decimals, or None when no prompt tokens.
    """
    denominator = total["cache_read"] + total["cache_write"] + total["input"]
    return round(total["cache_read"] / denominator, 4) if denominator else None


def write_summary(
    path: Path,
    track: str,
    framework: str | None,
    events: list[dict],
    total: dict[str, int],
) -> None:
    """Write the human-readable summary for a single track.

    Args:
        path: File to write.
        track: Name of the track being measured.
        framework: SDD framework used, or None when the track prompted freely.
        events: Events in chronological order.
        total: Summed token counts per field.
    """
    rate = cache_hit_rate(total)
    first = events[0]["time"] if events else None
    last = events[-1]["time"] if events else None
    models = sorted({e["model"] for e in events})

    lines = [
        f"# Token usage - {track}",
        "",
        f"Framework: {framework or 'none (free prompting)'}",
        # timezone.utc, ikke datetime.UTC: Stop-hooken kjorer pa systemets
        # python3, som pa macOS er 3.9. datetime.UTC krever 3.11.
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",  # noqa: UP017
        f"First message: {first}",
        f"Last message: {last}",
        f"Replies from the agent: {len(events)}",
        f"Models: {', '.join(models) or 'none'}",
        "",
        "| Bucket | Tokens |",
        "| --- | ---: |",
        f"| Uncached input | {total['input']:,} |",
        f"| Cache reads | {total['cache_read']:,} |",
        f"| Cache writes | {total['cache_write']:,} |",
        f"| Output | {total['output']:,} |",
        f"| **Sum** | **{sum(total.values()):,}** |",
        "",
        f"Cache hit rate: {f'{rate:.1%}' if rate is not None else 'n/a'}",
        "",
        "The full time series with cumulative counts is in `timeline.json`.",
        "It can be cut at any clock time.",
        "",
        "> Note: `output` from the transcript may be under-reported.",
        "> `/cost` in Claude Code is authoritative for output and cost.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Read transcripts and write timeline.json plus summary.md.

    Returns:
        0 on success, 1 when no usable transcript data was found.
    """
    quiet = "--quiet" in sys.argv

    repo_root = Path(os.environ.get("SDD_REPO_ROOT", Path.cwd()))
    out = Path(os.environ.get("SDD_METRICS_DIR", repo_root / "metrics"))
    out.mkdir(parents=True, exist_ok=True)

    track, found = read_track(out, repo_root)
    assistant = track["assistant"]

    if not found:
        print(
            f"No {out / TRACK_FILE} - this directory is not a track, so nothing "
            f"was written. Create the file (see track.example.json) and run "
            f"again; the series is rebuilt from the transcripts every time, so "
            f"no history is lost by waiting.",
            file=sys.stderr,
        )
        return 0

    if assistant not in READERS:
        print(
            f"Unknown assistant {assistant!r} in {out / TRACK_FILE}. "
            f"Supported: {', '.join(sorted(READERS))}. "
            f"Adding one means writing a reader and registering it in READERS.",
            file=sys.stderr,
        )
        return 1

    default_dir, reader = READERS[assistant]
    transcripts = Path(os.environ.get("SDD_TRANSCRIPTS_DIR", default_dir()))

    if not transcripts.is_dir():
        if not quiet:
            print(f"Could not find {transcripts}.", file=sys.stderr)
            print(f"Is {assistant} running locally?", file=sys.stderr)
        return 1

    events = reader(transcripts, repo_root)
    if not events:
        if not quiet:
            print(f"No messages with a cwd under {repo_root}.", file=sys.stderr)
        return 1

    series, total = build_timeline(events)

    (out / "timeline.json").write_text(
        json.dumps(
            {
                "track": track["name"],
                "framework": track["framework"],
                "assistant": assistant,
                "repo_root": str(repo_root),
                "events": series,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    write_summary(out / "summary.md", track["name"], track["framework"], events, total)

    if not quiet:
        rate = cache_hit_rate(total)
        print(f"{len(events)} replies from the agent written to {out}")
        print(f"  {'track':<12}: {track['name']}")
        print(f"  {'framework':<12}: {track['framework'] or 'none (free prompting)'}")
        print(f"  {'assistant':<12}: {assistant}")
        for field in FIELDS:
            print(f"  {field:<12}: {total[field]:>12,}")
        print(f"  {'cache hits':<12}: "
              f"{f'{rate:.1%}' if rate is not None else 'n/a':>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
