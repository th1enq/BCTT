#!/usr/bin/env python3
"""Exhaustive, Graph Atlas, seeded, and metamorphic cross-language audits."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

from generators import (PartialKTree, all_labels, bernoulli_labels, derived_seed,
                        edge, fixed_labels, random_partial_ktree, random_ttsp,
                        write_nice_decomposition, write_sp, write_temporal_graph)

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "tpcount"
OUT = ROOT / "benchmarks" / "generated" / "research-audit"
ATLAS = ROOT / "benchmarks" / "data" / "atlas.dat.gz"
ATLAS_SHA = "73fc416df0164923607751cb759f4ae81deb5f6550bf25be59c86de3b747e41d"


def oracle(n: int, labels: dict[tuple[int, int], list[int]], s: int, z: int, strict: bool) -> int:
    """Enumerate actual time-edge sequences using Python integers; no label DP."""
    adjacency = [[] for _ in range(n)]
    for (u, v), times in labels.items():
        adjacency[u].append((v, times)); adjacency[v].append((u, times))

    def visit(u: int, last: int | None, used: int) -> int:
        if u == z:
            return 1
        total = 0
        for v, times in adjacency[u]:
            if used & (1 << v):
                continue
            for t in times:
                if last is None or (last < t if strict else last <= t):
                    total += visit(v, t, used | (1 << v))
        return total
    return visit(s, None, 1 << s)


def elimination_decomposition(n: int, edges: set[tuple[int, int]], bound: int = 2) -> PartialKTree | None:
    """Width <=2 recognition by degree-2 elimination with fill (minor safe)."""
    adjacency = [set() for _ in range(n)]
    for u, v in edges:
        adjacency[u].add(v); adjacency[v].add(u)
    active = set(range(n)); bags = []; vertices = []; width = 0
    while active:
        v = min(active, key=lambda u: (len(adjacency[u] & active), u))
        neighbors = adjacency[v] & active
        if len(neighbors) > bound:
            return None
        width = max(width, len(neighbors)); bags.append({v} | neighbors); vertices.append(v)
        for u in neighbors:
            adjacency[u].update(neighbors - {u}); adjacency[u].discard(v)
        active.remove(v)
    indices = {v: i for i, v in enumerate(vertices)}
    tree_edges = []; roots = []
    for i, bag in enumerate(bags):
        other = bag - {vertices[i]}
        if other:
            tree_edges.append((i, min(indices[v] for v in other)))
        else:
            roots.append(i)
    tree_edges.extend(zip(roots, roots[1:]))
    return PartialKTree(n, edges, bags, tree_edges, width)


def atlas_graphs():
    if hashlib.sha256(ATLAS.read_bytes()).hexdigest() != ATLAS_SHA:
        raise RuntimeError("Graph Atlas checksum mismatch")
    with gzip.open(ATLAS, "rt") as stream:
        current = None; n = 0; edges = set()
        for line in stream:
            parts = line.split()
            if parts[0] == "GRAPH":
                if current is not None:
                    yield current, n, edges
                current = int(parts[1]); edges = set()
            elif parts[0] == "NODES":
                n = int(parts[1])
            else:
                edges.add(edge(int(parts[0]), int(parts[1])))
        if current is not None:
            yield current, n, edges


class Audit:
    def __init__(self, writer):
        self.writer = writer; self.jobs = []; self.expected = []; self.identities = []
        self.cases = {}; self.comparisons = {}; self.digest = hashlib.sha256()

    def add(self, family, identity, tg, auxiliary, solvers, expected, strict):
        key = f"{identity}:strict={int(strict)}"
        self.cases[family] = self.cases.get(family, 0) + 1
        for solver in solvers:
            aux = str(auxiliary) if auxiliary and solver.startswith(("ttsp", "tw-dp")) else "-"
            self.jobs.append(f"{solver} {tg} {aux} {int(strict)}")
            self.expected.append(str(expected)); self.identities.append((family, key, solver, tg))
        if len(self.jobs) >= 512:
            self.flush()

    def flush(self):
        if not self.jobs:
            return
        run = subprocess.run([str(BIN), "batch"], input="\n".join(self.jobs) + "\n",
                             text=True, capture_output=True, cwd=ROOT, timeout=300)
        if run.returncode:
            raise RuntimeError(f"batch solver failed: {run.stderr}")
        lines = run.stdout.splitlines()
        if len(lines) != len(self.jobs):
            raise RuntimeError("batch output length mismatch")
        for line, expected, (family, identity, solver, tg) in zip(lines, self.expected, self.identities):
            actual = str(json.loads(line)["count"])
            if actual != expected:
                failure = {"family": family, "case": identity, "solver": solver,
                           "tg": str(tg), "expected": expected, "actual": actual}
                (ROOT / "results" / "research_audit_failure.json").write_text(json.dumps(failure, indent=2))
                raise RuntimeError(f"COUNT MISMATCH: {failure}")
            self.comparisons[family] = self.comparisons.get(family, 0) + 1
            count_hash = hashlib.sha256(actual.encode()).hexdigest()
            self.writer.writerow([family, identity, solver, expected, count_hash])
            self.digest.update(f"{family}:{identity}:{solver}:{actual}\n".encode())
        self.jobs.clear(); self.expected.clear(); self.identities.clear()


def random_campaign(audit: Audit, count: int):
    for family in ("forest", "ttsp", "width1", "width2", "width3", "width4", "cactus"):
        target = count if family in ("forest", "ttsp", "cactus") else max(1, count // 4)
        for rep in range(target):
            rng = random.Random(derived_seed("research_audit", family, rep))
            auxiliary = None
            if family == "forest":
                n = rng.randint(2, 10)
                edges = {edge(v, rng.randrange(v)) for v in range(1, n) if rng.random() > 0.15}
                solvers = ["forest-paper", "forest-dense", "forest-sparse", "cactus", "brute-cartesian"]
            elif family == "ttsp":
                n, edges, nodes, root = random_ttsp(rng.randint(1, 14), rng.uniform(0.1, 0.9), rng)
                solvers = ["ttsp-transfer", "ttsp-events", "brute-cartesian"]
            elif family == "cactus":
                n = 1; edges = set()
                while n < 8:
                    anchor = rng.randrange(n)
                    extra = min(rng.choice([1, 2, 3]), 9 - n)
                    path = [anchor] + list(range(n, n + extra))
                    edges.update(edge(u, v) for u, v in zip(path, path[1:]))
                    if extra > 1:
                        edges.add(edge(path[-1], anchor))
                    n += extra
                solvers = ["cactus", "brute-cartesian"]
            else:
                width = int(family[-1]); n = rng.randint(width + 1, min(9, width + 5))
                graph = random_partial_ktree(n, width, rng.choice([0.0, 0.3, 0.7]), rng)
                edges = graph.edges; solvers = ["tw-dp", "tw-dp-baseline", "brute-cartesian"]
            s, z = (0, 1) if family == "ttsp" else rng.sample(range(n), 2)
            labels = bernoulli_labels(edges, rng.randint(1, 4 if not family.startswith("width") else 3), 0.5, rng)
            tg = OUT / family / f"{rep}.tg"
            write_temporal_graph(tg, n, edges, labels, s, z)
            if family == "ttsp":
                auxiliary = tg.with_suffix(".sp"); write_sp(auxiliary, nodes, root)
            elif family.startswith("width"):
                auxiliary = tg.with_suffix(".ntd"); write_nice_decomposition(auxiliary, graph, s, z)
            for strict in (False, True):
                audit.add(family, f"{family}:{rep}", tg, auxiliary, solvers, oracle(n, labels, s, z, strict), strict)
        audit.flush(); print(f"audit {family}: {audit.cases[family]} query/mode cases", flush=True)


def atlas_campaign(audit: Audit):
    total = 0; selected = 0; by_n = {}
    for atlas_id, n, edges in atlas_graphs():
        total += 1
        if n < 2:
            continue
        graph = elimination_decomposition(n, edges)
        if graph is None:
            continue
        selected += 1; by_n[n] = by_n.get(n, 0) + 1
        rng = random.Random(derived_seed("research_atlas", str(atlas_id), 0))
        configurations = [all_labels(edges, 1), all_labels(edges, 2), bernoulli_labels(edges, 3, 0.5, rng)]
        for s in range(n):
            for z in range(n):
                if s == z:
                    continue
                base = OUT / "atlas" / f"g{atlas_id}-s{s}-z{z}"
                td = base.with_suffix(".ntd"); write_nice_decomposition(td, graph, s, z)
                for config, labels in enumerate(configurations):
                    tg = base.with_name(base.name + f"-l{config}.tg")
                    write_temporal_graph(tg, n, edges, labels, s, z)
                    for strict in (False, True):
                        audit.add("atlas_width2", f"atlas:{atlas_id}:{s}:{z}:{config}", tg, td,
                                  ["tw-dp", "tw-dp-baseline"], oracle(n, labels, s, z, strict), strict)
        if selected % 50 == 0:
            audit.flush(); print(f"atlas: {selected} selected graphs", flush=True)
    audit.flush()
    if total != 1253:
        raise RuntimeError("Graph Atlas must contain exactly 1253 graphs")
    return {"atlas_graphs_total": total, "graphs_width_at_most_2": selected,
            "selected_by_n": by_n, "label_configurations_per_query": 3,
            "all_ordered_terminal_pairs": True, "atlas_sha256": ATLAS_SHA}


def metamorphic_campaign(audit: Audit, count: int):
    for rep in range(count):
        rng = random.Random(derived_seed("metamorphic", "ttsp", rep))
        n, edges, nodes, root = random_ttsp(rng.randint(3, 12), 0.6, rng)
        labels = fixed_labels(edges, 5, 3, rng)
        permutation = list(range(n)); rng.shuffle(permutation)
        changed_edges = {edge(permutation[u], permutation[v]) for u, v in edges}
        changed_labels = {edge(permutation[u], permutation[v]): [-10**12 + 17*t for t in times]
                          for (u, v), times in labels.items()}
        changed_nodes = [(kind, tuple(permutation[v] for v in args) if kind == "edge" else args)
                         for kind, args in nodes]
        tg = OUT / "metamorphic" / f"{rep}.tg"; sp = tg.with_suffix(".sp")
        write_temporal_graph(tg, n, changed_edges, changed_labels, permutation[0], permutation[1])
        write_sp(sp, changed_nodes, root)
        for strict in (False, True):
            audit.add("metamorphic", str(rep), tg, sp, ["ttsp-events", "ttsp-transfer"],
                      oracle(n, labels, 0, 1, strict), strict)
    audit.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random", type=int, default=1000)
    parser.add_argument("--skip-atlas", action="store_true")
    parser.add_argument("--skip-exhaustive", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter(); results = ROOT / "results"; results.mkdir(exist_ok=True)
    exhaustive = None
    if not args.skip_exhaustive:
        run = subprocess.run([str(ROOT / "build" / "tpcount_exhaustive")], text=True, capture_output=True, check=True)
        exhaustive = json.loads(run.stdout)
        (results / "exhaustive_summary.json").write_text(json.dumps(exhaustive, indent=2) + "\n")
        print(run.stderr, end="", flush=True)
    with (results / "research_audit_cases.csv").open("w", newline="") as stream:
        writer = csv.writer(stream); writer.writerow(["family", "case", "solver", "expected_count", "answer_sha256"])
        audit = Audit(writer); random_campaign(audit, args.random)
        metamorphic_campaign(audit, max(1, args.random // 5))
        atlas = None if args.skip_atlas else atlas_campaign(audit)
    summary = {"master_seed": 20260928, "query_mode_cases": audit.cases,
               "solver_comparisons": audit.comparisons, "total_query_mode_cases": sum(audit.cases.values()),
               "total_solver_comparisons": sum(audit.comparisons.values()), "mismatches": 0,
               "answers_digest_sha256": audit.digest.hexdigest(), "exhaustive": exhaustive, "atlas": atlas,
               "wall_seconds": time.perf_counter() - started,
               "scope": "Exhaustive n<=4,r<=2 and n=5,r=1. n=5,r=2 is NOT exhaustive."}
    (results / "research_audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
