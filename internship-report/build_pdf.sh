#!/usr/bin/env bash
set -euo pipefail
report_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "${report_dir}/.." && pwd)"
cd "$report_dir"
mkdir -p build/tex-cache "${repo_dir}/output/pdf"
export TEXMFCACHE="${report_dir}/build/tex-cache"
export TEXMFVAR="${report_dir}/build/tex-cache"
export TEXINPUTS="${report_dir}/:${repo_dir}/uet-graduation-latex//:${TEXINPUTS:-}"
export OSFONTDIR="${OSFONTDIR:-/usr/share/fonts:/nix/store/0hh3qjia9jxgw8lfayf503lwkiqa274c-liberation-fonts-2.1.5/share/fonts/truetype}"
if ! command -v lualatex >/dev/null 2>&1; then
  if ! command -v nix >/dev/null 2>&1; then
    printf '%s\n' 'LuaLaTeX is required. Install TeX Live with fontspec, mathfont and siunitx.' >&2
    exit 1
  fi
  exec nix shell --impure --file "$report_dir/tex-env.nix" -c bash "$report_dir/build_pdf.sh"
fi
for pass in 1 2 3; do
  lualatex -interaction=nonstopmode -halt-on-error -file-line-error \
    -output-directory=build main.tex >"build/compile-${pass}.log" 2>&1 || {
      tail -70 "build/compile-${pass}.log"
      exit 1
    }
done
cp build/main.pdf "${repo_dir}/output/pdf/bao_cao_thuc_tap_uet.pdf"
printf '%s\n' "${repo_dir}/output/pdf/bao_cao_thuc_tap_uet.pdf"
