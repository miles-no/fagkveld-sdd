#!/usr/bin/env python3
"""Collates every track for the SDD evening.

Every track is a directory under spor/, and each one measures itself into its
own spor/<name>/metrics/timeline.json. This reads all of them and writes a
table plus an HTML chart that can be projected. Each track declares in its
metrics/track.json whether it used an SDD framework, so runs with and without
one can be told apart.

    python metrics/compare.py

Pass --split with a clock time to additionally break each track's numbers into
before and after that moment.

Standard library only. No install, no CDN - the chart is inline SVG and works
without a network.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

FIELDS = ("input", "cache_read", "cache_write", "output")
COLORS = ["#2563eb", "#dc2626", "#16a34a", "#ca8a04", "#9333ea", "#0891b2"]
TRACKS_DIR = "spor"
NO_FRAMEWORK = "ingen (fri prompting)"


def find_track_dirs(root: Path) -> list[Path]:
    """Every track directory under spor/.

    A directory counts as a track when it holds metrics/track.json, so
    scratch folders and stray files are ignored.

    Args:
        root: Repository root.

    Returns:
        Track directories, sorted by name.
    """
    base = root / TRACKS_DIR
    if not base.is_dir():
        return []
    return sorted(
        d for d in base.iterdir()
        if d.is_dir() and (d / "metrics" / "track.json").is_file()
    )


def load_timeline(track_dir: Path) -> dict | None:
    """Read a track's metrics/timeline.json from disk.

    Args:
        track_dir: The track's directory under spor/.

    Returns:
        The parsed document, or None when it is missing or malformed.
    """
    try:
        return json.loads(
            (track_dir / "metrics" / "timeline.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return None


def parse_time(value: str | None) -> datetime | None:
    """Parse an ISO timestamp, tolerating a trailing 'Z'.

    Args:
        value: Timestamp string, possibly empty.

    Returns:
        The parsed datetime, or None when unparseable.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def total(events: list[dict]) -> dict[str, int]:
    """Sum every token field across a list of events.

    Args:
        events: Events to sum.

    Returns:
        One total per field in FIELDS.
    """
    sums = dict.fromkeys(FIELDS, 0)
    for event in events:
        for field in FIELDS:
            sums[field] += event.get(field, 0)
    return sums


def hit_rate(sums: dict[str, int]) -> float | None:
    """Share of prompt tokens served from cache.

    Args:
        sums: Summed token counts per field.

    Returns:
        The ratio, or None when no prompt tokens were recorded.
    """
    denominator = sums["cache_read"] + sums["cache_write"] + sums["input"]
    return sums["cache_read"] / denominator if denominator else None


def analyse(fallback_name: str, timeline: dict, split: datetime | None) -> dict | None:
    """Summarise one track, optionally split at a clock time.

    Args:
        fallback_name: Used when timeline.json carries no track name.
        timeline: Parsed timeline.json document.
        split: Clock time separating before from after, or None.

    Returns:
        A summary of the track, or None when it holds no timestamped events.
    """
    events = []
    for event in timeline.get("events", []):
        when = parse_time(event.get("time"))
        if when:
            events.append({**event, "_t": when})
    if not events:
        return None
    events.sort(key=lambda e: e["_t"])

    before = [e for e in events if split and e["_t"] < split]
    after = [e for e in events if split and e["_t"] >= split]

    return {
        "name": timeline.get("track") or fallback_name,
        "framework": timeline.get("framework") or None,
        "assistant": timeline.get("assistant") or "claude-code",
        "events": events,
        "count": len(events),
        "before": total(before),
        "after": total(after),
        "total": total(events),
        "start": events[0]["_t"],
        "end": events[-1]["_t"],
    }


def minutes(track: dict) -> int:
    """Wall-clock minutes between a track's first and last message."""
    return round((track["end"] - track["start"]).total_seconds() / 60)


def rate_text(sums: dict[str, int]) -> str:
    """Cache hit rate formatted for a table cell."""
    rate = hit_rate(sums)
    return f"{rate:.0%}" if rate is not None else "n/a"


def table(tracks: list[dict], split: datetime | None) -> str:
    """Render the comparison as a Markdown table.

    Args:
        tracks: Analysed tracks.
        split: Clock time, or None when no split was requested.

    Returns:
        The table as a single string.
    """
    if split:
        rows = [
            "| Spor | Rammeverk | Svar | Tokens før | Tokens etter | Sum | Cache | Tid |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for t in tracks:
            before, after = sum(t["before"].values()), sum(t["after"].values())
            rows.append(
                f"| {t['name']} | {t['framework'] or NO_FRAMEWORK} | {t['count']} | "
                f"{before:,} | {after:,} | {before + after:,} | "
                f"{rate_text(t['total'])} | {minutes(t)} min |"
            )
    else:
        rows = [
            "| Spor | Rammeverk | Svar | Tokens | Cache | Tid |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
        for t in tracks:
            rows.append(
                f"| {t['name']} | {t['framework'] or NO_FRAMEWORK} | {t['count']} | "
                f"{sum(t['total'].values()):,} | {rate_text(t['total'])} | "
                f"{minutes(t)} min |"
            )
    return "\n".join(rows)


def by_framework(tracks: list[dict]) -> str:
    """Aggregate tracks into framework and no-framework groups.

    Args:
        tracks: Analysed tracks.

    Returns:
        A Markdown table, or an empty string when only one group is present.
    """
    with_fw = [t for t in tracks if t["framework"]]
    without = [t for t in tracks if not t["framework"]]
    if not with_fw or not without:
        return ""

    rows = [
        "| Gruppe | Spor | Tokens totalt | Snitt per spor |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, group in (("Med rammeverk", with_fw), ("Uten rammeverk", without)):
        summed = sum(sum(t["total"].values()) for t in group)
        rows.append(f"| {label} | {len(group)} | {summed:,} | {summed // len(group):,} |")
    return "\n".join(rows)


def chart(tracks: list[dict], split: datetime | None, width: int = 960, height: int = 460) -> str:
    """Cumulative token usage over time, one line per track, as inline SVG.

    Tracks that used a framework are drawn solid; free prompting is dashed.

    Args:
        tracks: Analysed tracks.
        split: Clock time to mark with a vertical rule, or None.
        width: Viewbox width in pixels.
        height: Viewbox height in pixels.

    Returns:
        A self-contained SVG element.
    """
    left, right, top, bottom = 90, 30, 30, 50
    plot_w = width - left - right
    plot_h = height - top - bottom

    t0 = min(t["start"] for t in tracks)
    t1 = max(t["end"] for t in tracks)
    span = max((t1 - t0).total_seconds(), 1)
    peak = max(sum(t["total"].values()) for t in tracks) or 1

    def x(when: datetime) -> float:
        return left + (when - t0).total_seconds() / span * plot_w

    def y(value: float) -> float:
        return top + plot_h - value / peak * plot_h

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="system-ui, sans-serif" font-size="13">'
    ]

    for i in range(5):
        value = peak * i / 4
        gy = y(value)
        parts.append(
            f'<line x1="{left}" y1="{gy:.1f}" x2="{width - right}" '
            f'y2="{gy:.1f}" stroke="#e5e7eb"/>'
            f'<text x="{left - 10}" y="{gy + 4:.1f}" text-anchor="end" '
            f'fill="#6b7280">{value / 1000:,.0f}k</text>'
        )

    if split and t0 <= split <= t1:
        sx = x(split)
        parts.append(
            f'<line x1="{sx:.1f}" y1="{top}" x2="{sx:.1f}" '
            f'y2="{top + plot_h}" stroke="#111827" stroke-width="2" '
            f'stroke-dasharray="6 4"/>'
            f'<text x="{sx + 8:.1f}" y="{top + 16}" fill="#111827" '
            f'font-weight="600">split</text>'
        )

    for i, track in enumerate(tracks):
        color = COLORS[i % len(COLORS)]
        dash = '' if track["framework"] else ' stroke-dasharray="8 5"'
        running = 0
        points = []
        for event in track["events"]:
            running += sum(event.get(f, 0) for f in FIELDS)
            points.append(f"{x(event['_t']):.1f},{y(running):.1f}")
        parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.5" '
            f'stroke-linejoin="round"{dash} points="{" ".join(points)}"/>'
        )
        ly = top + 20 + i * 22
        label = f'{track["name"]} ({track["framework"] or "fri"})'
        parts.append(
            f'<rect x="{width - right - 220}" y="{ly - 9}" width="12" '
            f'height="12" fill="{color}" rx="2"/>'
            f'<text x="{width - right - 202}" y="{ly + 2}" fill="#374151">'
            f'{label}</text>'
        )

    parts.append(
        f'<text x="{left}" y="{height - 14}" fill="#6b7280">0 min</text>'
        f'<text x="{width - right}" y="{height - 14}" text-anchor="end" '
        f'fill="#6b7280">{span / 60:.0f} min</text>'
        f'<text x="{width / 2}" y="{height - 14}" text-anchor="middle" '
        f'fill="#6b7280">kumulative tokens over tid — stiplet = uten rammeverk</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def render_html(tracks: list[dict], split: datetime | None) -> str:
    """Build the projectable single-file report.

    Args:
        tracks: Analysed tracks.
        split: Clock time, or None.

    Returns:
        A complete HTML document.
    """
    def cells(row: str) -> str:
        return "".join(f"<td>{c.strip()}</td>" for c in row.strip("|").split("|"))

    lines = table(tracks, split).splitlines()
    head = "".join(f"<th>{c.strip()}</th>" for c in lines[0].strip("|").split("|"))
    body = "".join(f"<tr>{cells(r)}</tr>" for r in lines[2:])

    groups = by_framework(tracks)
    group_html = ""
    if groups:
        glines = groups.splitlines()
        ghead = "".join(f"<th>{c.strip()}</th>" for c in glines[0].strip("|").split("|"))
        gbody = "".join(f"<tr>{cells(r)}</tr>" for r in glines[2:])
        group_html = (
            "<h2>Med og uten rammeverk</h2>"
            f"<table><tr>{ghead}</tr>{gbody}</table>"
        )

    return (
        "<!doctype html><meta charset='utf-8'>"
        "<title>SDD-fagkveld — sammenligning</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:1000px;"
        "margin:40px auto;padding:0 20px;color:#111827}"
        "table{border-collapse:collapse;width:100%;margin-top:24px}"
        "th,td{padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right}"
        "th:first-child,td:first-child,th:nth-child(2),td:nth-child(2)"
        "{text-align:left}h2{margin-top:40px;font-size:18px}</style>"
        "<h1>SDD-fagkveld</h1>" + chart(tracks, split) +
        f"<table><tr>{head}</tr>{body}</table>" + group_html
    )


def main() -> int:
    """Collate every track directory into a Markdown table and an HTML chart.

    Returns:
        0 on success, 1 when no track had usable data, 2 on bad arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split",
        help="valgfritt ISO-tidspunkt, f.eks. 2026-11-12T19:23+01:00. "
             "Uten den rapporteres bare totaler per spor.",
    )
    parser.add_argument("--out", default="metrics", help="hvor resultatet skrives")
    args = parser.parse_args()

    split = None
    if args.split:
        split = parse_time(args.split)
        if not split:
            print("Ugyldig tidspunkt.", file=sys.stderr)
            return 2

    root = Path(__file__).resolve().parent.parent
    track_dirs = find_track_dirs(root)
    if not track_dirs:
        print(
            f"Fant ingen spor under {root / TRACKS_DIR}/. En mappe teller som "
            f"spor når den har metrics/track.json.",
            file=sys.stderr,
        )
        return 1

    tracks = []
    for track_dir in track_dirs:
        timeline = load_timeline(track_dir)
        if not timeline:
            print(
                f"  hopper over {track_dir.name}: ingen metrics/timeline.json "
                f"(sporet har ikke blitt målt ennå)",
                file=sys.stderr,
            )
            continue
        if result := analyse(track_dir.name, timeline, split):
            tracks.append(result)

    if not tracks:
        print("Ingen spor hadde brukbare data.", file=sys.stderr)
        return 1

    unattributed = [t["name"] for t in tracks if t["framework"] is None]
    if len(unattributed) > 1:
        print(
            f"Merk: {len(unattributed)} spor er registrert uten rammeverk "
            f"({', '.join(unattributed)}). Er det riktig, eller mangler noen "
            f"av dem metrics/track.json?",
            file=sys.stderr,
        )

    assistants = sorted({t["assistant"] for t in tracks})
    if len(assistants) > 1:
        print(
            f"ADVARSEL: sporene er målt med ulike kodeassistenter "
            f"({', '.join(assistants)}). Tokentall er IKKE sammenlignbare på "
            f"tvers av leverandører - cache-skriving faktureres ulikt, og pris "
            f"per token varierer. Sammenlign innenfor samme assistent, eller "
            f"bytt målestokk til kroner.",
            file=sys.stderr,
        )

    tracks.sort(key=lambda t: sum(t["total"].values()))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    header = "# Sammenligning av spor\n\n"
    if split:
        header += f"Delt ved: {split.isoformat()}\n\n"
    markdown = header + table(tracks, split) + "\n"
    if groups := by_framework(tracks):
        markdown += "\n## Med og uten rammeverk\n\n" + groups + "\n"
    (out / "comparison.md").write_text(markdown, encoding="utf-8")
    (out / "comparison.html").write_text(render_html(tracks, split), encoding="utf-8")

    print(markdown)
    print(f"Skrevet til {out}/comparison.md og {out}/comparison.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
