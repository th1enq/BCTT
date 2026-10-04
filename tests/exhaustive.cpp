#include "dag.hpp"
#include "tw_dp.hpp"

#include <chrono>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace {

std::string decomposition(const tp::TemporalGraph& g) {
    std::vector<std::string> rows;
    std::vector<int> bag;
    for (int v = 0; v < g.n; ++v) bag.push_back(v);
    auto add = [&](const std::string& action) {
        std::ostringstream row;
        row << rows.size() << ' ' << action << ' ' << bag.size();
        for (int v : bag) row << ' ' << v;
        rows.push_back(row.str());
    };
    add("leaf");
    for (const auto& [edge, labels] : g.labels) {
        (void)labels;
        add("introduce-e " + std::to_string(rows.size() - 1) + " " + std::to_string(edge.u) + " " + std::to_string(edge.v));
    }
    for (int v = 0; v < g.n; ++v) if (v != g.s && v != g.z) {
        bag.erase(std::find(bag.begin(), bag.end(), v));
        add("forget-v " + std::to_string(rows.size() - 1) + " " + std::to_string(v));
    }
    std::ostringstream out;
    out << "ntd " << rows.size() << ' ' << rows.size() - 1 << ' ' << g.n - 1 << '\n';
    for (const auto& row : rows) out << row << '\n';
    return out.str();
}

bool is_cactus(const tp::TemporalGraph& g) {
    // Independent small-graph characterization: no edge belongs to two simple
    // cycles. Enumerate each cycle once (smallest vertex, fixed orientation).
    std::map<tp::EdgeKey, int> cycles;
    bool valid = true;
    std::vector<int> path;
    std::vector<bool> used(g.n, false);
    for (int source = 0; source < g.n && valid; ++source) {
        path = {source}; used[source] = true;
        std::function<void(int)> visit = [&](int u) {
            for (int v : g.adjacency[u]) {
                if (v == source && path.size() >= 3 && path[1] < path.back()) {
                    for (std::size_t i = 1; i < path.size(); ++i) if (++cycles[tp::EdgeKey(path[i - 1], path[i])] > 1) valid = false;
                    if (++cycles[tp::EdgeKey(u, source)] > 1) valid = false;
                } else if (v > source && !used[v]) {
                    used[v] = true; path.push_back(v); visit(v); path.pop_back(); used[v] = false;
                }
            }
        };
        visit(source); used[source] = false;
    }
    return valid;
}

void expect(const tp::BigInt& a, const tp::BigInt& b, const std::string& context) {
    if (a != b) throw std::runtime_error(context + ": " + a.str() + " != " + b.str());
}

struct Summary { std::uint64_t graphs{}, queries{}, comparisons{}, cactus_queries{}; };

Summary campaign(int n, int ranks) {
    Summary result;
    std::vector<tp::EdgeKey> pairs;
    for (int u = 0; u < n; ++u) for (int v = u + 1; v < n; ++v) pairs.emplace_back(u, v);
    const int base = ranks == 1 ? 2 : 4;
    std::uint64_t assignments = 1;
    for (std::size_t i = 0; i < pairs.size(); ++i) assignments *= base;
    for (std::uint64_t code = 0; code < assignments; ++code) {
        tp::TemporalGraph g; g.n = n; g.r = ranks; g.adjacency.resize(n);
        auto remaining = code;
        for (const auto& edge : pairs) {
            const int mask = static_cast<int>(remaining % base); remaining /= base;
            if (!mask) continue;
            for (int t = 1; t <= ranks; ++t) if (mask & (1 << (t - 1))) g.labels[edge].push_back(t);
            g.adjacency[edge.u].push_back(edge.v); g.adjacency[edge.v].push_back(edge.u);
        }
        const bool cactus = is_cactus(g);
        ++result.graphs;
        for (g.s = 0; g.s < n; ++g.s) for (g.z = 0; g.z < n; ++g.z) {
            if (g.s == g.z) continue;
            const auto text = decomposition(g);
            for (bool strict : {false, true}) {
                g.strict = strict;
                const auto oracle = tp::temporal_dfs_reference(g);
                std::istringstream optimized(text), baseline(text);
                const std::string identity = "n=" + std::to_string(n) + ",r=" + std::to_string(ranks) + ",code=" + std::to_string(code) + ",s=" + std::to_string(g.s) + ",z=" + std::to_string(g.z) + ",strict=" + std::to_string(strict);
                expect(tp::treewidth_dp_stream(g, optimized), oracle, identity + "/tw");
                expect(tp::treewidth_dp_stream(g, baseline, nullptr, {false, false, false}), oracle, identity + "/baseline");
                expect(tp::static_path_reference(g), oracle, identity + "/static-ref");
                result.comparisons += 3; ++result.queries;
                if (cactus) { expect(tp::cactus_count(g), oracle, identity + "/cactus"); ++result.comparisons; ++result.cactus_queries; }
            }
        }
    }
    return result;
}

} // namespace

int main() {
    try {
        const auto start = std::chrono::steady_clock::now();
        std::cout << "{\"campaigns\":[";
        bool first = true;
        std::uint64_t total = 0;
        for (const auto [n, ranks] : std::vector<std::pair<int, int>>{{2, 2}, {3, 2}, {4, 2}, {5, 1}}) {
            const auto s = campaign(n, ranks); total += s.comparisons;
            if (!first) std::cout << ',';
            first = false;
            std::cout << "{\"n\":" << n << ",\"r\":" << ranks << ",\"graphs\":" << s.graphs
                      << ",\"queries_both_modes\":" << s.queries << ",\"comparisons\":" << s.comparisons
                      << ",\"cactus_queries\":" << s.cactus_queries << '}';
            std::cerr << "completed exhaustive n=" << n << " r=" << ranks << " queries=" << s.queries << '\n';
        }
        const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        std::cout << "],\"comparisons\":" << total << ",\"mismatches\":0,\"wall_seconds\":" << seconds << "}\n";
    } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}
