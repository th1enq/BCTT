#!/usr/bin/env python3
"""Exponential-route stress cases for arbitrary-terminal series-parallel DP."""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import time

from generators import all_labels, derived_seed, edge, write_nice_decomposition, write_temporal_graph
from research_audit import elimination_decomposition, oracle
from research_benchmark import BIN, ROOT, RESULTS, OUT, Case, FIELDS, hash_file, measure, source_hash


def ladder(columns):
    edges = {edge(2*i, 2*i+1) for i in range(columns)}
    for i in range(columns - 1):
        edges.add(edge(2*i, 2*i+2)); edges.add(edge(2*i+1, 2*i+3))
    return 2*columns, edges


def closed_form(columns, ranks, strict=False):
    return sum(math.comb(columns, q) *
               (math.comb(ranks, columns-1+q) if strict and ranks >= columns-1+q
                else 0 if strict else math.comb(ranks+columns+q-2, columns-1+q))
               for q in range(1, columns+1, 2))


def main():
    cpu = min(os.sched_getaffinity(0)); os.sched_setaffinity(0, {cpu})
    checks = 0
    for columns in range(2, 7):
        n, edges = ladder(columns)
        for ranks in (1, 2, 3):
            labels = all_labels(edges, ranks)
            for strict in (False, True):
                assert closed_form(columns, ranks, strict) == oracle(n, labels, 0, n-1, strict)
                checks += 1
    started = time.perf_counter(); statuses = {}; row_count = 0; case_count = 0
    metadata = json.loads((RESULTS / "research_benchmark_metadata.json").read_text())
    if hash_file(BIN) != metadata["binary_sha256"] or source_hash() != metadata["source_sha256"]:
        raise RuntimeError("C++ version changed since the main benchmark")
    with (RESULTS / "research_ladder.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore"); writer.writeheader()
        for columns in (4, 8, 12, 16, 24, 32, 64):
            for ranks in (2, 4, 8):
                identity = f"c{columns}-r{ranks}"; n, edges = ladder(columns)
                tg = OUT / "ladder" / f"{identity}.tg"; td = tg.with_suffix(".ntd")
                labels = all_labels(edges, ranks); write_temporal_graph(tg, n, edges, labels, 0, n-1)
                graph = elimination_decomposition(n, edges); write_nice_decomposition(td, graph, 0, n-1)
                expected = str(closed_form(columns, ranks)); solvers = ("brute", "tw-dp-baseline", "tw-dp")
                case = Case("ladder", identity, tg, solvers, td, int(expected), "closed_form_ladder", 2, nominal_r=ranks)
                info = json.loads(subprocess.check_output([str(BIN), "info", str(tg)], text=True))
                common = {"family": "ladder", "instance_id": identity, "strict": 0, "seed": 0,
                          "nominal_r": ranks, "treewidth": 2, "oracle": "closed_form_ladder",
                          "input_sha256": hash_file(tg), "auxiliary_sha256": hash_file(td),
                          "source_sha256": metadata["source_sha256"], "r": ranks,
                          **{k: info[k] for k in ("n", "m_static", "m_temporal", "s", "z")}}

                def save(solver, rep, payload):
                    nonlocal row_count
                    if payload["status"] == "ok" and str(payload["count"]) != expected:
                        raise RuntimeError(f"ladder count mismatch {identity}/{solver}: {payload}")
                    writer.writerow({**common, **payload, "solver": solver, "replicate": rep,
                                     "count_decimal": payload.get("count", ""),
                                     "answer_sha256": hashlib.sha256(str(payload["count"]).encode()).hexdigest() if "count" in payload else ""})
                    stream.flush(); row_count += 1; statuses[payload["status"]] = statuses.get(payload["status"], 0) + 1

                calibrated = {}
                for solver in solvers:
                    pilot = measure(case, solver, 1, 3.0)
                    if pilot["status"] != "ok":
                        save(solver, 0, pilot); continue
                    if str(pilot["count"]) != expected:
                        raise RuntimeError("ladder warm-up mismatch")
                    calibrated[solver] = min(256, max(1, math.ceil(10 / max(0.01, float(pilot["wall_ms"])))))
                rng = random.Random(derived_seed("measurement_order", identity, 0))
                for rep in range(7):
                    order = list(calibrated); rng.shuffle(order)
                    for solver in order:
                        save(solver, rep, measure(case, solver, calibrated[solver], 3.0))
                case_count += 1; print(f"ladder {case_count}: {identity}", flush=True)
    metadata.update({"cases": case_count, "rows": row_count, "statuses": statuses,
                     "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                     "controller_sha256": hash_file(Path(__file__)), "base_controller_sha256": hash_file(ROOT / "python" / "research_benchmark.py"),
                     "wall_seconds": time.perf_counter() - started, "formula_checks_python_cartesian": checks})
    (RESULTS / "research_ladder_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
