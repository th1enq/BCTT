#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_dir}/results/figures"
figures=(forest-scaling density-control ttsp-scaling partial2-scaling width-scaling cactus-scaling ladder-scaling)
for figure in "${figures[@]}"; do
  if [[ -f "${figure}.pdf" && "${figure}.pdf" -nt "${figure}.tex" ]]; then
    continue
  fi
  if command -v tectonic >/dev/null 2>&1; then
    tectonic "${figure}.tex"
  else
    nix shell nixpkgs#tectonic -c tectonic "${figure}.tex"
  fi
done
