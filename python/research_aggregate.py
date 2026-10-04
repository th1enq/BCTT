#!/usr/bin/env python3
"""Generate all publication tables/PGFPlots from the final raw CSV, never by hand."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
GENERATED = ROOT / "thesis" / "generated"
FIGURES = RESULTS / "figures"


def fmt(x):
    if x is None:
        return "T/O"
    return f"{float(x):.3g}"


def integer(x):
    return f"{int(x):,}".replace(",", r"\,")


def escape(text):
    return str(text).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def geomean(values):
    values = [v for v in values if v > 0]
    return math.exp(statistics.mean(map(math.log, values))) if values else None


def table(name, headers, rows, caption, label, alignment=None):
    alignment = alignment or "l" + "r" * (len(headers) - 1)
    lines = [r"\begin{table}[htbp]", r"\centering", r"\small", r"\setlength{\tabcolsep}{4pt}",
             r"\caption{" + caption + "}", r"\label{" + label + "}",
             r"\begin{tabular}{" + alignment + "}", r"\toprule",
             " & ".join(headers) + r" \\", r"\midrule"]
    lines += [" & ".join(map(str, row)) + r" \\" for row in rows]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    (GENERATED / f"{name}.tex").write_text("\n".join(lines), encoding="utf-8")


def plot(name, series, xlabel, ylabel="Solver time (ms)", xlog=False, ylog=True,
         extra="", legend="north west"):
    colors = ("blue!75!black", "orange!85!black", "green!50!black", "violet")
    marks = ("*", "square*", "triangle*", "diamond*")
    text = [r"\documentclass[tikz,border=4pt]{standalone}", r"\usepackage{fontspec}",
            r"\setmainfont{DejaVu Serif}", r"\usepackage{pgfplots}", r"\pgfplotsset{compat=1.18}",
            r"\begin{document}", r"\begin{tikzpicture}",
            r"\begin{axis}[width=14cm,height=8cm,grid=both,minor grid style={gray!12},",
            "xlabel={" + xlabel + "},ylabel={" + ylabel + "},",
            "legend pos=" + legend + ",legend style={font=\\small},",
            ("xmode=log," if xlog else "") + ("ymode=log," if ylog else "") + extra + "]"]
    for i, (label, points) in enumerate(series):
        if not points:
            continue
        text += [r"\addplot+[color=" + colors[i % 4] + ",mark=" + marks[i % 4] +
                 r",thick,error bars/.cd,y dir=both,y explicit] table[x=x,y=y,y error minus=minus,y error plus=plus] {",
                 "x y minus plus"]
        for x, median, low, high in sorted(points):
            text.append(f"{x} {median:.9g} {max(0,median-low):.9g} {max(0,high-median):.9g}")
        text += ["};", r"\addlegendentry{" + label + "}"]
    text += [r"\end{axis}", r"\end{tikzpicture}", r"\end{document}", ""]
    (FIGURES / f"{name}.tex").write_text("\n".join(text), encoding="utf-8")


def main():
    GENERATED.mkdir(exist_ok=True); FIGURES.mkdir(exist_ok=True)
    raw_path = RESULTS / "research_benchmark.csv"
    metadata = json.loads((RESULTS / "research_benchmark_metadata.json").read_text())
    audit = json.loads((RESULTS / "research_audit_summary.json").read_text())
    rows = list(csv.DictReader(raw_path.open()))
    raw_files = {raw_path.name: hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    ladder_path = RESULTS / "research_ladder.csv"
    ladder_metadata = RESULTS / "research_ladder_metadata.json"
    if ladder_path.exists() and ladder_metadata.exists():
        extra = json.loads(ladder_metadata.read_text())
        if extra["binary_sha256"] != metadata["binary_sha256"]:
            raise RuntimeError("main and ladder benchmarks use different binaries")
        rows.extend(csv.DictReader(ladder_path.open()))
        metadata["cases"] += extra["cases"]
        metadata["statuses"] = dict(Counter(metadata["statuses"]) + Counter(extra["statuses"]))
        raw_files[ladder_path.name] = hashlib.sha256(ladder_path.read_bytes()).hexdigest()
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["instance_id"], row["solver"])].append(row)
    summary = {}; expected_reps = metadata["repetitions"]
    numeric = ("wall_ms", "cpu_ms", "parse_ms", "process_wall_ms", "peak_rss_mb",
               "states_created", "states_peak_bag", "states_peak_live", "join_pairs_possible",
               "join_pairs_tested", "join_pairs_compatible", "temporal_events", "dag_additions")
    for key, current in grouped.items():
        ok = [r for r in current if r["status"] == "ok"]
        first = current[0]
        item = {k: first[k] for k in ("family", "instance_id", "solver", "n", "m_static", "m_temporal",
                                      "r", "nominal_r", "treewidth", "strict", "count_bits", "answer_sha256", "oracle")}
        item.update({"successful_samples": len(ok), "status": "ok" if len(ok) == expected_reps else "+".join(sorted({r["status"] for r in current}))})
        for field in numeric:
            values = [float(r[field]) for r in ok if r[field]]
            if values:
                q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive") if len(values) > 1 else [values[0]] * 3
                item[field + "_median"] = statistics.median(values)
                item[field + "_q1"] = q1; item[field + "_q3"] = q3; item[field + "_iqr"] = q3 - q1
                item[field + "_max"] = max(values)
        summary[key] = item
    fields = sorted(set().union(*(set(item) for item in summary.values())))
    with (RESULTS / "research_benchmark_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(summary.values())

    def get(family, identity, solver):
        return summary.get((family, identity, solver))

    def metric(family, identity, solver, field="wall_ms_median"):
        item = get(family, identity, solver)
        return item.get(field) if item and item["status"] == "ok" else None

    def speed(family, identity, slow, fast):
        a, b = metric(family, identity, slow), metric(family, identity, fast)
        return a / b if a is not None and b is not None and b else None

    audit_rows = []
    for c in audit["exhaustive"]["campaigns"]:
        audit_rows.append([f"Vét cạn $n={c['n']},r={c['r']}$", integer(c["queries_both_modes"]), integer(c["comparisons"]), "0"])
    names = {"forest": "Rừng ngẫu nhiên", "ttsp": "TTSP ngẫu nhiên", "cactus": "Cactus ngẫu nhiên",
             "metamorphic": "Đổi đỉnh và nhãn thời gian", "atlas_width2": "Graph Atlas, width $\\le2$"}
    width_cases = sum(v for k, v in audit["query_mode_cases"].items() if k.startswith("width"))
    width_comparisons = sum(v for k, v in audit["solver_comparisons"].items() if k.startswith("width"))
    for key in ("forest", "ttsp"):
        audit_rows.append([names[key], integer(audit["query_mode_cases"][key]), integer(audit["solver_comparisons"][key]), "0"])
    audit_rows.append(["Partial $k$-tree, $k=1..4$", integer(width_cases), integer(width_comparisons), "0"])
    for key in ("cactus", "metamorphic", "atlas_width2"):
        audit_rows.append([names[key], integer(audit["query_mode_cases"][key]), integer(audit["solver_comparisons"][key]), "0"])
    exhaustive_queries = sum(c["queries_both_modes"] for c in audit["exhaustive"]["campaigns"])
    comparisons = audit["exhaustive"]["comparisons"] + audit["total_solver_comparisons"]
    audit_rows.append([r"\textbf{Tổng lượt}", integer(exhaustive_queries + audit["total_query_mode_cases"]), integer(comparisons), "0"])
    table("audit-table", ["Chiến dịch", r"\shortstack{Truy vấn/\\ngữ nghĩa}", r"\shortstack{Đối chiếu\\solver}", "Sai lệch"], audit_rows,
          "Kiểm chứng mới; mỗi cặp đầu cuối được thử theo cả hai ngữ nghĩa thời gian.", "tab:audit-expanded")

    forest_rows = []
    for length, r in ((100, 100), (100, 1000), (500, 500), (1000, 200), (1000, 1000)):
        identity = f"L{length}-r{r}"
        forest_rows.append([f"{length}/{r}"] + [fmt(metric("forest_dense", identity, s)) for s in ("forest-paper", "forest-dense", "forest-sparse")]
                           + ["--" if speed("forest_dense", identity, "forest-paper", "forest-dense") is None else fmt(speed("forest_dense", identity, "forest-paper", "forest-dense"))])
    table("forest-table", ["$|P|/r$", "Paper ms", "Dense ms", "Sparse ms", "Paper/Dense"], forest_rows,
          "Median forest dày; T/O là timeout và không được dùng để tính speedup.", "tab:forest-repeated")
    density_rows = []
    for d in (1, 4, 16, 100, 1000):
        identity = f"L1000-r1000-d{d}"
        density_rows.append([str(d), "1000"] + [fmt(metric("forest_density_control", identity, s)) for s in ("forest-paper", "forest-dense", "forest-sparse")]
                            + [fmt(speed("forest_density_control", identity, "forest-dense", "forest-sparse"))])
    table("density-table", ["Nhãn/cạnh $d$", "$r$", "Paper ms", "Dense ms", "Sparse ms", "Dense/Sparse"], density_rows,
          "Kiểm soát mật độ: đường dài 1000 cạnh, compressed rank cố định 1000.", "tab:density-control")

    ttsp_rows = []
    targets = [("ttsp_dense", f"k{k}-r32", str(k)) for k in (1, 16, 64, 256)] + [
        ("ttsp_extra", "k32-r128-strict0", "32"), ("ttsp_sparse", "k1024-r10000-d4", "1024")]
    for family, identity, k in targets:
        fast = get(family, identity, "ttsp-events"); slow = get(family, identity, "ttsp-transfer")
        slow_time = "skip" if slow and slow["status"] == "skipped_budget" else fmt(metric(family, identity, "ttsp-transfer"))
        slow_rss = metric(family, identity, "ttsp-transfer", "peak_rss_mb_max")
        fast_rss = metric(family, identity, "ttsp-events", "peak_rss_mb_max")
        rss = ("--" if slow_rss is None else fmt(slow_rss)) + "/" + ("--" if fast_rss is None else fmt(fast_rss))
        ttsp_rows.append([k, fast["r"], slow_time, fmt(metric(family, identity, "ttsp-events")),
                          "--" if speed(family, identity, "ttsp-transfer", "ttsp-events") is None else fmt(speed(family, identity, "ttsp-transfer", "ttsp-events")), rss, fast["count_bits"]])
    table("ttsp-table", ["$k$", "$r$ thật", "Matrix ms", "Events ms", "M/E", "RSS M/E MiB", "Bit"], ttsp_rows,
          "TTSP: median thời gian và maximum peak RSS qua các lần đo; skip là giới hạn ngân sách.", "tab:ttsp-repeated")

    width_rows = []
    for width in (1, 2, 3, 4):
        identity = f"w{width}-n12-r8"
        width_rows.append([str(width)] + [fmt(metric("width", identity, s)) for s in ("brute", "tw-dp-baseline", "tw-dp")]
                          + [fmt(metric("width", identity, "tw-dp", "states_created_median"))])
    table("width-table", ["$w$", "Brute ms", "DP cũ ms", "DP mới ms", "Trạng thái mới"], width_rows,
          "Độ nhạy theo width tại n=12, r=8; mỗi width dùng một seed cố định.", "tab:width-sensitivity")

    variants = (("tw-dp-baseline", "DP cũ"), ("tw-dp", "Đầy đủ"), ("tw-dp/no-compact", "Bỏ compact"),
                ("tw-dp/no-prune", "Bỏ prune và compact"), ("tw-dp/no-index", "Bỏ index join"),
                ("tw-dp/no-release", "Giữ bảng con"))
    ablation_rows = []; effects = {}
    identities = [f"w2-n24-r8-rep{i}" for i in range(3)]
    for solver, label in variants:
        values = [metric("ablation", identity, solver) for identity in identities]
        elapsed = geomean([x for x in values if x is not None])
        states = statistics.median(metric("ablation", identity, solver, "states_created_median") for identity in identities)
        live = statistics.median(metric("ablation", identity, solver, "states_peak_live_median") for identity in identities)
        ratios = [metric("ablation", identity, solver, "join_pairs_tested_median") /
                  max(1, metric("ablation", identity, solver, "join_pairs_possible_median")) for identity in identities]
        ablation_rows.append([label, fmt(elapsed), integer(states), integer(live), fmt(100 * statistics.median(ratios)) + r"\%"])
        effects[solver] = geomean([speed("ablation", identity, solver, "tw-dp") for identity in identities
                                  if speed("ablation", identity, solver, "tw-dp") is not None])
    table("ablation-table", ["Cấu hình", "Median-GM ms", "States", "Peak live", "Join thử/có thể"], ablation_rows,
          "Ablation trên ba partial 2-tree: GM của median thời gian; median telemetry theo instance.", "tab:ablation")

    cactus_rows = []
    for k in (4, 16, 64, 256):
        identity = f"k{k}-r8-arbitrary"
        cactus_rows.append([str(k), fmt(metric("cactus", identity, "cactus")), fmt(metric("cactus", identity, "tw-dp")),
                            fmt(speed("cactus", identity, "tw-dp", "cactus"))])
    table("cactus-table", ["$k$", "Cactus ms", "Treewidth ms", "DP/Cactus"], cactus_rows,
          "Cactus với đầu cuối nội bộ tùy ý; toàn bộ đáp án đối chiếu công thức độc lập.", "tab:cactus-repeated")

    crossover_rows = []
    for n in (12, 24, 48, 96):
        identity = f"n{n}-r4-rep0"
        crossover_rows.append([str(n), fmt(metric("enumeration_crossover", identity, "brute")),
                                fmt(metric("enumeration_crossover", identity, "tw-dp"))])
    table("crossover-table", ["$n$", "Enumeration ms", "Treewidth ms"], crossover_rows,
          "Enumeration crossover tại width 2, r=4; các seed khác nhau được báo cáo đầy đủ.", "tab:enumeration-crossover")
    if any(key[0] == "ladder" for key in summary):
        ladder_rows = []
        for columns in (4, 8, 12, 16, 24, 32, 64):
            identity = f"c{columns}-r4"
            ladder_rows.append([str(columns), f"$2^{{{columns-1}}}$"] +
                               [fmt(metric("ladder", identity, s)) for s in ("brute", "tw-dp-baseline", "tw-dp")])
        table("ladder-table", ["Cột $c$", "Tuyến tĩnh", "Brute ms", "DP cũ ms", "DP mới ms"], ladder_rows,
              "Ladder width hai với r=4 và truy vấn top-left/bottom-right; oracle đóng cho mọi cell.", "tab:ladder")

    censored = [item for item in summary.values() if item["status"] != "ok"]
    table("censor-table", ["Họ", "Instance", "Solver", "Trạng thái"],
          [[escape(i["family"]), escape(i["instance_id"]), escape(i["solver"]), escape(i["status"])] for i in censored],
          "Mọi solver/cell không hoàn thành; không bị loại khỏi báo cáo.", "tab:censored", "llll")

    def points(family, solver, pattern, index=1):
        out = []
        for (f, identity, s), item in summary.items():
            match = re.fullmatch(pattern, identity)
            if f == family and s == solver and match and item["status"] == "ok":
                out.append((int(match.group(index)), item["wall_ms_median"], item["wall_ms_q1"], item["wall_ms_q3"]))
        return out
    plot("forest-scaling", [(label, points("forest_dense", solver, r"L1000-r(\d+)"))
         for solver, label in (("forest-paper", "Paper recurrence"), ("forest-dense", "Dense prefix"), ("forest-sparse", "Sparse scan"))],
         "Distinct ranks r (path length 1000)", xlog=True)
    plot("density-control", [(label, points("forest_density_control", solver, r"L1000-r1000-d(\d+)"))
         for solver, label in (("forest-paper", "Paper recurrence"), ("forest-dense", "Dense prefix"), ("forest-sparse", "Sparse scan"))],
         "Labels per path edge d (fixed r=1000)", xlog=True)
    plot("ttsp-scaling", [(label, points("ttsp_dense", solver, r"k(\d+)-r32"))
         for solver, label in (("ttsp-transfer", "Transfer matrix"), ("ttsp-events", "Sparse events"))],
         "Diamonds k (r=32)", xlog=True, extra="log basis x=2,")
    plot("partial2-scaling", [(label, points("partial2", solver, r"n(\d+)-r4-rep0"))
         for solver, label in (("tw-dp-baseline", "Original DP"), ("tw-dp", "Compact DP"))],
         "Vertices n (width 2, r=4)", xlog=True, extra="log basis x=2,")
    plot("width-scaling", [(label, points("width", solver, r"w(\d+)-n12-r8"))
         for solver, label in (("brute", "Enumeration"), ("tw-dp-baseline", "Original DP"), ("tw-dp", "Compact DP"))],
         "Input width w (n=12, r=8)", extra="xtick={1,2,3,4},")
    plot("cactus-scaling", [(label, points("cactus", solver, r"k(\d+)-r8-arbitrary"))
         for solver, label in (("cactus", "Block route/events"), ("tw-dp", "Compact treewidth DP"))],
         "Cycle blocks k (r=8, internal endpoints)", xlog=True, extra="log basis x=2,")
    if any(key[0] == "ladder" for key in summary):
        plot("ladder-scaling", [(label, points("ladder", solver, r"c(\d+)-r4"))
             for solver, label in (("brute", "Enumeration"), ("tw-dp-baseline", "Original DP"), ("tw-dp", "Compact DP"))],
             "Columns c (ladder width 2, r=4)", xlog=True, extra="log basis x=2,")

    paired = {}
    for family, slow, fast in (("forest_dense", "forest-paper", "forest-dense"),
                               ("ttsp_dense", "ttsp-transfer", "ttsp-events"),
                               ("partial2", "tw-dp-baseline", "tw-dp"), ("cactus", "tw-dp", "cactus")):
        identities = sorted({identity for f, identity, _ in summary if f == family})
        ratios = [speed(family, identity, slow, fast) for identity in identities]
        ratios = [r for r in ratios if r is not None]
        paired[family] = {"paired_cells": len(ratios), "geometric_mean_speedup": geomean(ratios),
                          "min_speedup": min(ratios), "max_speedup": max(ratios)}
    key = ("ttsp_dense", "k256-r32")
    macros = {"AuditComparisons": integer(comparisons), "AuditQueryModes": integer(exhaustive_queries + audit["total_query_mode_cases"]),
              "AtlasGraphs": str(audit["atlas"]["graphs_width_at_most_2"]), "BenchCases": str(metadata["cases"]),
              "BenchSuccessfulSamples": integer(metadata["statuses"].get("ok", 0)),
              "BenchTimeouts": str(metadata["statuses"].get("timeout", 0)), "BenchSkips": str(metadata["statuses"].get("skipped_budget", 0)),
              "TTSPMatrixTime": fmt(metric(*key, "ttsp-transfer")), "TTSPEventTime": fmt(metric(*key, "ttsp-events")),
              "TTSPSpeedup": fmt(speed(*key, "ttsp-transfer", "ttsp-events")),
              "TTSPMatrixRSS": fmt(metric(*key, "ttsp-transfer", "peak_rss_mb_max")),
              "TTSPEventRSS": fmt(metric(*key, "ttsp-events", "peak_rss_mb_max")),
              "ForestPairedCells": str(paired["forest_dense"]["paired_cells"]),
              "ForestCensoredCells": str(sum(i["family"] == "forest_dense" and i["solver"] == "forest-paper" for i in censored)),
              "ForestGeoSpeedup": fmt(paired["forest_dense"]["geometric_mean_speedup"]),
              "DPGeoSpeedup": fmt(paired["partial2"]["geometric_mean_speedup"]),
              "CactusGeoSpeedup": fmt(paired["cactus"]["geometric_mean_speedup"]),
              "AblationCombinedSpeedup": fmt(effects["tw-dp-baseline"])}
    (GENERATED / "benchmark-macros.tex").write_text("% Automatically generated; do not edit values by hand.\n" +
        "\n".join("\\newcommand{\\" + name + "}{" + value + "}" for name, value in macros.items()) + "\n")
    highlights = {"audit_comparisons": comparisons, "query_mode_evaluations": exhaustive_queries + audit["total_query_mode_cases"],
                  "benchmark_cases": metadata["cases"], "raw_rows": len(rows), "paired_speedups": paired,
                  "ablation_relative_to_full": effects, "censored_cells": len(censored),
                  "source_sha256": metadata["source_sha256"], "raw_csv_sha256": raw_files,
                  "statuses": metadata["statuses"]}
    (RESULTS / "research_highlights.json").write_text(json.dumps(highlights, indent=2) + "\n")
    report = ["# Final research benchmark report", "", "Generated from the final CSV; historical/exploratory CSVs are excluded.", "",
              f"Correctness: {comparisons:,} solver/oracle comparisons, zero mismatches; {audit['atlas']['graphs_width_at_most_2']} Atlas graphs.",
              f"Measurements: {metadata['cases']} cells, {len(rows)} raw records; statuses {dict(Counter(r['status'] for r in rows))}.",
              "Seven subprocess batches per completed cell; median/IQR, pinning, child CPU time, exact counts and hashes.", "",
              "The paper comparison is the literal forest recurrence after equal rank compression, not author code.",
              "Transfer matrices and the unoptimized treewidth DP are internal baselines.", "",
              "| Family | Paired cells | Geometric mean speedup | Min | Max |", "|---|---:|---:|---:|---:|"]
    for family, p in paired.items():
        report.append(f"| {family} | {p['paired_cells']} | {fmt(p['geometric_mean_speedup'])}x | {fmt(p['min_speedup'])}x | {fmt(p['max_speedup'])}x |")
    report += ["", "No censored cell enters a speedup average. Geometric means summarize this grid, not all graphs.", "",
               f"TTSP k=256,r=32: matrix {macros['TTSPMatrixTime']} ms vs events {macros['TTSPEventTime']} ms ({macros['TTSPSpeedup']}x); maximum process RSS {macros['TTSPMatrixRSS']} vs {macros['TTSPEventRSS']} MiB.", "",
               "## Censored solver/cells", "", "| Family | Instance | Solver | Status |", "|---|---|---|---|"]
    report += [f"| {i['family']} | {i['instance_id']} | {i['solver']} | {i['status']} |" for i in censored]
    report += ["", "Remaining limits: no full n=5,r=2 exhaustive campaign, no independent proof referee, no real-world temporal dataset in this campaign.",
               "CPU frequency is not locked. RSS includes input parsing and allocator retention. Strict timings cover a subset, correctness audits cover both modes.", ""]
    (RESULTS / "RESEARCH_BENCHMARK_REPORT.md").write_text("\n".join(report))
    print(json.dumps(highlights, indent=2))


if __name__ == "__main__":
    main()
