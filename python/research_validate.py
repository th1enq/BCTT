#!/usr/bin/env python3
"""Fail-closed integrity checks for the final research release artifacts."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hash():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src").glob("*.cpp")) + sorted((ROOT / "src").glob("*.hpp")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    return digest.hexdigest()


def main():
    source = source_hash()
    binary = sha(ROOT / "build" / "tpcount")
    all_rows = []
    artifact_hashes = {}
    input_hashes = {}
    for name, controller in (("research_benchmark", "research_benchmark.py"),
                             ("research_ladder", "ladder_benchmark.py")):
        raw = RESULTS / f"{name}.csv"
        meta_path = RESULTS / f"{name}_metadata.json"
        meta = json.loads(meta_path.read_text())
        require(meta["source_sha256"] == source, f"stale C++ source: {name}")
        require(meta["binary_sha256"] == binary, f"stale binary: {name}")
        require(meta["controller_sha256"] == sha(ROOT / "python" / controller), f"stale controller: {name}")
        require(meta["generator_sha256"] == sha(ROOT / "python" / "generators.py"), f"stale generator: {name}")
        require(meta["repetitions"] == 7, f"unexpected repetition design: {name}")
        if name == "research_ladder":
            require(meta["base_controller_sha256"] == sha(ROOT / "python" / "research_benchmark.py"), "stale ladder timing dependency")
        rows = list(csv.DictReader(raw.open()))
        require(len(rows) == meta["rows"], f"row count: {name}")
        require(dict(Counter(r["status"] for r in rows)) == meta["statuses"], f"status count: {name}")
        require(len({(r["family"], r["instance_id"]) for r in rows}) == meta["cases"], f"instance count: {name}")
        all_rows.extend(rows)
        artifact_hashes[raw.name] = sha(raw)
        artifact_hashes[meta_path.name] = sha(meta_path)

    grouped = defaultdict(list)
    cell_answers = defaultdict(set)
    for row in all_rows:
        key = (row["family"], row["instance_id"], row["solver"])
        grouped[key].append(row)
        require(row["source_sha256"] == source, f"mixed sources: {key}")
        require(0 <= int(row["s"]) < int(row["n"]) and 0 <= int(row["z"]) < int(row["n"]), f"terminal range: {key}")
        require(row["s"] != row["z"], f"equal terminals: {key}")
        input_family = "partial2" if row["family"] == "enumeration_crossover" else row["family"]
        tg = ROOT / "benchmarks" / "generated" / "research-benchmark" / input_family / (row["instance_id"] + ".tg")
        if tg not in input_hashes:
            input_hashes[tg] = sha(tg)
        require(input_hashes[tg] == row["input_sha256"], f"input changed: {key}")
        if row["auxiliary_sha256"]:
            candidates = [tg.with_suffix(ext) for ext in (".sp", ".ntd")]
            require(any(p.exists() and sha(p) == row["auxiliary_sha256"] for p in candidates), f"decomposition changed: {key}")
        require(row["status"] in {"ok", "timeout", "skipped_budget"}, f"unexpected failure: {key}")
        if row["status"] != "ok":
            require(not row["count_decimal"] and not row["wall_ms"], f"censored record has successful measurement: {key}")
            continue
        count = int(row["count_decimal"])
        require(count >= 0 and count.bit_length() == int(row["count_bits"]), f"invalid exact count: {key}")
        require(hashlib.sha256(str(count).encode()).hexdigest() == row["answer_sha256"], f"answer hash: {key}")
        cell_answers[key[:2]].add(row["answer_sha256"])
        for field in ("wall_ms", "cpu_ms", "parse_ms", "process_wall_ms", "peak_rss_mb"):
            value = float(row[field])
            require(math.isfinite(value) and value >= 0, f"invalid {field}: {key}")
        require(1 <= int(row["batch_repeats"]) <= 256, f"batch bounds: {key}")
        if row["solver"] == "ttsp-events":
            require(int(row["dag_additions"]) == int(row["m_temporal"]), f"event arithmetic: {key}")
            require(int(row["temporal_events"]) == 2 * int(row["m_temporal"]), f"event size: {key}")
        if row["join_pairs_tested"]:
            require(int(row["join_pairs_compatible"]) <= int(row["join_pairs_tested"]) <= int(row["join_pairs_possible"]), f"join telemetry: {key}")
    require(all(len(values) == 1 for values in cell_answers.values()), "solver counts disagree in benchmark")

    summary_path = RESULTS / "research_benchmark_summary.csv"
    summary = {(r["family"], r["instance_id"], r["solver"]): r for r in csv.DictReader(summary_path.open())}
    require(set(summary) == set(grouped), "missing or extra summary cells")
    completed = 0
    for key, rows in grouped.items():
        ok = [r for r in rows if r["status"] == "ok"]
        if ok:
            require(len(ok) == 7 and {int(r["replicate"]) for r in ok} == set(range(7)), f"incomplete or duplicate samples: {key}")
            require(summary[key]["status"] == "ok", f"incorrect summary status: {key}")
            for field in ("wall_ms", "cpu_ms", "peak_rss_mb"):
                values = [float(r[field]) for r in ok]
                q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
                for suffix, expected in (("median", statistics.median(values)), ("q1", q1), ("q3", q3), ("max", max(values))):
                    require(math.isclose(float(summary[key][field + "_" + suffix]), expected, rel_tol=1e-12, abs_tol=1e-12), f"incorrect statistic: {key}/{field}/{suffix}")
            completed += 1
        else:
            require(summary[key]["status"] != "ok", f"censored summary marked ok: {key}")

    audit_path = RESULTS / "research_audit_summary.json"
    audit = json.loads(audit_path.read_text())
    require(audit["mismatches"] == 0 and audit["exhaustive"]["mismatches"] == 0, "correctness mismatch recorded")
    require(audit["atlas"]["atlas_sha256"] == sha(ROOT / "benchmarks" / "data" / "atlas.dat.gz"), "Atlas checksum")
    answer_digest = hashlib.sha256()
    comparisons = 0
    audit_csv = RESULTS / "research_audit_cases.csv"
    with audit_csv.open() as stream:
        for row in csv.DictReader(stream):
            count = row["expected_count"]
            require(hashlib.sha256(count.encode()).hexdigest() == row["answer_sha256"], "audit answer hash")
            answer_digest.update(f"{row['family']}:{row['case']}:{row['solver']}:{count}\n".encode())
            comparisons += 1
    require(comparisons == audit["total_solver_comparisons"], "audit comparison rows")
    require(answer_digest.hexdigest() == audit["answers_digest_sha256"], "audit answer digest")
    require(sum(c["comparisons"] for c in audit["exhaustive"]["campaigns"]) == audit["exhaustive"]["comparisons"], "exhaustive total")

    highlights = json.loads((RESULTS / "research_highlights.json").read_text())
    require(highlights["raw_rows"] == len(all_rows), "stale highlights")
    require(highlights["raw_csv_sha256"] == {k: v for k, v in artifact_hashes.items() if k.endswith(".csv")}, "stale raw CSV hashes")
    require(highlights["audit_comparisons"] == comparisons + audit["exhaustive"]["comparisons"], "wrong combined audit total")
    pdf = RESULTS / "temporal_path_thesis.pdf"
    require(pdf.read_bytes().startswith(b"%PDF-"), "missing PDF")
    tex_files = sorted((ROOT / "thesis").rglob("*.tex"))
    require(pdf.stat().st_mtime >= max(p.stat().st_mtime for p in tex_files), "PDF older than manuscript")
    for tex in sorted((RESULTS / "figures").glob("*-*.tex")):
        figure = tex.with_suffix(".pdf")
        require(figure.exists() and figure.stat().st_mtime >= tex.stat().st_mtime, f"stale figure: {tex.name}")
        artifact_hashes[str(figure.relative_to(RESULTS))] = sha(figure)
    for path in (summary_path, audit_path, audit_csv, pdf):
        artifact_hashes[path.name] = sha(path)
    tex_digest = hashlib.sha256()
    for path in tex_files:
        tex_digest.update(str(path.relative_to(ROOT)).encode() + b"\0" + path.read_bytes())
    result = {"status": "passed", "source_sha256": source, "binary_sha256": binary,
              "validation_controller_sha256": sha(Path(__file__)),
              "aggregation_controller_sha256": sha(ROOT / "python" / "research_aggregate.py"),
              "thesis_source_sha256": tex_digest.hexdigest(), "benchmark_instances": len(cell_answers),
              "raw_records": len(all_rows), "completed_solver_cells": completed,
              "censored_solver_cells": len(grouped) - completed,
              "audit_comparisons": highlights["audit_comparisons"], "artifact_sha256": artifact_hashes}
    (RESULTS / "research_release_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "artifact_sha256"}, indent=2))


if __name__ == "__main__":
    main()
