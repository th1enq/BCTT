#pragma once

#include "solvers.hpp"

#include <cstdint>
#include <string>
#include <istream>

namespace tp {

struct TwStats {
    std::uint64_t states_created{};
    std::uint64_t states_peak_bag{};
    std::uint64_t join_pairs_tested{};
    std::uint64_t join_pairs_possible{};
    std::uint64_t join_pairs_compatible{};
    std::uint64_t states_peak_live{};
    int width_input{-1};
};

struct TwOptions {
    bool prune_terminals{true};
    bool index_joins{true};
    bool release_tables{true};
    bool compact_terminals{true};
};

BigInt treewidth_dp(const TemporalGraph& graph, const std::string& decomposition_path,
                    TwStats* stats = nullptr, TwOptions options = {});
BigInt treewidth_dp_stream(const TemporalGraph& graph, std::istream& decomposition,
                          TwStats* stats = nullptr, TwOptions options = {});

} // namespace tp
