#include "solvers.hpp"

#include <algorithm>
#include <functional>
#include <queue>
#include <numeric>
#include <stdexcept>

namespace tp {

namespace {

void require_forest(const TemporalGraph& graph) {
    std::vector<int> parent(graph.n), size(graph.n, 1);
    std::iota(parent.begin(), parent.end(), 0);
    auto find = [&](int u) {
        while (parent[u] != u) { parent[u] = parent[parent[u]]; u = parent[u]; }
        return u;
    };
    for (const auto& [edge, labels] : graph.labels) {
        (void)labels;
        int a = find(edge.u), b = find(edge.v);
        if (a == b) throw std::runtime_error("forest solver requires an acyclic underlying graph");
        if (size[a] < size[b]) std::swap(a, b);
        parent[b] = a; size[a] += size[b];
    }
}

BigInt count_labels_on_path(const TemporalGraph& graph, const std::vector<int>& path) {
    if (path.size() < 2) return 0;
    std::vector<BigInt> counts(graph.times(path[0], path[1]).size(), 1);
    for (std::size_t i = 2; i < path.size(); ++i) {
        const auto& previous_times = graph.times(path[i - 2], path[i - 1]);
        const auto& current_times = graph.times(path[i - 1], path[i]);
        std::vector<BigInt> next(current_times.size());
        BigInt prefix = 0;
        std::size_t cursor = 0;
        for (std::size_t j = 0; j < current_times.size(); ++j) {
            while (cursor < previous_times.size() &&
                   (graph.strict ? previous_times[cursor] < current_times[j]
                                 : previous_times[cursor] <= current_times[j])) {
                prefix += counts[cursor++];
            }
            next[j] = prefix;
        }
        counts = std::move(next);
    }
    BigInt answer = 0;
    for (const BigInt& value : counts) answer += value;
    return answer;
}

} // namespace

std::vector<int> unique_forest_path(const TemporalGraph& graph) {
    require_forest(graph);
    std::vector<int> parent(graph.n, -1);
    std::queue<int> queue;
    parent[graph.s] = graph.s;
    queue.push(graph.s);
    while (!queue.empty()) {
        const int u = queue.front();
        queue.pop();
        for (int v : graph.adjacency[u]) {
            if (parent[v] != -1) continue;
            parent[v] = u;
            queue.push(v);
        }
    }
    if (parent[graph.z] == -1) return {};
    std::vector<int> path;
    for (int v = graph.z; v != graph.s; v = parent[v]) path.push_back(v);
    path.push_back(graph.s);
    std::reverse(path.begin(), path.end());
    return path;
}

BigInt forest_paper(const TemporalGraph& graph) {
    const auto path = unique_forest_path(graph);
    if (path.empty() || graph.r == 0) return 0;
    std::vector<BigInt> previous(graph.r + 1, 1), current(graph.r + 1);
    for (std::size_t i = 1; i < path.size(); ++i) {
        std::fill(current.begin(), current.end(), BigInt(0));
        const auto& labels = graph.times(path[i - 1], path[i]);
        for (int t = 1; t <= graph.r; ++t) {
            for (int label : labels) {
                if (label > t) break;
                current[t] += previous[label - (graph.strict ? 1 : 0)];
            }
        }
        previous.swap(current);
    }
    return previous[graph.r];
}

BigInt forest_dense_prefix(const TemporalGraph& graph) {
    const auto path = unique_forest_path(graph);
    if (path.empty() || graph.r == 0) return 0;
    std::vector<BigInt> previous(graph.r + 1, 1), current(graph.r + 1);
    std::vector<unsigned char> active(graph.r + 1);
    for (std::size_t i = 1; i < path.size(); ++i) {
        std::fill(active.begin(), active.end(), 0);
        for (int t : graph.times(path[i - 1], path[i])) active[t] = 1;
        current[0] = 0;
        for (int t = 1; t <= graph.r; ++t) {
            current[t] = current[t - 1];
            if (active[t]) current[t] += previous[t - (graph.strict ? 1 : 0)];
        }
        previous.swap(current);
    }
    return previous[graph.r];
}

BigInt forest_sparse(const TemporalGraph& graph) {
    const auto path = unique_forest_path(graph);
    if (path.empty()) return 0;
    return count_labels_on_path(graph, path);
}

BigInt static_path_reference(const TemporalGraph& graph) {
    std::vector<unsigned char> used(graph.n, 0);
    std::vector<int> path{graph.s};
    BigInt answer = 0;
    used[graph.s] = 1;
    std::function<void(int)> dfs = [&](int u) {
        if (u == graph.z) {
            answer += count_labels_on_path(graph, path);
            return;
        }
        for (int v : graph.adjacency[u]) {
            if (used[v]) continue;
            used[v] = 1;
            path.push_back(v);
            dfs(v);
            path.pop_back();
            used[v] = 0;
        }
    };
    dfs(graph.s);
    return answer;
}

// Independent oracle: explicitly enumerate time-edge sequences, without using
// a prefix recurrence or a decomposition. Deliberately exponential.
BigInt temporal_dfs_reference(const TemporalGraph& graph) {
    std::vector<unsigned char> used(graph.n, 0);
    BigInt answer = 0;
    used[graph.s] = 1;
    std::function<void(int, int)> visit = [&](int u, int last) {
        if (u == graph.z) { answer += 1; return; }
        for (int v : graph.adjacency[u]) {
            if (used[v]) continue;
            used[v] = 1;
            for (int t : graph.times(u, v)) {
                if (graph.strict ? last < t : last <= t) visit(v, t);
            }
            used[v] = 0;
        }
    };
    visit(graph.s, 0);
    return answer;
}

std::uint64_t bit_length(const BigInt& value) {
    return value.bit_length();
}

BigInt binomial(unsigned n, unsigned k) {
    if (k > n) return 0;
    k = std::min(k, n - k);
    BigInt result = 1;
    for (unsigned i = 1; i <= k; ++i) {
        result *= n - k + i;
        result /= i;
    }
    return result;
}

} // namespace tp
