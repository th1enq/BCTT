#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_dir}"
bash scripts/build.sh
python3 python/research_audit.py
python3 python/research_benchmark.py
python3 python/ladder_benchmark.py
python3 python/research_aggregate.py
bash thesis/build_figures.sh
bash thesis/build_pdf.sh
python3 python/research_validate.py
