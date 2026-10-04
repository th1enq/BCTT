#include "ttsp.hpp"

#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace tp {
namespace {

struct Node {
    enum class Type { Edge, Series, Parallel } type;
    int a{}, b{}, x{}, y{};
};
struct Decomposition {
    int root{};
    std::unordered_map<int, Node> nodes;
    std::vector<int> postorder;
    std::vector<DirectedEdge> oriented;
};

Decomposition read_and_validate(const TemporalGraph& graph, const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open TTSP decomposition: " + path);
    Decomposition tree;
    tree.root = -1;
    int declared = -1;
    bool header = false;
    std::string line;
    while (std::getline(input, line)) {
        const auto first = line.find_first_not_of(" \t\r");
        if (first == std::string::npos || line[first] == '#') continue;
        std::istringstream row(line);
        std::string token;
        row >> token;
        if (token == "sp") {
            if (header || !(row >> declared >> tree.root) || declared <= 0 || tree.root < 0)
                throw std::runtime_error("invalid or duplicate sp header");
            header = true;
        } else {
            const int id = std::stoi(token);
            if (id < 0) throw std::runtime_error("negative SP node id");
            std::string type; row >> type;
            Node node;
            if (type == "edge") {
                node.type = Node::Type::Edge;
                if (!(row >> node.a >> node.b)) throw std::runtime_error("invalid edge SP node");
            } else if (type == "series" || type == "parallel") {
                node.type = type == "series" ? Node::Type::Series : Node::Type::Parallel;
                if (!(row >> node.x >> node.y)) throw std::runtime_error("invalid internal SP node");
            } else throw std::runtime_error("unknown SP node type: " + type);
            if (!tree.nodes.emplace(id, node).second) throw std::runtime_error("duplicate SP node id");
        }
        if (row >> token) throw std::runtime_error("extra token in SP row");
    }
    if (!header || declared != static_cast<int>(tree.nodes.size()) || !tree.nodes.contains(tree.root))
        throw std::runtime_error("SP header/node count mismatch");
    std::unordered_map<int, int> parents;
    for (const auto& [id, node] : tree.nodes) {
        (void)id;
        if (node.type == Node::Type::Edge) continue;
        for (int child : {node.x, node.y}) {
            if (!tree.nodes.contains(child)) throw std::runtime_error("SP references missing child");
            ++parents[child];
        }
    }
    for (const auto& [id, node] : tree.nodes) {
        (void)node;
        if (parents[id] != (id == tree.root ? 0 : 1)) throw std::runtime_error("SP must be a rooted expression tree");
    }
    std::vector<std::pair<int, bool>> stack{{tree.root, false}};
    std::unordered_set<int> reached;
    while (!stack.empty()) {
        const auto [id, closing] = stack.back(); stack.pop_back();
        if (closing) { tree.postorder.push_back(id); continue; }
        if (!reached.insert(id).second) throw std::runtime_error("cycle in SP tree");
        stack.emplace_back(id, true);
        const auto& node = tree.nodes.at(id);
        if (node.type != Node::Type::Edge) { stack.emplace_back(node.y, false); stack.emplace_back(node.x, false); }
    }
    if (reached.size() != tree.nodes.size()) throw std::runtime_error("unreachable SP nodes");
    struct Component { int source{}, sink{}; std::unordered_set<int> vertices; };
    std::unordered_map<int, Component> components;
    std::unordered_set<std::uint64_t> used_edges;
    for (int id : tree.postorder) {
        const auto& node = tree.nodes.at(id);
        Component result;
        if (node.type == Node::Type::Edge) {
            if (!graph.has_edge(node.a, node.b)) throw std::runtime_error("SP leaf is not a static edge");
            const EdgeKey key(node.a, node.b);
            const auto packed = static_cast<std::uint64_t>(key.u) * static_cast<unsigned>(graph.n) + key.v;
            if (!used_edges.insert(packed).second) throw std::runtime_error("SP repeats a static edge leaf");
            result.source = node.a; result.sink = node.b; result.vertices = {node.a, node.b};
            tree.oriented.push_back({node.a, node.b, &graph.times(node.a, node.b)});
        } else {
            auto left = std::move(components.at(node.x));
            auto right = std::move(components.at(node.y));
            components.erase(node.x); components.erase(node.y);
            int allowed_a, allowed_b;
            if (node.type == Node::Type::Parallel) {
                if (left.source != right.source || left.sink != right.sink)
                    throw std::runtime_error("parallel SP children have different ordered poles");
                result.source = left.source; result.sink = left.sink;
                allowed_a = left.source; allowed_b = left.sink;
            } else {
                if (left.sink != right.source) throw std::runtime_error("series SP children do not meet at a pole");
                result.source = left.source; result.sink = right.sink;
                allowed_a = left.sink; allowed_b = -1;
            }
            if (result.source == result.sink) throw std::runtime_error("SP component poles must be distinct");
            if (left.vertices.size() < right.vertices.size()) left.vertices.swap(right.vertices);
            for (int v : right.vertices) {
                if (left.vertices.contains(v) && v != allowed_a && v != allowed_b)
                    throw std::runtime_error("SP children share a forbidden internal vertex");
                left.vertices.insert(v);
            }
            result.vertices = std::move(left.vertices);
        }
        components.emplace(id, std::move(result));
    }
    if (used_edges.size() != graph.labels.size()) throw std::runtime_error("SP does not cover every static edge");
    const auto& root = components.at(tree.root);
    if (root.source != graph.s || root.sink != graph.z)
        throw std::runtime_error("TTSP ordered root poles must equal query (s,z)");
    return tree;
}

} // namespace

BigInt ttsp_events(const TemporalGraph& graph, const std::string& path, DagStats* stats) {
    const auto tree = read_and_validate(graph, path);
    return count_temporal_dag(graph, tree.oriented, stats);
}

BigInt ttsp_transfer(const TemporalGraph& graph, const std::string& path, TtspStats* stats) {
    const auto tree = read_and_validate(graph, path);
    const int dim = graph.r + 1;
    using Matrix = std::vector<BigInt>;
    auto index = [dim](int a, int b) { return static_cast<std::size_t>(a) * dim + b; };
    std::unordered_map<int, Matrix> matrices;
    for (int id : tree.postorder) {
        const auto& node = tree.nodes.at(id);
        Matrix value(static_cast<std::size_t>(dim) * dim);
        if (node.type == Node::Type::Edge) {
            for (int b : graph.times(node.a, node.b))
                for (int a = 0; a <= b - (graph.strict ? 1 : 0); ++a) value[index(a, b)] = 1;
        } else {
            const auto& left = matrices.at(node.x);
            const auto& right = matrices.at(node.y);
            if (node.type == Node::Type::Parallel) {
                for (std::size_t i = 0; i < value.size(); ++i) value[i] = left[i] + right[i];
            } else {
                for (int i = 0; i < dim; ++i) {
                    for (int k = 1; k < dim; ++k) {
                        const auto& lhs = left[index(i, k)];
                        if (lhs == 0) continue;
                        for (int j = k; j < dim; ++j) {
                            const auto& rhs = right[index(k, j)];
                            if (rhs == 0) continue;
                            value[index(i, j)] += lhs * rhs;
                            if (stats) ++stats->scalar_products;
                        }
                    }
                }
            }
        }
        matrices.emplace(id, std::move(value));
    }
    BigInt answer = 0;
    const auto& result = matrices.at(tree.root);
    for (int b = 1; b < dim; ++b) answer += result[index(0, b)];
    if (stats) stats->nodes = tree.nodes.size();
    return answer;
}

} // namespace tp
