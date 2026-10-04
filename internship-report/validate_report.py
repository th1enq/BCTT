#!/usr/bin/env python3
"""Check report data, references, typography diagnostics and page budget."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    pdf = ROOT / "output/pdf/bao_cao_thuc_tap_uet.pdf"
    require(pdf.is_file() and pdf.read_bytes().startswith(b"%PDF-"), "Missing report PDF")
    aux = (REPORT / "build/main.aux").read_text(encoding="utf-8")
    log = (REPORT / "build/compile-3.log").read_text(encoding="utf-8")
    for forbidden in ("Missing character:", "Overfull", "undefined", "unreferenced destination", "Fatal error"):
        require(forbidden not in log, f"LaTeX diagnostic: {forbidden}")
    def page(label):
        match = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{[^}]*\}\{(\d+)\}", aux)
        require(match is not None, f"Missing page label: {label}")
        return int(match.group(1))
    start, end = page("report:body:start"), page("report:body:end")
    body_pages = end - start + 1
    require(start == 1 and 10 <= body_pages <= 15, f"Body page budget: {body_pages}")
    sources = [REPORT / "main.tex", *sorted(REPORT.glob("*.tex")), *sorted((REPORT / "chapters").glob("*.tex"))]
    source_text = "\n".join(p.read_text(encoding="utf-8") for p in sources)
    cites = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", source_text):
        cites.update(group.split(","))
    bibliography = set(re.findall(r"\\bibitem\{([^}]+)\}", (REPORT / "references.tex").read_text(encoding="utf-8")))
    require(cites == bibliography, "Citation/bibliography mismatch")
    for token in (r"\begin{lstlisting}", r"\begin{minted}", "TODO", "TBD", "turn13view"):
        require(token not in source_text, f"Unexpected report content: {token}")
    manifest_path = REPORT / "generated/data-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["research_inputs_sha256"].items():
        require(sha(ROOT / "results" / name) == expected, f"Changed research data: {name}")
    for name, expected in manifest["unchanged_inputs_sha256"].items():
        require(sha(ROOT / name) == expected, f"Changed original asset: {name}")
    for name, expected in manifest["generated_files_sha256"].items():
        require(sha(REPORT / "generated" / name) == expected, f"Edited generated table: {name}")
    pdfinfo, pdftotext = shutil.which("pdfinfo"), shutil.which("pdftotext")
    require(pdfinfo and pdftotext, "Poppler pdfinfo and pdftotext are required")
    info = subprocess.check_output([pdfinfo, str(pdf)], text=True)
    total_pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    text = subprocess.check_output([pdftotext, "-layout", str(pdf), "-"], text=True)
    require("??" not in text and "\ufffd" not in text, "Unresolved reference or invalid character")
    for value in ("Quách Đức Thiện", "23020161", "Trần Mạnh Cường", "741", "280", "poly", "Bell", "log"):
        require(value in text, f"Missing PDF text/formula: {value}")
    pages = text.split("\f")
    require(len(pages) - 1 == total_pages, "Unexpected extracted page count")
    require(all(len(p.strip()) > 25 for p in pages[:-1]), "Unexpected blank page")
    chapter_titles = re.findall(r"\\chapter\{([^}]+)\}", source_text)
    require(len(chapter_titles) == 5, "Expected exactly five content chapters")
    visual_path = REPORT / "generated/visual-review.json"
    visual_status = "pending"
    if visual_path.exists():
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        if (visual.get("pdf_sha256") == sha(pdf) and visual.get("status") == "passed"
                and visual.get("reviewed_pdf_pages") == list(range(1, total_pages + 1))):
            visual_status = "passed"
    result = {"status": "passed", "pdf_sha256": sha(pdf), "total_pages": total_pages,
              "body_start": start, "body_end": end, "body_pages": body_pages,
              "citations": sorted(cites), "missing_glyphs": 0, "overfull_boxes": 0,
              "original_assets_preserved": True, "data_manifest_sha256": sha(manifest_path),
              "generated_tables_checked": len(manifest["generated_files_sha256"]),
              "visual_review": visual_status}
    (REPORT / "generated/verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {total_pages} pages, {body_pages} content pages, references/data/fonts checked.")


if __name__ == "__main__":
    main()
