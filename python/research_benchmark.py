#!/usr/bin/env python3
"""Repeated, affinity-pinned benchmark with exact oracles and honest censoring."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import subprocess
import sys
import time

from generators import (MASTER_SEED, all_labels, bernoulli_labels, derived_seed,
                        diamond_chain, edge, path_graph, random_partial_ktree,
                        write_nice_decomposition, write_sp, write_temporal_graph)
from research_audit import elimination_decomposition

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tpcount"
OUT = ROOT / "benchmarks" / "generated" / "research-benchmark"
RESULTS = ROOT / "results"


@dataclass
class Case:
    family: str
    identity: str
    tg: Path
    solvers: tuple[str, ...]
    auxiliary: Path | None = None
    expected: int | None = None
    oracle: str = "cross_solver"
    width: int = -1
    seed: int = 0
    nominal_r: int = 0
    strict: bool = False


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hash() -> str:
    digest = hashlib.sha256()
    paths = sorted((ROOT / "src").glob("*.cpp")) + sorted((ROOT / "src").glob("*.hpp"))
    for path in paths:
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def limit_child():
    # Prevent baseline matrices/state tables from swapping the shared machine.
    cap = 1536 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))


def measure(case: Case, solver: str, batch: int, timeout: float) -> dict:
    actual, _, mode = solver.partition("/")
    command = [str(BIN), "count", "--solver", actual, str(case.tg), "--repeat", str(batch)]
    if actual.startswith("ttsp"):
        command += ["--decomp", str(case.auxiliary)]
    elif actual.startswith("tw-dp"):
        command += ["--td", str(case.auxiliary)]
    if mode:
        command += ["--tw-mode", mode]
    if case.strict:
        command += ["--strict"]
    started = time.perf_counter()
    try:
        run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                             timeout=timeout, preexec_fn=limit_child)
        if run.returncode:
            payload = {"status": "error", "error": run.stderr.strip()}
        else:
            payload = json.loads(run.stdout); payload["status"] = "ok"
    except subprocess.TimeoutExpired:
        payload = {"status": "timeout", "error": f"subprocess exceeded {timeout}s"}
    payload["process_wall_ms"] = 1000 * (time.perf_counter() - started)
    return payload


def sparse_labels(edges, ranks, cardinality, rng):
    # A shared planted rank avoids benchmarking exclusively zero-answer paths.
    pivot = max(1, ranks // 2)
    return {e: sorted({pivot} | set(rng.sample([t for t in range(1, ranks + 1) if t != pivot],
                                             min(cardinality - 1, ranks - 1))))
            for e in sorted(edges)}


def expression_oracle(nodes, root, labels, strict=False):
    """Python sparse vector action on an SP expression, not DAG event traversal."""
    def apply(node_id, incoming):
        kind, args = nodes[node_id]
        if kind == "edge":
            previous = sorted(incoming.items()); cursor = 0; prefix = 0; output = {}
            for t in labels[edge(*args)]:
                while cursor < len(previous) and (previous[cursor][0] < t if strict else previous[cursor][0] <= t):
                    prefix += previous[cursor][1]; cursor += 1
                if prefix:
                    output[t] = prefix
            return output
        if kind == "series":
            return apply(args[1], apply(args[0], incoming))
        left = apply(args[0], incoming); right = apply(args[1], incoming)
        for t, value in right.items():
            left[t] = left.get(t, 0) + value
        return left
    return sum(apply(root, {0: 1}).values())


def cases():
    forest = ("forest-paper", "forest-dense", "forest-sparse")
    for length in (10, 20, 50, 100, 200, 500, 1000):
        for ranks in (10, 20, 50, 100, 200, 500, 1000):
            identity = f"L{length}-r{ranks}"; tg = OUT / "forest_dense" / f"{identity}.tg"
            n, edges = path_graph(length)
            write_temporal_graph(tg, n, edges, all_labels(edges, ranks), 0, length)
            yield Case("forest_dense", identity, tg, forest, expected=math.comb(ranks + length - 1, length),
                       oracle="closed_form", nominal_r=ranks)
    sparse_grid = [(1000, 1000, d) for d in (1, 4, 16, 100, 1000)] + [
        (100, 10000, 4), (1000, 10000, 4), (5000, 1000, 4), (5000, 10000, 4)]
    for length, ranks, d in sparse_grid:
        identity = f"L{length}-r{ranks}-d{d}"; tg = OUT / "forest_sparse" / f"{identity}.tg"
        seed = derived_seed("research_forest", identity, 0); rng = random.Random(seed)
        n, edges = path_graph(length); labels = sparse_labels(edges, ranks, d, rng)
        write_temporal_graph(tg, n, edges, labels, 0, length)
        # Separate Python per-path label recurrence, exact Python integers.
        counts = {0: 1}
        for e in sorted(edges):
            previous = sorted(counts.items()); p = 0; prefix = 0; current = {}
            for t in labels[e]:
                while p < len(previous) and previous[p][0] <= t:
                    prefix += previous[p][1]; p += 1
                current[t] = prefix
            counts = current
        yield Case("forest_sparse", identity, tg, forest, expected=sum(counts.values()),
                   oracle="python_label_dp", seed=seed, nominal_r=ranks)
    # Follow-up control: keep the global compressed rank set fixed while only
    # changing the label density on the s-z path. An off-path leaf supplies all
    # ranks, but contributes no path choice. Earlier raw measurements remain.
    for d in (1, 4, 16, 100, 1000):
        length, ranks = 1000, 1000
        identity = f"L{length}-r{ranks}-d{d}"; tg = OUT / "forest_density_control" / f"{identity}.tg"
        seed = derived_seed("density_control", identity, 0); rng = random.Random(seed)
        n, edges = path_graph(length); labels = sparse_labels(edges, ranks, d, rng)
        counts = {0: 1}
        for e in sorted(edges):
            previous = sorted(counts.items()); p = 0; prefix = 0; current = {}
            for t in labels[e]:
                while p < len(previous) and previous[p][0] <= t:
                    prefix += previous[p][1]; p += 1
                current[t] = prefix
            counts = current
        extra = edge(0, n); edges.add(extra); labels[extra] = list(range(1, ranks + 1))
        write_temporal_graph(tg, n + 1, edges, labels, 0, length)
        yield Case("forest_density_control", identity, tg, forest, expected=sum(counts.values()),
                   oracle="python_label_dp", seed=seed, nominal_r=ranks)
    for k in (1, 2, 4, 8, 16, 32, 64, 128, 256):
        for ranks in (2, 4, 8, 16, 32):
            identity = f"k{k}-r{ranks}"; tg = OUT / "ttsp_dense" / f"{identity}.tg"; sp = tg.with_suffix(".sp")
            n, edges, nodes, root = diamond_chain(k)
            write_temporal_graph(tg, n, edges, all_labels(edges, ranks), 0, k); write_sp(sp, nodes, root)
            yield Case("ttsp_dense", identity, tg, ("ttsp-transfer", "ttsp-events"), sp,
                       (1 << k) * math.comb(ranks + 2*k - 1, 2*k), "closed_form", nominal_r=ranks)
    for k, ranks, strict in ((16, 64, False), (32, 64, False), (32, 128, False),
                             (64, 128, False), (8, 32, True), (16, 64, True), (32, 128, True)):
        identity = f"k{k}-r{ranks}-strict{int(strict)}"; tg = OUT / "ttsp_extra" / f"{identity}.tg"; sp = tg.with_suffix(".sp")
        n, edges, nodes, root = diamond_chain(k)
        write_temporal_graph(tg, n, edges, all_labels(edges, ranks), 0, k); write_sp(sp, nodes, root)
        expected = (1 << k) * (math.comb(ranks, 2*k) if strict else math.comb(ranks + 2*k - 1, 2*k))
        yield Case("ttsp_extra", identity, tg, ("ttsp-transfer", "ttsp-events"), sp, expected,
                   "closed_form", nominal_r=ranks, strict=strict)
    for k, ranks, d in ((64, 1000, 4), (256, 10000, 4), (1024, 10000, 4)):
        identity = f"k{k}-r{ranks}-d{d}"; tg = OUT / "ttsp_sparse" / f"{identity}.tg"; sp = tg.with_suffix(".sp")
        seed = derived_seed("research_ttsp", identity, 0); rng = random.Random(seed)
        n, edges, nodes, root = diamond_chain(k); labels = sparse_labels(edges, ranks, d, rng)
        write_temporal_graph(tg, n, edges, labels, 0, k); write_sp(sp, nodes, root)
        yield Case("ttsp_sparse", identity, tg, ("ttsp-transfer", "ttsp-events"), sp,
                   expression_oracle(nodes, root, labels), "python_expression", seed=seed, nominal_r=ranks)
    for n in (12, 24, 48, 96):
        for ranks in (2, 4, 8):
            for rep in range(2):
                identity = f"n{n}-r{ranks}-rep{rep}"; seed = derived_seed("research_partial2", identity, 0)
                rng = random.Random(seed); graph = random_partial_ktree(n, 2, 0.3, rng)
                s, z = rng.sample(range(n), 2); labels = bernoulli_labels(graph.edges, ranks, 0.5, rng)
                tg = OUT / "partial2" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
                write_temporal_graph(tg, n, graph.edges, labels, s, z); write_nice_decomposition(td, graph, s, z)
                yield Case("partial2", identity, tg, ("tw-dp-baseline", "tw-dp"), td,
                           width=2, seed=seed, nominal_r=ranks)
    for width in (1, 2, 3, 4):
        for ranks in (2, 4, 8):
            identity = f"w{width}-n12-r{ranks}"; seed = derived_seed("research_width", identity, 0)
            rng = random.Random(seed); graph = random_partial_ktree(12, width, 0.0, rng)
            s, z = rng.sample(range(12), 2); labels = bernoulli_labels(graph.edges, ranks, 0.5, rng)
            tg = OUT / "width" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
            write_temporal_graph(tg, 12, graph.edges, labels, s, z); write_nice_decomposition(td, graph, s, z)
            yield Case("width", identity, tg, ("brute", "tw-dp-baseline", "tw-dp"), td,
                       oracle="cpp_static_enum", width=width, seed=seed, nominal_r=ranks)
    for n in (12, 24, 48, 96):
        identity = f"n{n}-r4-rep0"
        seed = derived_seed("research_partial2", identity, 0)
        tg = OUT / "partial2" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
        yield Case("enumeration_crossover", identity, tg, ("brute", "tw-dp"), td,
                   oracle="cpp_static_enum_if_completed", width=2, seed=seed, nominal_r=4)
    for rep in range(3):
        identity = f"w2-n24-r8-rep{rep}"; seed = derived_seed("research_ablation", identity, 0)
        rng = random.Random(seed); graph = random_partial_ktree(24, 2, 0.0, rng)
        s, z = rng.sample(range(24), 2); labels = bernoulli_labels(graph.edges, 8, 0.5, rng)
        tg = OUT / "ablation" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
        write_temporal_graph(tg, 24, graph.edges, labels, s, z); write_nice_decomposition(td, graph, s, z)
        yield Case("ablation", identity, tg, ("tw-dp-baseline", "tw-dp", "tw-dp/no-index",
                   "tw-dp/no-prune", "tw-dp/no-release", "tw-dp/no-compact"), td,
                   width=2, seed=seed, nominal_r=8)
    for k in (4, 16, 64, 256):
        for ranks in (4, 8):
            identity = f"k{k}-r{ranks}-arbitrary"; tg = OUT / "cactus" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
            n, edges, _, _ = diamond_chain(k); s, z = k + 1, 3*k - 1
            write_temporal_graph(tg, n, edges, all_labels(edges, ranks), s, z)
            graph = elimination_decomposition(n, edges); write_nice_decomposition(td, graph, s, z)
            expected = (1 << (k - 2)) * sum(c * math.comb(ranks + length - 1, length)
                                            for c, length in ((1, 2*k - 2), (2, 2*k), (1, 2*k + 2)))
            yield Case("cactus", identity, tg, ("cactus", "tw-dp"), td, expected,
                       "closed_form", width=2, nominal_r=ranks)


FIELDS = ["family", "instance_id", "solver", "replicate", "status", "strict", "seed",
          "n", "m_static", "m_temporal", "r", "nominal_r", "treewidth", "s", "z",
          "count_decimal", "count_bits", "answer_sha256", "oracle", "wall_ms", "cpu_ms",
          "parse_ms", "process_wall_ms", "batch_repeats", "peak_rss_mb", "states_created",
          "states_peak_bag", "states_peak_live", "join_pairs_possible", "join_pairs_tested",
          "join_pairs_compatible", "temporal_events", "dag_additions", "ttsp_scalar_products",
          "input_sha256", "auxiliary_sha256", "source_sha256", "error"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--target-ms", type=float, default=10.0)
    parser.add_argument("--families", default="all")
    parser.add_argument("--output-name", default="research_benchmark")
    args = parser.parse_args()
    if args.repeats < 3:
        raise SystemExit("at least 3 measurement repetitions are required")
    sys.setrecursionlimit(20000)
    affinity = None
    if hasattr(os, "sched_getaffinity"):
        affinity = min(os.sched_getaffinity(0)); os.sched_setaffinity(0, {affinity})
    selected = set(args.families.split(",")); digest = source_hash()
    metadata = {"master_seed": MASTER_SEED, "repetitions": args.repeats, "warmups": 1,
                "timeout_seconds": args.timeout, "target_batch_ms": args.target_ms,
                "max_batch_iterations": 256, "cpu_affinity": affinity, "cpu_frequency_fixed": False,
                "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
                "compiler_flags": "-std=c++20 -O3 -DNDEBUG -Wall -Wextra -Wpedantic",
                "platform": platform.platform(), "machine": platform.node(), "source_sha256": digest,
                "binary_sha256": hash_file(BIN), "address_space_limit_mib": 1536,
                "controller_sha256": hash_file(Path(__file__)),
                "generator_sha256": hash_file(ROOT / "python" / "generators.py"),
                "baseline": "own reimplementation of paper recurrence after rank compression",
                "timing_region": "solver plus auxiliary-file reading/validation; excludes TG parsing",
                "rss_measurement": "Linux /proc/self/status VmHWM of post-exec C++ address space",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    started = time.perf_counter(); total_rows = 0; statuses = {}; case_count = 0
    RESULTS.mkdir(exist_ok=True)
    if not args.output_name.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("output-name must contain only letters, numbers, '-' and '_'")
    with (RESULTS / f"{args.output_name}.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore"); writer.writeheader()
        for case in cases():
            if "all" not in selected and case.family not in selected:
                continue
            case_count += 1
            info = json.loads(subprocess.check_output([str(BIN), "info", str(case.tg)], text=True))
            common = {"family": case.family, "instance_id": case.identity, "strict": int(case.strict),
                      "seed": case.seed, "nominal_r": case.nominal_r, "treewidth": case.width,
                      "oracle": case.oracle, "input_sha256": hash_file(case.tg),
                      "auxiliary_sha256": hash_file(case.auxiliary) if case.auxiliary else "",
                      "source_sha256": digest, "r": info["time_ranks"],
                      **{k: info[k] for k in ("n", "m_static", "m_temporal", "s", "z")}}
            expected = str(case.expected) if case.expected is not None else None
            calibrated = {}

            def save(solver, rep, payload):
                nonlocal total_rows
                if payload["status"] == "ok":
                    if expected is not None and str(payload["count"]) != expected:
                        failure = {"case": case.identity, "solver": solver, "expected": expected, "actual": payload}
                        (RESULTS / "benchmark_failure.json").write_text(json.dumps(failure, indent=2))
                        raise RuntimeError(f"COUNT MISMATCH {case.identity}: {solver}")
                row = {**common, **payload, "solver": solver, "replicate": rep,
                       "count_decimal": payload.get("count", ""),
                       "answer_sha256": hashlib.sha256(str(payload["count"]).encode()).hexdigest() if "count" in payload else ""}
                writer.writerow(row); stream.flush(); total_rows += 1
                statuses[payload["status"]] = statuses.get(payload["status"], 0) + 1

            for solver in case.solvers:
                if solver == "ttsp-transfer" and info["time_ranks"] > 128:
                    save(solver, 0, {"status": "skipped_budget", "error": "matrix baseline rank cap 128"}); continue
                pilot = measure(case, solver, 1, args.timeout)
                if pilot["status"] != "ok":
                    save(solver, 0, pilot); continue
                if expected is None:
                    expected = str(pilot["count"])
                if str(pilot["count"]) != expected:
                    save(solver, -1, pilot)  # raises and persists mismatch
                batch = min(256, max(1, math.ceil(args.target_ms / max(0.01, float(pilot["wall_ms"])))))
                calibrated[solver] = batch
            rng = random.Random(derived_seed("measurement_order", case.identity, 0))
            for rep in range(args.repeats):
                order = list(calibrated); rng.shuffle(order)
                for solver in order:
                    save(solver, rep, measure(case, solver, calibrated[solver], args.timeout))
            print(f"benchmark {case_count}: {case.family}/{case.identity}", flush=True)
    metadata.update({"cases": case_count, "rows": total_rows, "statuses": statuses,
                     "wall_seconds": time.perf_counter() - started})
    (RESULTS / f"{args.output_name}_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
