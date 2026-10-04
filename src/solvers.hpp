#pragma once

#include "bigint.hpp"
#include "temporal_graph.hpp"

#include <cstdint>
#include <vector>

namespace tp {

std::vector<int> unique_forest_path(const TemporalGraph& graph);
BigInt forest_paper(const TemporalGraph& graph);
BigInt forest_dense_prefix(const TemporalGraph& graph);
BigInt forest_sparse(const TemporalGraph& graph);
BigInt static_path_reference(const TemporalGraph& graph);
BigInt temporal_dfs_reference(const TemporalGraph& graph);
std::uint64_t bit_length(const BigInt& value);
BigInt binomial(unsigned n, unsigned k);

} // namespace tp
