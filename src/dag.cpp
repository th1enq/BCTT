#include "dag.hpp"

#include <algorithm>
#include <numeric>
#include <queue>
#include <stdexcept>

namespace tp {

BigInt count_temporal_dag(const TemporalGraph& graph,
                         const std::vector<DirectedEdge>& edges,
                         DagStats* output) {
    struct TemporalEdge { int from; int to; int time; };
    struct Event { std::size_t id; bool incoming; };
    DagStats stats;
    std::vector<int> indegree(graph.n, 0);
    std::vector<std::vector<int>> outgoing(graph.n);
    std::vector<TemporalEdge> temporal;
    std::vector<std::size_t> offsets(static_cast<std::size_t>(graph.r) + 2, 0);
    for (const auto& edge : edges) {
        outgoing[edge.from].push_back(edge.to);
        ++indegree[edge.to];
        for (int t : *edge.labels) {
            temporal.push_back({edge.from, edge.to, t});
            ++offsets[t + 1];
        }
    }
    // Stable counting sort by compressed rank: O(M+r), no n*r array.
    std::partial_sum(offsets.begin(), offsets.end(), offsets.begin());
    auto cursor = offsets;
    std::vector<std::size_t> ranked(temporal.size());
    for (std::size_t id = 0; id < temporal.size(); ++id)
        ranked[cursor[temporal[id].time]++] = id;
    std::vector<std::vector<Event>> events(graph.n);
    for (int t = 1; t <= graph.r; ++t) {
        // Equal-time ordering is semantic: incoming before outgoing for <=,
        // outgoing before incoming for <. Aggregate all incoming at a tie.
        for (int pass = 0; pass < 2; ++pass) {
            const bool incoming = graph.strict ? pass == 1 : pass == 0;
            for (std::size_t i = offsets[t]; i < offsets[t + 1]; ++i) {
                const auto id = ranked[i];
                const int v = incoming ? temporal[id].to : temporal[id].from;
                events[v].push_back({id, incoming});
            }
        }
    }
    std::queue<int> ready;
    for (int v = 0; v < graph.n; ++v) if (indegree[v] == 0) ready.push(v);
    std::vector<BigInt> values(temporal.size());
    BigInt answer = 0;
    int processed = 0;
    while (!ready.empty()) {
        const int v = ready.front(); ready.pop(); ++processed;
        BigInt prefix = v == graph.s ? BigInt(1) : BigInt(0);
        if (!events[v].empty()) ++stats.active_vertices;
        for (const auto& event : events[v]) {
            if (event.incoming) { prefix += values[event.id]; ++stats.additions; }
            else values[event.id] = prefix;
        }
        if (v == graph.z) answer = std::move(prefix);
        for (int w : outgoing[v]) if (--indegree[w] == 0) ready.push(w);
    }
    if (processed != graph.n) throw std::runtime_error("temporal DAG counter received a cyclic orientation");
    stats.temporal_events = 2 * temporal.size();
    if (output) *output = stats;
    return answer;
}

BigInt cactus_count(const TemporalGraph& graph, DagStats* stats) {
    // Iterative Tarjan edge-block decomposition, including disconnected graphs.
    struct StaticEdge { int u; int v; const std::vector<int>* labels; };
    std::vector<StaticEdge> edges;
    std::vector<std::vector<std::pair<int, int>>> adjacency(graph.n);
    for (const auto& [key, labels] : graph.labels) {
        const int id = static_cast<int>(edges.size());
        edges.push_back({key.u, key.v, &labels});
        adjacency[key.u].push_back({key.v, id});
        adjacency[key.v].push_back({key.u, id});
    }
    std::vector<int> discovered(graph.n, -1), low(graph.n), parent(graph.n, -1),
                     parent_edge(graph.n, -1), edge_stack;
    std::vector<std::size_t> next(graph.n, 0);
    std::vector<std::vector<int>> blocks;
    int clock = 0;
    for (int start = 0; start < graph.n; ++start) {
        if (discovered[start] >= 0) continue;
        std::vector<int> stack{start};
        discovered[start] = low[start] = clock++;
        while (!stack.empty()) {
            const int u = stack.back();
            if (next[u] < adjacency[u].size()) {
                const auto [v, id] = adjacency[u][next[u]++];
                if (id == parent_edge[u]) continue;
                if (discovered[v] < 0) {
                    parent[v] = u; parent_edge[v] = id; edge_stack.push_back(id);
                    discovered[v] = low[v] = clock++; stack.push_back(v);
                } else if (discovered[v] < discovered[u]) {
                    low[u] = std::min(low[u], discovered[v]); edge_stack.push_back(id);
                }
            } else {
                stack.pop_back();
                const int p = parent[u];
                if (p < 0) continue;
                low[p] = std::min(low[p], low[u]);
                if (low[u] >= discovered[p]) {
                    blocks.emplace_back();
                    int id;
                    do {
                        id = edge_stack.back(); edge_stack.pop_back(); blocks.back().push_back(id);
                    } while (id != parent_edge[u]);
                }
            }
        }
    }
    std::vector<std::vector<int>> block_tree(graph.n + blocks.size());
    std::vector<int> degree(graph.n, 0);
    for (std::size_t b = 0; b < blocks.size(); ++b) {
        std::vector<int> vertices;
        for (int id : blocks[b]) {
            for (int v : {edges[id].u, edges[id].v}) {
                if (degree[v]++ == 0) vertices.push_back(v);
            }
        }
        if (blocks[b].size() > 1) {
            if (vertices.size() != blocks[b].size()) throw std::runtime_error("cactus solver requires edge-or-cycle blocks");
            for (int v : vertices) if (degree[v] != 2) throw std::runtime_error("cactus solver requires simple cycle blocks");
        }
        const int block_id = graph.n + static_cast<int>(b);
        for (int v : vertices) {
            block_tree[v].push_back(block_id); block_tree[block_id].push_back(v); degree[v] = 0;
        }
    }
    std::vector<int> parent_path(block_tree.size(), -1);
    std::queue<int> queue; queue.push(graph.s); parent_path[graph.s] = graph.s;
    while (!queue.empty()) {
        const int u = queue.front(); queue.pop();
        for (int v : block_tree[u]) if (parent_path[v] < 0) { parent_path[v] = u; queue.push(v); }
    }
    if (parent_path[graph.z] < 0) return 0;
    std::vector<int> route;
    for (int v = graph.z; v != graph.s; v = parent_path[v]) route.push_back(v);
    route.push_back(graph.s); std::reverse(route.begin(), route.end());
    std::vector<DirectedEdge> oriented;
    std::vector<std::vector<std::pair<int, int>>> local(graph.n);
    for (std::size_t i = 1; i < route.size(); i += 2) {
        const int source = route[i - 1], sink = route[i + 1];
        const auto& block = blocks[route[i] - graph.n];
        if (block.size() == 1) {
            oriented.push_back({source, sink, edges[block[0]].labels}); continue;
        }
        std::vector<int> touched;
        for (int id : block) {
            const auto& edge = edges[id];
            if (local[edge.u].empty()) touched.push_back(edge.u);
            if (local[edge.v].empty()) touched.push_back(edge.v);
            local[edge.u].push_back({edge.v, id}); local[edge.v].push_back({edge.u, id});
        }
        for (const auto& [first, id] : local[source]) {
            int previous = source, current = first;
            oriented.push_back({source, first, edges[id].labels});
            while (current != sink) {
                const auto step = local[current][local[current][0].first == previous ? 1 : 0];
                oriented.push_back({current, step.first, edges[step.second].labels});
                previous = current; current = step.first;
            }
        }
        for (int v : touched) local[v].clear();
    }
    return count_temporal_dag(graph, oriented, stats);
}

} // namespace tp
