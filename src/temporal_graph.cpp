#include "temporal_graph.hpp"

#include <algorithm>
#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <tuple>

namespace tp {

std::size_t TemporalGraph::temporal_edges() const {
    std::size_t total = 0;
    for (const auto& [edge, ts] : labels) {
        (void)edge;
        total += ts.size();
    }
    return total;
}

const std::vector<int>& TemporalGraph::times(int u, int v) const {
    static const std::vector<int> empty;
    const auto it = labels.find(EdgeKey(u, v));
    return it == labels.end() ? empty : it->second;
}

bool TemporalGraph::has_edge(int u, int v) const {
    return labels.contains(EdgeKey(u, v));
}

TemporalGraph read_temporal_graph(std::istream& in) {
    std::string line;
    int n = -1;
    long long declared_m = -1;
    int s = -1;
    int z = -1;
    std::set<std::tuple<int, int, std::int64_t>> triples;
    bool header_seen = false;
    long long rows_seen = 0;

    while (std::getline(in, line)) {
        const auto first = line.find_first_not_of(" \t\r");
        if (first == std::string::npos || line[first] == '#') continue;
        std::istringstream row(line);
        if (!header_seen) {
            char p{};
            if (!(row >> p >> n >> declared_m >> s >> z) || p != 'p') {
                throw std::runtime_error("expected header: p n m_temporal s z");
            }
            if (n <= 0 || declared_m < 0 || s < 0 || s >= n || z < 0 || z >= n || s == z) {
                throw std::runtime_error("invalid graph header");
            }
            header_seen = true;
            continue;
        }
        int u{}, v{};
        std::int64_t t{};
        if (!(row >> u >> v >> t)) throw std::runtime_error("invalid temporal-edge row");
        ++rows_seen;
        std::string extra;
        if (row >> extra) throw std::runtime_error("extra token in temporal-edge row");
        if (u < 0 || u >= n || v < 0 || v >= n) throw std::runtime_error("vertex out of range");
        if (u == v) throw std::runtime_error("self-loops are not supported");
        if (u > v) std::swap(u, v);
        triples.emplace(u, v, t);
    }
    if (!header_seen) throw std::runtime_error("missing graph header");
    if (rows_seen != declared_m) throw std::runtime_error("header m_temporal does not match the number of rows");

    std::vector<std::int64_t> raw_times;
    raw_times.reserve(triples.size());
    for (const auto& [u, v, t] : triples) {
        (void)u; (void)v;
        raw_times.push_back(t);
    }
    std::sort(raw_times.begin(), raw_times.end());
    raw_times.erase(std::unique(raw_times.begin(), raw_times.end()), raw_times.end());

    TemporalGraph graph;
    graph.n = n;
    graph.s = s;
    graph.z = z;
    graph.r = static_cast<int>(raw_times.size());
    graph.rank_to_time.resize(raw_times.size() + 1);
    for (std::size_t i = 0; i < raw_times.size(); ++i) graph.rank_to_time[i + 1] = raw_times[i];
    graph.adjacency.assign(n, {});

    for (const auto& [u, v, t] : triples) {
        const int rank = static_cast<int>(std::lower_bound(raw_times.begin(), raw_times.end(), t) - raw_times.begin()) + 1;
        graph.labels[EdgeKey(u, v)].push_back(rank);
    }
    for (const auto& [edge, ts] : graph.labels) {
        (void)ts;
        graph.adjacency[edge.u].push_back(edge.v);
        graph.adjacency[edge.v].push_back(edge.u);
    }
    for (auto& neighbors : graph.adjacency) std::sort(neighbors.begin(), neighbors.end());
    return graph;
}

TemporalGraph read_temporal_graph_file(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open temporal graph: " + path);
    return read_temporal_graph(input);
}

} // namespace tp
