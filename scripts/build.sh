#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
build_dir="${repo_dir}/build"
mkdir -p "${build_dir}"

common=(-std=c++20 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -I"${repo_dir}/src")
sources=(temporal_graph solvers dag ttsp tw_dp)
objects=()
for source in "${sources[@]}"; do
  object="${build_dir}/${source}.o"
  g++ "${common[@]}" -c "${repo_dir}/src/${source}.cpp" -o "${object}"
  objects+=("${object}")
done
g++ "${common[@]}" "${repo_dir}/src/main.cpp" "${objects[@]}" -o "${build_dir}/tpcount"
g++ "${common[@]}" -DTPCOUNT_SOURCE_DIR="\"${repo_dir}\"" \
  "${repo_dir}/tests/test_core.cpp" "${objects[@]}" -o "${build_dir}/tpcount_tests"
"${build_dir}/tpcount_tests"
g++ "${common[@]}" "${repo_dir}/tests/exhaustive.cpp" "${objects[@]}" -o "${build_dir}/tpcount_exhaustive"
