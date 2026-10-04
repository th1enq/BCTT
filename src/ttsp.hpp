#pragma once

#include "solvers.hpp"
#include "dag.hpp"

#include <string>

namespace tp {

struct TtspStats {
    std::uint64_t scalar_products{};
    std::size_t nodes{};
};

BigInt ttsp_transfer(const TemporalGraph& graph, const std::string& decomposition_path,
                     TtspStats* stats = nullptr);
BigInt ttsp_events(const TemporalGraph& graph, const std::string& decomposition_path,
                  DagStats* stats = nullptr);

} // namespace tp
