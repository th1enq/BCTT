#!/usr/bin/env python3
"""Large seeded correctness audit against independent static-path enumeration."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import subprocess
import sys

from generators import (
    bernoulli_labels, derived_seed, fixed_labels, random_partial_ktree,
    random_ttsp, write_nice_decomposition, write_sp, write_temporal_graph,
)

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tpcount"
OUT = ROOT / "benchmarks" / "generated" / "audit"


def solve(solver: str, tg: Path, auxiliary: Path | None = None) -> str:
    command = [str(BIN), "count", "--solver", solver, str(tg)]
    if solver == "ttsp-transfer": command += ["--decomp", str(auxiliary)]
    if solver == "tw-dp": command += ["--td", str(auxiliary)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{solver} failed for {tg}: {result.stderr}")
    return str(json.loads(result.stdout)["count"])


def check(values: dict[str, str], identity: str) -> None:
    if len(set(values.values())) != 1:
        failure = ROOT / "results" / "audit_failure.json"
        failure.parent.mkdir(exist_ok=True)
        failure.write_text(json.dumps({"instance": identity, "counts": values}, indent=2), encoding="utf-8")
        raise RuntimeError(f"mismatch at {identity}; saved {failure}")


def forest_audit(count: int) -> None:
    target = OUT / "forest"
    for rep in range(count):
        seed = derived_seed("audit_forest", "random_tree", rep)
        rng = random.Random(seed)
        n = rng.randint(2, 10)
        edges = {(vertex, rng.randrange(vertex)) for vertex in range(1, n)}
        s, z = rng.sample(range(n), 2)
        ranks = rng.randint(1, 5)
        labels = bernoulli_labels(edges, ranks, rng.uniform(0.2, 0.9), rng)
        tg = target / f"forest-{rep}.tg"
        write_temporal_graph(tg, n, edges, labels, s, z)
        values = {solver: solve(solver, tg) for solver in
                  ("forest-paper", "forest-dense", "forest-sparse", "brute")}
        check(values, f"forest:{rep}:{seed}")


def ttsp_audit(count: int) -> None:
    target = OUT / "ttsp"
    for rep in range(count):
        seed = derived_seed("audit_ttsp", "recursive", rep)
        rng = random.Random(seed)
        n, edges, nodes, root = random_ttsp(rng.randint(1, 9), rng.uniform(0.2, 0.8), rng)
        ranks = rng.randint(1, 5)
        labels = fixed_labels(edges, ranks, rng.randint(1, ranks), rng)
        tg = target / f"ttsp-{rep}.tg"; sp = tg.with_suffix(".sp")
        write_temporal_graph(tg, n, edges, labels, 0, 1)
        write_sp(sp, nodes, root)
        values = {"ttsp-transfer": solve("ttsp-transfer", tg, sp), "brute": solve("brute", tg)}
        check(values, f"ttsp:{rep}:{seed}")


def partial_audit(count: int) -> None:
    target = OUT / "partial2"
    for rep in range(count):
        seed = derived_seed("audit_partial2", "ktree", rep)
        rng = random.Random(seed)
        n = rng.randint(4, 9)
        graph = random_partial_ktree(n, 2, 0.0, rng)
        s, z = rng.sample(range(n), 2)
        ranks = rng.randint(1, 4)
        labels = bernoulli_labels(graph.edges, ranks, 0.5, rng)
        tg = target / f"partial2-{rep}.tg"; td = tg.with_suffix(".ntd")
        write_temporal_graph(tg, n, graph.edges, labels, s, z)
        write_nice_decomposition(td, graph, s, z)
        values = {"tw-dp": solve("tw-dp", tg, td), "brute": solve("brute", tg)}
        check(values, f"partial2:{rep}:{seed}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forest", type=int, default=3000)
    parser.add_argument("--ttsp", type=int, default=2500)
    parser.add_argument("--partial2", type=int, default=1000)
    args = parser.parse_args()
    if not BIN.exists(): raise SystemExit("run scripts/build.sh first")
    forest_audit(args.forest)
    ttsp_audit(args.ttsp)
    partial_audit(args.partial2)
    summary = {
        "master_seed": 20260928,
        "forest_comparisons": args.forest,
        "ttsp_comparisons": args.ttsp,
        "partial2_comparisons": args.partial2,
        "total": args.forest + args.ttsp + args.partial2,
        "mismatches": 0,
    }
    result = ROOT / "results" / "audit_summary.json"
    result.parent.mkdir(exist_ok=True)
    result.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
