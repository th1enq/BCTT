#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_dir}/thesis"
if [[ -f "${repo_dir}/results/figures/forest-scaling.tex" ]]; then
  bash "${repo_dir}/thesis/build_figures.sh"
fi

if command -v tectonic >/dev/null 2>&1; then
  tectonic --keep-logs --keep-intermediates main.tex
else
  nix shell nixpkgs#tectonic -c tectonic --keep-logs --keep-intermediates main.tex
fi

mkdir -p "${repo_dir}/results"
cp main.pdf "${repo_dir}/results/temporal_path_thesis.pdf"
echo "PDF: ${repo_dir}/results/temporal_path_thesis.pdf"
