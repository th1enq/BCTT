#!/usr/bin/env python3
"""Aggregate benchmark CSV files into a compact Markdown table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import statistics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("results/aggregate.md"))
    args = parser.parse_args()
    groups: dict[tuple[str, str], list[float]] = {}
    statuses: dict[tuple[str, str], dict[str, int]] = {}
    for path in args.inputs:
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                key = (row["family"], row["solver"])
                statuses.setdefault(key, {})[row["status"]] = statuses.setdefault(key, {}).get(row["status"], 0) + 1
                if row["status"] == "ok" and row["wall_ms"]:
                    groups.setdefault(key, []).append(float(row["wall_ms"]))
    lines = ["# Aggregate benchmark results", "", "| Family | Solver | OK/total | Median ms | IQR ms | Max ms |", "|---|---|---:|---:|---:|---:|"]
    for key in sorted(statuses):
        values = sorted(groups.get(key, []))
        total = sum(statuses[key].values())
        if values:
            quartiles = statistics.quantiles(values, n=4, method="inclusive") if len(values) > 1 else [values[0]] * 3
            lines.append(f"| {key[0]} | {key[1]} | {len(values)}/{total} | {statistics.median(values):.6g} | {quartiles[2]-quartiles[0]:.6g} | {max(values):.6g} |")
        else:
            lines.append(f"| {key[0]} | {key[1]} | 0/{total} | – | – | – |")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
