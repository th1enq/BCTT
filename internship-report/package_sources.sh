#!/usr/bin/env bash
set -euo pipefail
report_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "${report_dir}/.." && pwd)"
cd "$repo_dir"
mkdir -p output/pdf
{
  rg --files internship-report | rg -v '^internship-report/build/'
  printf '%s\n' \
    template.pdf \
    uet-graduation-latex/uetgraduation.cls \
    uet-graduation-latex/sizes.clo \
    'uet-graduation-latex/UET logo.pdf' \
    uet-graduation-latex/LICENSE.txt \
    uet-graduation-latex/README.md \
    results/figures/forest-scaling.pdf
} | sort | zip -q output/pdf/bao_cao_thuc_tap_uet_latex.zip -@
unzip -tq output/pdf/bao_cao_thuc_tap_uet_latex.zip
