#include "solvers.hpp"
#include "ttsp.hpp"
#include "tw_dp.hpp"

#include <chrono>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/resource.h>

namespace {

double peak_rss_mb() {
    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) != 0) return 0.0;
#if defined(__APPLE__)
    return static_cast<double>(usage.ru_maxrss) / (1024.0 * 1024.0);
#else
    return static_cast<double>(usage.ru_maxrss) / 1024.0;
#endif
}

std::string option(int argc, char** argv, const std::string& name) {
    for (int i = 1; i + 1 < argc; ++i) if (argv[i] == name) return argv[i + 1];
    return {};
}

std::string positional_instance(int argc, char** argv) {
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--solver" || arg == "--decomp" || arg == "--td" || arg == "--reference" ||
            arg == "--repeat" || arg == "--tw-mode") {
            ++i;
            continue;
        }
        if (!arg.starts_with("--")) return arg;
    }
    return {};
}

void usage() {
    std::cerr << "Usage:\n"
              << "  tpcount info INSTANCE.tg\n"
              << "  tpcount count --solver NAME INSTANCE.tg [--decomp FILE.sp | --td FILE.ntd]\n"
              << "  tpcount verify --solver NAME INSTANCE.tg [--decomp FILE.sp | --td FILE.ntd]\n"
              << "  tpcount batch  (stdin: SOLVER TG AUX STRICT, one request per line)\n"
              << "Options: --strict, --repeat N, --tw-mode baseline|no-index|no-prune|no-release|no-compact\n"
              << "Solvers: forest-paper, forest-dense, forest-sparse, ttsp-transfer, ttsp-events,\n"
              << "         cactus, tw-dp, tw-dp-baseline, brute, brute-cartesian\n";
}

tp::BigInt solve(const tp::TemporalGraph& graph, const std::string& solver,
                 const std::string& auxiliary, tp::TwStats& tw_stats,
                 tp::TtspStats& ttsp_stats, tp::DagStats& dag_stats,
                 tp::TwOptions tw_options = {}) {
    if (solver == "forest-paper") return tp::forest_paper(graph);
    if (solver == "forest-dense") return tp::forest_dense_prefix(graph);
    if (solver == "forest-sparse") return tp::forest_sparse(graph);
    if (solver == "brute") return tp::static_path_reference(graph);
    if (solver == "brute-cartesian") return tp::temporal_dfs_reference(graph);
    if (solver == "cactus") return tp::cactus_count(graph, &dag_stats);
    if (solver == "ttsp-transfer" || solver == "ttsp-events") {
        if (auxiliary.empty()) throw std::runtime_error("TTSP solver requires --decomp");
        return solver == "ttsp-transfer" ? tp::ttsp_transfer(graph, auxiliary, &ttsp_stats)
                                          : tp::ttsp_events(graph, auxiliary, &dag_stats);
    }
    if (solver == "tw-dp" || solver == "tw-dp-baseline") {
        if (auxiliary.empty()) throw std::runtime_error("treewidth solver requires --td");
        if (solver == "tw-dp-baseline") tw_options = {false, false, false};
        return tp::treewidth_dp(graph, auxiliary, &tw_stats, tw_options);
    }
    throw std::runtime_error("unknown solver: " + solver);
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc >= 2 && std::string(argv[1]) == "batch") {
            std::string line;
            while (std::getline(std::cin, line)) {
                std::istringstream row(line);
                std::string solver, instance, auxiliary;
                int strict = 0;
                if (!(row >> solver >> instance >> auxiliary >> strict)) throw std::runtime_error("malformed batch request");
                auto graph = tp::read_temporal_graph_file(instance);
                graph.strict = strict != 0;
                tp::TwStats tw; tp::TtspStats sp; tp::DagStats dag;
                const auto count = solve(graph, solver, auxiliary == "-" ? "" : auxiliary, tw, sp, dag);
                std::cout << "{\"count\":\"" << count << "\"}\n";
            }
            return 0;
        }
        if (argc < 3) { usage(); return 2; }
        const std::string command = argv[1];
        const std::string instance = positional_instance(argc, argv);
        if (instance.empty()) throw std::runtime_error("missing instance path");
        const auto parse_start = std::chrono::steady_clock::now();
        tp::TemporalGraph graph = tp::read_temporal_graph_file(instance);
        const double parse_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - parse_start).count();
        for (int i = 2; i < argc; ++i) if (std::string(argv[i]) == "--strict") graph.strict = true;
        if (command == "info") {
            std::cout << "{\"n\":" << graph.n
                      << ",\"m_static\":" << graph.labels.size()
                      << ",\"m_temporal\":" << graph.temporal_edges()
                      << ",\"time_ranks\":" << graph.r
                      << ",\"s\":" << graph.s << ",\"z\":" << graph.z << "}\n";
            return 0;
        }
        if (command != "count" && command != "verify") throw std::runtime_error("unknown command: " + command);
        const std::string solver = option(argc, argv, "--solver");
        if (solver.empty()) throw std::runtime_error("missing --solver");
        tp::TwStats tw_stats;
        tp::TtspStats ttsp_stats;
        tp::DagStats dag_stats;
        tp::TwOptions tw_options;
        const std::string mode = option(argc, argv, "--tw-mode");
        if (mode == "baseline") tw_options = {false, false, false};
        else if (mode == "no-index") tw_options.index_joins = false;
        else if (mode == "no-prune") tw_options.prune_terminals = false;
        else if (mode == "no-release") tw_options.release_tables = false;
        else if (mode == "no-compact") tw_options.compact_terminals = false;
        else if (!mode.empty()) throw std::runtime_error("unknown --tw-mode");
        const std::string repeat_text = option(argc, argv, "--repeat");
        const int repeats = repeat_text.empty() ? 1 : std::stoi(repeat_text);
        if (repeats < 1 || repeats > 100000) throw std::runtime_error("--repeat must be in 1..100000");
        const auto auxiliary = solver.starts_with("ttsp") ? option(argc, argv, "--decomp") : option(argc, argv, "--td");
        const auto cpu_start = std::clock();
        const auto start = std::chrono::steady_clock::now();
        tp::BigInt answer;
        for (int iteration = 0; iteration < repeats; ++iteration) {
            tw_stats = {}; ttsp_stats = {}; dag_stats = {};
            const auto next = solve(graph, solver, auxiliary, tw_stats, ttsp_stats, dag_stats, tw_options);
            if (iteration && answer != next) throw std::runtime_error("non-deterministic repeated count");
            answer = next;
        }
        const auto stop = std::chrono::steady_clock::now();
        const double wall_ms = std::chrono::duration<double, std::milli>(stop - start).count() / repeats;
        const double cpu_ms = 1000.0 * (std::clock() - cpu_start) / CLOCKS_PER_SEC / repeats;

        bool verified = true;
        if (command == "verify") {
            const tp::BigInt reference = option(argc, argv, "--reference") == "cartesian"
                ? tp::temporal_dfs_reference(graph) : tp::static_path_reference(graph);
            verified = (answer == reference);
        }
        std::cout << "{\"solver\":\"" << solver << "\",\"count\":\"" << answer
                  << "\",\"count_bits\":" << tp::bit_length(answer)
                  << ",\"wall_ms\":" << wall_ms
                  << ",\"cpu_ms\":" << cpu_ms
                  << ",\"parse_ms\":" << parse_ms
                  << ",\"batch_repeats\":" << repeats
                  << ",\"strict\":" << (graph.strict ? "true" : "false")
                  << ",\"peak_rss_mb\":" << peak_rss_mb()
                  << ",\"n\":" << graph.n
                  << ",\"m_static\":" << graph.labels.size()
                  << ",\"m_temporal\":" << graph.temporal_edges()
                  << ",\"time_ranks\":" << graph.r
                  << ",\"s\":" << graph.s << ",\"z\":" << graph.z
                  << ",\"treewidth_input\":" << tw_stats.width_input
                  << ",\"states_created\":" << tw_stats.states_created
                  << ",\"states_peak_bag\":" << tw_stats.states_peak_bag
                  << ",\"join_pairs_tested\":" << tw_stats.join_pairs_tested
                  << ",\"join_pairs_possible\":" << tw_stats.join_pairs_possible
                  << ",\"join_pairs_compatible\":" << tw_stats.join_pairs_compatible
                  << ",\"states_peak_live\":" << tw_stats.states_peak_live
                  << ",\"temporal_events\":" << dag_stats.temporal_events
                  << ",\"dag_additions\":" << dag_stats.additions
                  << ",\"ttsp_nodes\":" << ttsp_stats.nodes
                  << ",\"ttsp_scalar_products\":" << ttsp_stats.scalar_products;
        if (command == "verify") std::cout << ",\"verified\":" << (verified ? "true" : "false");
        std::cout << "}\n";
        return verified ? 0 : 3;
    } catch (const std::exception& error) {
        std::cerr << "tpcount: " << error.what() << '\n';
        return 1;
    }
}
