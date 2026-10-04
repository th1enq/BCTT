#pragma once

#include "solvers.hpp"

namespace tp {

struct DirectedEdge {
    int from{};
    int to{};
    const std::vector<int>* labels{};
};

struct DagStats {
    std::uint64_t temporal_events{};
    std::uint64_t additions{};
    std::uint64_t active_vertices{};
};

// Count time-respecting directed paths in an acyclic orientation. The caller
// must prove that these paths coincide with its desired undirected paths.
BigInt count_temporal_dag(const TemporalGraph& graph,
                         const std::vector<DirectedEdge>& edges,
                         DagStats* stats = nullptr);
BigInt cactus_count(const TemporalGraph& graph, DagStats* stats = nullptr);

} // namespace tp
