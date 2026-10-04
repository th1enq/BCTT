#!/usr/bin/env python3
"""Read existing research artifacts; generate report-only tables and macros.

No solver, benchmark, thesis file or existing research result is modified.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parent
RESULTS = ROOT / "results"
OUT = REPORT / "generated"


def load_json(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integer(value):
    return f"{int(value):,}".replace(",", r"\,")


def number(value, precision=3):
    return r"\num{" + f"{float(value):.{precision}g}" + "}"


def gm(values):
    return math.exp(statistics.mean(map(math.log, values)))


def write_table(name, caption, label, headers, rows, alignment, note=""):
    lines = [r"\begin{table}[htbp]{" + caption + "}",
             r"\label{" + label + "}", r"\centering\small",
             r"\setlength{\tabcolsep}{4pt}", r"\renewcommand{\arraystretch}{1.16}",
             r"\begin{tabular}{" + alignment + "}", r"\toprule",
             " & ".join(headers) + r" \\", r"\midrule"]
    lines += [" & ".join(row) + r" \\" for row in rows]
    lines += [r"\bottomrule", r"\end{tabular}"]
    if note:
        lines += [r"\par\vspace{3pt}\begin{minipage}{0.97\linewidth}\footnotesize "
                  + note + r"\end{minipage}"]
    lines += [r"\end{table}", ""]
    (OUT / (name + ".tex")).write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    highlights = load_json("research_highlights.json")
    audit = load_json("research_audit_summary.json")
    metadata = load_json("research_benchmark_metadata.json")
    provenance = {}
    rows = []
    for name, expected in highlights["raw_csv_sha256"].items():
        path = RESULTS / name
        assert digest(path) == expected, f"Research CSV changed: {name}"
        provenance[name] = expected
        with path.open(newline="", encoding="utf-8") as stream:
            rows.extend(csv.DictReader(stream))
    assert len(rows) == highlights["raw_rows"]
    assert dict(Counter(r["status"] for r in rows)) == highlights["statuses"]
    assert len({(r["family"], r["instance_id"]) for r in rows}) == highlights["benchmark_cases"]
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["instance_id"], row["solver"])].append(row)
    measured = {}
    for key, samples in grouped.items():
        ok = [r for r in samples if r["status"] == "ok"]
        if not ok:
            continue
        assert len(ok) == metadata["repetitions"] == 7, key
        assert len({r["answer_sha256"] for r in ok}) == 1, key
        item = dict(ok[0])
        for metric in ("wall_ms", "peak_rss_mb", "states_created", "states_peak_live"):
            values = [float(r[metric]) for r in ok]
            item[metric + "_median"] = statistics.median(values)
            item[metric + "_max"] = max(values)
        measured[key] = item

    comparisons = [
        ("forest_dense", "forest-paper", "forest-dense", "Rừng dày", "Truy hồi bài gốc", "Tổng tiền tố"),
        ("ttsp_dense", "ttsp-transfer", "ttsp-events", "TTSP dày", "Ma trận nội bộ", "Quét sự kiện"),
        ("partial2", "tw-dp-baseline", "tw-dp", "Partial 2-tree", "DP nội bộ cũ", "DP tối giản"),
        ("cactus", "tw-dp", "cactus", "Cactus", "DP tổng quát", "Quét theo block"),
    ]
    speed_rows = []
    for family, slow, fast, label, baseline, proposed in comparisons:
        ratios = []
        for f, identity, solver in measured:
            other = (f, identity, slow)
            if f == family and solver == fast and other in measured:
                ratios.append(measured[other]["wall_ms_median"] / measured[(f, identity, fast)]["wall_ms_median"])
        expected = highlights["paired_speedups"][family]
        assert len(ratios) == expected["paired_cells"]
        assert math.isclose(gm(ratios), expected["geometric_mean_speedup"], rel_tol=1e-12)
        speed_rows.append([label, baseline, proposed, str(len(ratios)), number(gm(ratios))])
    write_table("speedups", "Tăng tốc trên các trường hợp ghép cặp hoàn thành.",
                "tab:speedups", ["Họ đồ thị", "Đối chứng", "Đề xuất", "$K$", "GM"],
                speed_rows, "p{2.4cm}p{3.1cm}p{2.6cm}rr",
                "GM là trung bình nhân của tỷ số thời gian đối chứng/đề xuất; $K$ là số trường hợp ghép cặp. "
                "Chỉ đối chứng ở hàng rừng tái hiện truy hồi của bài báo gốc; các hàng còn lại là đối chứng của dự án.")

    cpp_queries = sum(c["queries_both_modes"] for c in audit["exhaustive"]["campaigns"])
    atlas_queries = audit["query_mode_cases"]["atlas_width2"]
    atlas_comparisons = audit["solver_comparisons"]["atlas_width2"]
    total_queries = cpp_queries + audit["total_query_mode_cases"]
    total_comparisons = audit["exhaustive"]["comparisons"] + audit["total_solver_comparisons"]
    assert total_queries == highlights["query_mode_evaluations"]
    assert total_comparisons == highlights["audit_comparisons"]
    write_table("audit", "Phạm vi kiểm chứng tính đúng của các thuật toán.", "tab:audit",
                ["Chiến dịch", r"\shortstack{Lượt truy vấn/\\ngữ nghĩa}", "Đối chiếu", "Sai lệch"],
                [["Vét cạn nhỏ", integer(cpp_queries), integer(audit["exhaustive"]["comparisons"]), "0"],
                 ["Ngẫu nhiên và biến đổi", integer(audit["total_query_mode_cases"]-atlas_queries),
                  integer(audit["total_solver_comparisons"]-atlas_comparisons), "0"],
                 [r"Graph Atlas, $w\le2$", integer(atlas_queries), integer(atlas_comparisons), "0"],
                 [r"\textbf{Tổng lượt}", integer(total_queries), integer(total_comparisons), "0"]],
                "p{5.2cm}rrr",
                "Một lượt truy vấn/ngữ nghĩa có thể tạo nhiều đối chiếu giữa các thuật toán. "
                "Các tổng trên không phải số đồ thị khác nhau.")

    variants = [("tw-dp-baseline", "DP nội bộ cũ"), ("tw-dp", "DP đầy đủ"),
                ("tw-dp/no-compact", "Không xóa nhãn đầu cuối"),
                ("tw-dp/no-prune", "Không cắt tỉa và xóa nhãn"),
                ("tw-dp/no-index", "Không lọc cặp ghép"),
                ("tw-dp/no-release", "Giữ mọi bảng con")]
    ablation_rows = []
    for solver, title in variants:
        items = [measured[("ablation", f"w2-n24-r8-rep{i}", solver)] for i in range(3)]
        ablation_rows.append([title, number(gm([x["wall_ms_median"] for x in items])),
                              integer(statistics.median(x["states_created_median"] for x in items)),
                              integer(statistics.median(x["states_peak_live_median"] for x in items))])
    write_table("ablation", "Đóng góp của từng tối ưu trên ba partial 2-tree ($n=24$, $r=8$).",
                "tab:ablation", ["Cấu hình", "Thời gian (ms)", "Trạng thái tạo", r"\shortstack{Trạng thái\\sống cực đại}"],
                ablation_rows, "p{6cm}rrr",
                "Thời gian là trung bình nhân của ba trung vị; hai cột cuối là trung vị theo trường hợp. "
                "Số trạng thái sống là số trạng thái đồng thời đang được giữ, không phải số đỉnh đồ thị.")

    representative = []
    for columns in (8, 16, 24, 64):
        cells = [measured.get(("ladder", f"c{columns}-r4", solver))
                 for solver in ("brute", "tw-dp-baseline", "tw-dp")]
        representative.append([str(columns), f"$2^{{{columns-1}}}$"] +
                              [number(c["wall_ms_median"]) if c else "Hết giờ" for c in cells])
    write_table("ladder", "Ladder có độ rộng hai, $r=4$, đầu cuối trên-trái và dưới-phải.",
                "tab:ladder", ["Số cột $c$", "Đường đi tĩnh", "Liệt kê (ms)", "DP cũ (ms)", "DP mới (ms)"],
                representative, "lrrrr",
                "Mỗi số đo là trung vị của bảy mẫu. Hết giờ nghĩa là tiến trình không hoàn thành trong 3 giây; "
                "không thay bằng một thời gian giả để tính tỷ số tăng tốc.")

    dense_matrix = measured[("ttsp_dense", "k256-r32", "ttsp-transfer")]
    dense_events = measured[("ttsp_dense", "k256-r32", "ttsp-events")]
    extra_matrix = measured[("ttsp_extra", "k32-r128-strict0", "ttsp-transfer")]
    extra_events = measured[("ttsp_extra", "k32-r128-strict0", "ttsp-events")]
    sparse = measured[("ttsp_sparse", "k1024-r10000-d4", "ttsp-events")]
    dense_control = measured[("forest_density_control", "L1000-r1000-d1", "forest-dense")]
    sparse_control = measured[("forest_density_control", "L1000-r1000-d1", "forest-sparse")]
    macros = {
        "AuditComparisons": integer(total_comparisons), "QueryModeCases": integer(total_queries),
        "BenchmarkCases": str(highlights["benchmark_cases"]), "RawRows": integer(len(rows)),
        "CompletedSolverCases": str(len(measured)),
        "ForestGM": number(highlights["paired_speedups"]["forest_dense"]["geometric_mean_speedup"]),
        "TTSPGM": number(highlights["paired_speedups"]["ttsp_dense"]["geometric_mean_speedup"]),
        "PartialGM": number(highlights["paired_speedups"]["partial2"]["geometric_mean_speedup"]),
        "CactusGM": number(highlights["paired_speedups"]["cactus"]["geometric_mean_speedup"]),
        "TTSPMatrixTime": number(dense_matrix["wall_ms_median"]),
        "TTSPEventsTime": number(dense_events["wall_ms_median"]),
        "TTSPMatrixRSS": number(dense_matrix["peak_rss_mb_max"]),
        "TTSPEventsRSS": number(dense_events["peak_rss_mb_max"]),
        "TTSPExampleSpeed": number(dense_matrix["wall_ms_median"] / dense_events["wall_ms_median"]),
        "TTSPExtraSpeed": number(extra_matrix["wall_ms_median"] / extra_events["wall_ms_median"]),
        "TTSPSparseTime": number(sparse["wall_ms_median"]), "TTSPSparseRanks": integer(sparse["r"]),
        "SparseControlSpeed": number(dense_control["wall_ms_median"] / sparse_control["wall_ms_median"]),
    }
    (OUT / "numbers.tex").write_text("% Generated from verified, existing research artifacts.\n" +
        "\n".join(f"\\newcommand{{\\{key}}}{{{value}}}" for key, value in macros.items()) + "\n", encoding="utf-8")
    for name in ("research_benchmark_summary.csv", "research_highlights.json", "research_audit_summary.json",
                 "research_benchmark_metadata.json", "research_ladder_metadata.json"):
        provenance[name] = digest(RESULTS / name)
    protected = ["template.pdf", "results/temporal_path_thesis.pdf", "uet-graduation-latex/uetgraduation.cls",
                 "uet-graduation-latex/sizes.clo", "uet-graduation-latex/UET logo.pdf"]
    manifest = {"research_inputs_sha256": provenance,
                "unchanged_inputs_sha256": {name: digest(ROOT / name) for name in protected},
                "benchmark_cases": highlights["benchmark_cases"],
                "raw_rows": len(rows), "completed_solver_cases": len(measured),
                "comparisons": total_comparisons, "query_mode_cases": total_queries,
                "statuses": highlights["statuses"],
                "generated_files_sha256": {p.name: digest(p) for p in sorted(OUT.glob("*.tex"))}}
    (OUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(rows)} records; generated report-only tables for {total_comparisons} comparisons.")


if __name__ == "__main__":
    main()
