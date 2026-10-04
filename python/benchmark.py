#!/usr/bin/env python3
"""Reproducible benchmark runner. Standard library only.

`smoke` is intentionally small and suitable for every commit. The named thesis
suites use the grids from TEMPORAL_PATH_RESEARCH_MASTER_HANDOFF.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
from functools import lru_cache

from generators import (
    all_labels,
    bernoulli_labels,
    derived_seed,
    diamond_chain,
    fixed_labels,
    path_graph,
    random_partial_ktree,
    write_nice_decomposition,
    write_sp,
    write_temporal_graph,
)

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tpcount"
GENERATED = ROOT / "benchmarks" / "generated"
RESULTS = ROOT / "results"

FIELDS = [
    "family", "instance_id", "seed", "solver", "status", "n", "m_static",
    "m_temporal", "r", "treewidth", "s", "z", "count_decimal", "count_bits",
    "wall_ms", "cpu_ms", "peak_rss_mb", "states_total", "states_peak",
    "join_pairs", "answer_sha256", "git_commit", "compiler", "compiler_flags",
    "machine_id",
]


@lru_cache(maxsize=1)
def metadata() -> dict[str, str]:
    def capture(command: list[str]) -> str:
        try:
            return subprocess.check_output(command, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
    return {
        "git_commit": capture(["git", "rev-parse", "HEAD"]),
        "compiler": capture(["g++", "--version"]).splitlines()[0],
        "compiler_flags": "-std=c++20 -O3 -DNDEBUG",
        "machine_id": f"{platform.node()}:{platform.machine()}:{platform.system()}-{platform.release()}",
    }


def run_solver(
    family: str, instance_id: str, seed: int, solver: str, tg: Path,
    *, sp: Path | None = None, td: Path | None = None, timeout: float = 60.0,
    treewidth: int = -1,
) -> dict[str, object]:
    command = [str(BIN), "count", "--solver", solver, str(tg)]
    if sp:
        command += ["--decomp", str(sp)]
    if td:
        command += ["--td", str(td)]
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        if completed.returncode:
            payload: dict[str, object] = {"status": "wrong", "error": completed.stderr.strip()}
        else:
            payload = json.loads(completed.stdout)
            payload["status"] = "ok"
    except subprocess.TimeoutExpired:
        payload = {"status": "timeout"}
    count = str(payload.get("count", ""))
    import hashlib
    row: dict[str, object] = {
        "family": family,
        "instance_id": instance_id,
        "seed": seed,
        "solver": solver,
        "status": payload["status"],
        "n": payload.get("n", ""),
        "m_static": payload.get("m_static", ""),
        "m_temporal": payload.get("m_temporal", ""),
        "r": payload.get("time_ranks", ""),
        "treewidth": treewidth,
        "s": payload.get("s", ""), "z": payload.get("z", ""),
        "count_decimal": count,
        "count_bits": payload.get("count_bits", ""),
        "wall_ms": payload.get("wall_ms", ""),
        "cpu_ms": payload.get("cpu_ms", ""),
        "peak_rss_mb": payload.get("peak_rss_mb", ""),
        "states_total": payload.get("states_created", ""),
        "states_peak": payload.get("states_peak_bag", ""),
        "join_pairs": payload.get("join_pairs_tested", ""),
        "answer_sha256": hashlib.sha256(count.encode()).hexdigest() if count else "",
    }
    row.update(metadata())
    return row


def assert_equal(rows: list[dict[str, object]], context: str) -> None:
    good = [row for row in rows if row["status"] == "ok"]
    if len(good) != len(rows):
        raise RuntimeError(f"solver failure in {context}: {rows}")
    counts = {row["count_decimal"] for row in good}
    if len(counts) != 1:
        raise RuntimeError(f"COUNT MISMATCH in {context}: {rows}")


def forest_cases(smoke: bool) -> list[dict[str, object]]:
    rows = []
    grid = [(10, 10), (40, 20), (100, 50), (250, 100)] if smoke else [
        (length, ranks)
        for length in (10, 20, 50, 100, 200, 500, 1000)
        for ranks in (10, 20, 50, 100, 200, 500, 1000)
    ]
    for length, ranks in grid:
        instance_id = f"dense-L{length}-r{ranks}"
        tg = GENERATED / "forest" / f"{instance_id}.tg"
        n, edges = path_graph(length)
        write_temporal_graph(tg, n, edges, all_labels(edges, ranks), 0, length)
        current = [run_solver("forest_dense", instance_id, 0, solver, tg)
                   for solver in ("forest-paper", "forest-dense", "forest-sparse")]
        assert_equal(current, instance_id)
        rows.extend(current)
    return rows


def ttsp_cases(smoke: bool) -> list[dict[str, object]]:
    rows = []
    ks = (1, 2, 4, 8, 16, 32) if smoke else (1, 2, 4, 8, 16, 32, 64, 128, 256)
    ranks_grid = (2, 4, 8) if smoke else (2, 4, 8, 16, 32)
    for k in ks:
        for ranks in ranks_grid:
            instance_id = f"diamond-k{k}-r{ranks}"
            tg = GENERATED / "ttsp" / f"{instance_id}.tg"
            sp = tg.with_suffix(".sp")
            n, edges, nodes, root = diamond_chain(k)
            write_temporal_graph(tg, n, edges, all_labels(edges, ranks), 0, k)
            write_sp(sp, nodes, root)
            current = [run_solver("ttsp_diamond", instance_id, 0, "ttsp-transfer", tg, sp=sp)]
            if k <= 4:
                current.append(run_solver("ttsp_diamond", instance_id, 0, "brute", tg))
                assert_equal(current, instance_id)
            rows.extend(current)
    return rows


def correctness_cases(smoke: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    target = 12 if smoke else 1000
    for replicate in range(target):
        seed = derived_seed("partial2tree", "correctness", replicate)
        rng = random.Random(seed)
        n = rng.randint(4, 7 if smoke else 9)
        graph = random_partial_ktree(n, 2, 0.0, rng)
        s, z = rng.sample(range(n), 2)
        ranks = rng.randint(2, 4)
        labels = bernoulli_labels(graph.edges, ranks, 0.5, rng)
        name = f"p2-n{n}-rep{replicate}"
        tg = GENERATED / "correctness" / f"{name}.tg"
        td = tg.with_suffix(".ntd")
        write_temporal_graph(tg, n, graph.edges, labels, s, z)
        write_nice_decomposition(td, graph, s, z)
        current = [
            run_solver("correctness_p2", name, seed, "tw-dp", tg, td=td, treewidth=2),
            run_solver("correctness_p2", name, seed, "brute", tg, treewidth=2),
        ]
        assert_equal(current, name)
        rows.extend(current)
    return rows


def write_results(rows: list[dict[str, object]], name: str) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    output = RESULTS / f"{name}.csv"
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("smoke", "correctness", "forest", "ttsp", "all"), default="smoke")
    parser.add_argument("--thesis", action="store_true", help="use the full handoff grids/targets")
    args = parser.parse_args()
    if not BIN.exists():
        raise SystemExit("build/tpcount not found; run scripts/build.sh first")
    smoke = not args.thesis
    rows: list[dict[str, object]] = []
    if args.suite in ("smoke", "forest", "all"):
        rows.extend(forest_cases(smoke))
    if args.suite in ("smoke", "ttsp", "all"):
        rows.extend(ttsp_cases(smoke))
    if args.suite in ("smoke", "correctness", "all"):
        rows.extend(correctness_cases(smoke))
    output = write_results(rows, f"{args.suite}{'-thesis' if args.thesis else ''}")
    print(json.dumps({"rows": len(rows), "output": str(output), "status": "ok"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
