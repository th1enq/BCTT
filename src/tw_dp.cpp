#include "tw_dp.hpp"

#include <algorithm>
#include <fstream>
#include <functional>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

namespace tp {

namespace {

struct State {
  std::vector<int> status;
  std::vector<int>
      part; // -1 for ZERO, otherwise canonical restricted-growth labels
  bool operator==(const State &) const = default;
};

struct StateHash {
  std::size_t operator()(const State &state) const noexcept {
    std::size_t h = 1469598103934665603ULL;
    for (int x : state.status)
      h = (h ^ static_cast<std::size_t>(x + 3)) * 1099511628211ULL;
    h ^= 0x9e3779b97f4a7c15ULL;
    for (int x : state.part)
      h = (h ^ static_cast<std::size_t>(x + 3)) * 1099511628211ULL;
    return h;
  }
};

using Table = std::unordered_map<State, BigInt, StateHash>;

struct Node {
  enum class Type {
    Leaf,
    IntroduceVertex,
    IntroduceEdge,
    ForgetVertex,
    Join
  } type;
  int child{-1};
  int right{-1};
  int u{-1};
  int v{-1};
  std::vector<int> bag;
};

struct Dsu {
  std::vector<int> parent;
  explicit Dsu(int n) : parent(n) {
    std::iota(parent.begin(), parent.end(), 0);
  }
  int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
  bool unite(int a, int b) {
    a = find(a);
    b = find(b);
    if (a == b)
      return false;
    parent[b] = a;
    return true;
  }
};

void canonicalize(State &state) {
  std::vector<int> remap(state.part.size() + 1, -1);
  int next = 0;
  for (std::size_t i = 0; i < state.part.size(); ++i) {
    if (state.status[i] == 0) {
      state.part[i] = -1;
      continue;
    }
    const int old = state.part[i];
    if (remap[old] < 0)
      remap[old] = next++;
    state.part[i] = remap[old];
  }
}

int position(const std::vector<int> &bag, int vertex) {
  const auto it = std::find(bag.begin(), bag.end(), vertex);
  return it == bag.end() ? -1 : static_cast<int>(it - bag.begin());
}

void validate_state(const State &state) {
  if (state.status.size() != state.part.size())
    throw std::runtime_error("internal malformed DP state");
  for (std::size_t i = 0; i < state.status.size(); ++i) {
    if ((state.status[i] == 0) != (state.part[i] == -1)) {
      throw std::runtime_error("internal status/partition disagreement");
    }
  }
}

int add_outgoing(int status, int t, int r, bool strict) {
  const int both = 2 * r + 1;
  if (status == 0)
    return r + t;
  if (status >= 1 && status <= r && (strict ? status < t : status <= t))
    return both;
  return -1;
}

int add_incoming(int status, int t, int r, bool strict) {
  const int both = 2 * r + 1;
  if (status == 0)
    return t;
  if (status > r && status <= 2 * r &&
      (strict ? t < status - r : t <= status - r))
    return both;
  return -1;
}

int join_status(int a, int b, int r, bool strict) {
  const int both = 2 * r + 1;
  if (a == 0)
    return b;
  if (b == 0)
    return a;
  if (a == both || b == both)
    return -1;
  const bool a_in = a <= r;
  const bool b_in = b <= r;
  if (a_in == b_in)
    return -1;
  const int incoming = a_in ? a : b;
  const int outgoing = a_in ? b - r : a - r;
  return (strict ? incoming < outgoing : incoming <= outgoing) ? both : -1;
}

void add_to(Table &table, State state, const BigInt &count) {
  canonicalize(state);
  table[std::move(state)] += count;
}

State remap_state(const State &source, const std::vector<int> &source_bag,
                  const std::vector<int> &target_bag) {
  State target;
  target.status.assign(target_bag.size(), 0);
  target.part.assign(target_bag.size(), -1);
  for (std::size_t i = 0; i < target_bag.size(); ++i) {
    const int j = position(source_bag, target_bag[i]);
    if (j >= 0) {
      target.status[i] = source.status[j];
      target.part[i] = source.part[j];
    }
  }
  canonicalize(target);
  return target;
}

} // namespace

BigInt treewidth_dp(const TemporalGraph &graph, const std::string &path,
                    TwStats *output_stats, TwOptions options) {
  std::ifstream input(path);
  if (!input)
    throw std::runtime_error("cannot open nice tree decomposition: " + path);
  return treewidth_dp_stream(graph, input, output_stats, options);
}

BigInt treewidth_dp_stream(const TemporalGraph &graph, std::istream &input,
                           TwStats *output_stats, TwOptions options) {
  int declared_nodes = -1;
  int root = -1;
  int width = -1;
  std::unordered_map<int, Node> nodes;
  std::map<EdgeKey, int> introduced_edges;
  std::string line;
  while (std::getline(input, line)) {
    const auto first = line.find_first_not_of(" \t\r");
    if (first == std::string::npos || line[first] == '#')
      continue;
    std::istringstream row(line);
    std::string first_token;
    row >> first_token;
    if (first_token == "ntd") {
      if (declared_nodes >= 0 || !(row >> declared_nodes >> root >> width) ||
          width < 0)
        throw std::runtime_error("invalid or duplicate ntd header");
      if (row >> first_token)
        throw std::runtime_error("extra token in ntd header");
      continue;
    }
    const int id = std::stoi(first_token);
    if (id < 0)
      throw std::runtime_error("negative ntd node id");
    std::string type;
    row >> type;
    Node node;
    int bag_size = -1;
    if (type == "leaf") {
      node.type = Node::Type::Leaf;
      row >> bag_size;
    } else if (type == "introduce-v") {
      node.type = Node::Type::IntroduceVertex;
      row >> node.child >> node.v >> bag_size;
    } else if (type == "introduce-e") {
      node.type = Node::Type::IntroduceEdge;
      row >> node.child >> node.u >> node.v >> bag_size;
      ++introduced_edges[EdgeKey(node.u, node.v)];
    } else if (type == "forget-v") {
      node.type = Node::Type::ForgetVertex;
      row >> node.child >> node.v >> bag_size;
    } else if (type == "join") {
      node.type = Node::Type::Join;
      row >> node.child >> node.right >> bag_size;
    } else {
      throw std::runtime_error("unknown ntd node type: " + type);
    }
    if (!row || bag_size < 0)
      throw std::runtime_error("malformed ntd node");
    node.bag.resize(bag_size);
    for (int &v : node.bag)
      if (!(row >> v))
        throw std::runtime_error("short ntd bag");
    if (row >> first_token)
      throw std::runtime_error("extra token in ntd row");
    std::sort(node.bag.begin(), node.bag.end());
    if (std::adjacent_find(node.bag.begin(), node.bag.end()) !=
        node.bag.end()) {
      throw std::runtime_error("duplicate vertex in ntd bag");
    }
    for (int v : node.bag)
      if (v < 0 || v >= graph.n)
        throw std::runtime_error("ntd vertex out of range");
    if (!nodes.emplace(id, std::move(node)).second)
      throw std::runtime_error("duplicate ntd node id");
  }
  if (root < 0 || declared_nodes != static_cast<int>(nodes.size()) ||
      !nodes.contains(root)) {
    throw std::runtime_error("ntd header/node count mismatch");
  }
  if (introduced_edges.size() != graph.labels.size()) {
    throw std::runtime_error(
        "ntd must introduce every static edge exactly once");
  }
  for (const auto &[edge, labels] : graph.labels) {
    (void)labels;
    if (introduced_edges[edge] != 1)
      throw std::runtime_error("ntd static edge introduction count is not one");
  }
  std::unordered_map<int, int> parent_count;
  std::vector<int> occurrences(graph.n, 0), common_edges(graph.n, 0);
  for (const auto &[id, node] : nodes) {
    (void)id;
    if (position(node.bag, graph.s) < 0 || position(node.bag, graph.z) < 0) {
      throw std::runtime_error(
          "s and z must occur in every normalized ntd bag");
    }
    if (node.bag.size() > static_cast<std::size_t>(width + 3))
      throw std::runtime_error("normalized bag exceeds width+3");
    for (int v : node.bag)
      ++occurrences[v];
    if (node.type != Node::Type::Leaf)
      ++parent_count[node.child];
    if (node.type == Node::Type::Join)
      ++parent_count[node.right];
    for (int child : {node.child, node.right}) {
      if (child < 0)
        continue;
      if (!nodes.contains(child))
        throw std::runtime_error("ntd references missing child");
      for (int v : node.bag)
        if (position(nodes.at(child).bag, v) >= 0)
          ++common_edges[v];
    }
  }
  for (int v = 0; v < graph.n; ++v) {
    if (occurrences[v] && common_edges[v] != occurrences[v] - 1)
      throw std::runtime_error("ntd violates running intersection");
  }
  for (const auto &[id, node] : nodes) {
    (void)node;
    const int expected = id == root ? 0 : 1;
    if (parent_count[id] != expected)
      throw std::runtime_error("ntd nodes must form a rooted tree");
  }

  TwStats local_stats;
  local_stats.width_input = width;
  std::unordered_map<int, Table> memo;
  std::unordered_set<int> visiting;
  std::size_t evaluated_nodes = 0;
  std::uint64_t live_states = 0;
  std::function<const Table &(int)> evaluate = [&](int id) -> const Table & {
    if (const auto it = memo.find(id); it != memo.end())
      return it->second;
    const auto node_it = nodes.find(id);
    if (node_it == nodes.end())
      throw std::runtime_error("ntd references missing child");
    if (!visiting.insert(id).second)
      throw std::runtime_error("cycle in ntd");
    const Node &node = node_it->second;
    Table table;
    if (node.type == Node::Type::Leaf) {
      State initial;
      initial.status.assign(node.bag.size(), 0);
      initial.part.assign(node.bag.size(), -1);
      table.emplace(std::move(initial), BigInt(1));
    } else if (node.type == Node::Type::IntroduceVertex) {
      const Node &child_node = nodes.at(node.child);
      if (position(node.bag, node.v) < 0 ||
          position(child_node.bag, node.v) >= 0 ||
          node.bag.size() != child_node.bag.size() + 1 ||
          !std::includes(node.bag.begin(), node.bag.end(),
                         child_node.bag.begin(), child_node.bag.end())) {
        throw std::runtime_error("invalid introduce-v bags");
      }
      const Table &child = evaluate(node.child);
      for (const auto &[state, count] : child)
        add_to(table, remap_state(state, child_node.bag, node.bag), count);
    } else if (node.type == Node::Type::ForgetVertex) {
      const Node &child_node = nodes.at(node.child);
      const int forgotten = position(child_node.bag, node.v);
      if (forgotten < 0 || position(node.bag, node.v) >= 0 ||
          child_node.bag.size() != node.bag.size() + 1 ||
          !std::includes(child_node.bag.begin(), child_node.bag.end(),
                         node.bag.begin(), node.bag.end())) {
        throw std::runtime_error("invalid forget-v bags");
      }
      const Table &child = evaluate(node.child);
      for (const auto &[state, count] : child) {
        const int status = state.status[forgotten];
        if (status != 0 && status != 2 * graph.r + 1)
          continue;
        if (status != 0) {
          int block_size = 0;
          for (int p : state.part)
            if (p == state.part[forgotten])
              ++block_size;
          if (block_size == 1)
            continue;
        }
        add_to(table, remap_state(state, child_node.bag, node.bag), count);
      }
    } else if (node.type == Node::Type::IntroduceEdge) {
      const Node &child_node = nodes.at(node.child);
      if (node.bag != child_node.bag || position(node.bag, node.u) < 0 ||
          position(node.bag, node.v) < 0 || !graph.has_edge(node.u, node.v))
        throw std::runtime_error("invalid introduce-e node");
      const Table &child = evaluate(node.child);
      const int pu = position(node.bag, node.u);
      const int pv = position(node.bag, node.v);
      for (const auto &[state, count] : child) {
        add_to(table, state, count); // skip
        for (int t : graph.times(node.u, node.v)) {
          for (int direction = 0; direction < 2; ++direction) {
            const int from = direction == 0 ? pu : pv;
            const int to = direction == 0 ? pv : pu;
            if (options.prune_terminals &&
                (node.bag[from] == graph.z || node.bag[to] == graph.s))
              continue;
            const int out =
                add_outgoing(state.status[from], t, graph.r, graph.strict);
            const int in =
                add_incoming(state.status[to], t, graph.r, graph.strict);
            if (out < 0 || in < 0)
              continue;
            if (state.status[from] != 0 && state.status[to] != 0 &&
                state.part[from] == state.part[to])
              continue;
            State next = state;
            // Endpoint labels have no local predecessor/successor
            // constraint. With terminal pruning they can be erased.
            const bool compact =
                options.prune_terminals && options.compact_terminals;
            next.status[from] =
                compact && node.bag[from] == graph.s ? graph.r + 1 : out;
            next.status[to] = compact && node.bag[to] == graph.z ? 1 : in;
            int new_block = 0;
            for (int p : next.part)
              new_block = std::max(new_block, p + 1);
            if (state.status[from] == 0 && state.status[to] == 0) {
              next.part[from] = next.part[to] = new_block;
            } else if (state.status[from] == 0) {
              next.part[from] = next.part[to];
            } else if (state.status[to] == 0) {
              next.part[to] = next.part[from];
            } else {
              const int keep = next.part[from];
              const int replace = next.part[to];
              for (int &p : next.part)
                if (p == replace)
                  p = keep;
            }
            add_to(table, std::move(next), count);
          }
        }
      }
    } else {
      const Node &left_node = nodes.at(node.child);
      const Node &right_node = nodes.at(node.right);
      if (node.bag != left_node.bag || node.bag != right_node.bag)
        throw std::runtime_error("join bags must be identical");
      const Table &left = evaluate(node.child);
      const Table &right = evaluate(node.right);
      local_stats.join_pairs_possible +=
          static_cast<std::uint64_t>(left.size()) * right.size();
      using Entry = Table::value_type;
      std::map<std::vector<int>, std::vector<const Entry *>> buckets;
      auto shape = [&](const State &state) {
        std::vector<int> result;
        for (int status : state.status)
          result.push_back(status == 0             ? 0
                           : status <= graph.r     ? 1
                           : status <= 2 * graph.r ? 2
                                                   : 3);
        return result;
      };
      if (options.index_joins) {
        for (const auto &entry : right)
          buckets[shape(entry.first)].push_back(&entry);
      } else {
        for (const auto &entry : right)
          buckets[{}].push_back(&entry);
      }
      for (const auto &[a, count_a] : left) {
        const auto a_shape = shape(a);
        for (const auto &[b_shape, entries] : buckets) {
          bool coarse_valid = true;
          if (options.index_joins)
            for (std::size_t i = 0; i < a_shape.size(); ++i) {
              if (a_shape[i] && b_shape[i] && a_shape[i] + b_shape[i] != 3) {
                coarse_valid = false;
                break;
              }
            }
          if (!coarse_valid)
            continue;
          for (const auto *entry : entries) {
            const auto &[b, count_b] = *entry;
            ++local_stats.join_pairs_tested;
            State merged;
            merged.status.resize(node.bag.size());
            merged.part.assign(node.bag.size(), -1);
            bool valid = true;
            for (std::size_t i = 0; i < node.bag.size(); ++i) {
              merged.status[i] =
                  join_status(a.status[i], b.status[i], graph.r, graph.strict);
              if (merged.status[i] < 0) {
                valid = false;
                break;
              }
            }
            if (!valid)
              continue;
            ++local_stats.join_pairs_compatible;

            int left_blocks = 0, right_blocks = 0;
            for (int p : a.part)
              left_blocks = std::max(left_blocks, p + 1);
            for (int p : b.part)
              right_blocks = std::max(right_blocks, p + 1);
            Dsu incidence(left_blocks + right_blocks);
            for (std::size_t i = 0; i < node.bag.size(); ++i) {
              if (a.status[i] == 0 || b.status[i] == 0)
                continue;
              if (!incidence.unite(a.part[i], left_blocks + b.part[i])) {
                valid = false;
                break;
              }
            }
            if (!valid)
              continue;

            Dsu connectivity(static_cast<int>(node.bag.size()));
            for (std::size_t i = 0; i < node.bag.size(); ++i) {
              if (merged.status[i] == 0)
                continue;
              for (std::size_t j = i + 1; j < node.bag.size(); ++j) {
                if ((a.status[i] != 0 && a.status[j] != 0 &&
                     a.part[i] == a.part[j]) ||
                    (b.status[i] != 0 && b.status[j] != 0 &&
                     b.part[i] == b.part[j])) {
                  connectivity.unite(static_cast<int>(i), static_cast<int>(j));
                }
              }
            }
            for (std::size_t i = 0; i < node.bag.size(); ++i) {
              if (merged.status[i] != 0)
                merged.part[i] = connectivity.find(static_cast<int>(i));
            }
            add_to(table, std::move(merged), count_a * count_b);
          }
        }
      }
    }
    visiting.erase(id);
    local_stats.states_created += table.size();
    local_stats.states_peak_bag =
        std::max<std::uint64_t>(local_stats.states_peak_bag, table.size());
    live_states += table.size();
    local_stats.states_peak_live =
        std::max(local_stats.states_peak_live, live_states);
    ++evaluated_nodes;
    if (options.release_tables)
      for (int child : {node.child, node.right}) {
        if (child < 0)
          continue;
        live_states -= memo.at(child).size();
        memo.erase(child);
      }
    return memo.emplace(id, std::move(table)).first->second;
  };

  const Table &root_table = evaluate(root);
  if (evaluated_nodes != nodes.size())
    throw std::runtime_error("ntd contains unreachable nodes");
  const Node &root_node = nodes.at(root);
  if (root_node.bag.size() != 2 || position(root_node.bag, graph.s) < 0 ||
      position(root_node.bag, graph.z) < 0) {
    throw std::runtime_error("ntd root bag must contain exactly s and z");
  }
  const int ps = position(root_node.bag, graph.s);
  const int pz = position(root_node.bag, graph.z);
  BigInt answer = 0;
  for (const auto &[state, count] : root_table) {
    validate_state(state);
    const bool s_out =
        state.status[ps] > graph.r && state.status[ps] <= 2 * graph.r;
    const bool z_in = state.status[pz] >= 1 && state.status[pz] <= graph.r;
    if (s_out && z_in && state.part[ps] == state.part[pz])
      answer += count;
  }
  if (output_stats)
    *output_stats = local_stats;
  return answer;
}

} // namespace tp
