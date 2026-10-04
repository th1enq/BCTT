#pragma once

#include <cstdint>
#include <istream>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace tp {

struct EdgeKey {
    int u{};
    int v{};
    EdgeKey() = default;
    EdgeKey(int a, int b) : u(std::min(a, b)), v(std::max(a, b)) {}
    auto operator<=>(const EdgeKey&) const = default;
};

struct TemporalGraph {
    int n{};
    int s{};
    int z{};
    int r{};
    bool strict{}; // false: non-decreasing labels; true: strictly increasing
    std::vector<std::int64_t> rank_to_time; // index 0 is unused
    std::map<EdgeKey, std::vector<int>> labels;
    std::vector<std::vector<int>> adjacency;

    [[nodiscard]] std::size_t temporal_edges() const;
    [[nodiscard]] const std::vector<int>& times(int u, int v) const;
    [[nodiscard]] bool has_edge(int u, int v) const;
};

TemporalGraph read_temporal_graph(std::istream& in);
TemporalGraph read_temporal_graph_file(const std::string& path);

} // namespace tp
