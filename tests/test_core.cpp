#include "solvers.hpp"
#include "ttsp.hpp"
#include "tw_dp.hpp"

#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

void expect(const tp::BigInt& actual, const tp::BigInt& expected, const std::string& name) {
    if (actual != expected) {
        throw std::runtime_error(name + ": expected " + expected.str() + ", got " + actual.str());
    }
}

tp::TemporalGraph parse(const std::string& text) {
    std::istringstream input(text);
    return tp::read_temporal_graph(input);
}

std::string data(const std::string& name) {
    return std::string(TPCOUNT_SOURCE_DIR) + "/tests/data/" + name;
}

} // namespace

int main() {
    try {
        const auto single = parse("p 2 3 0 1\n0 1 1\n0 1 3\n0 1 3\n");
        expect(tp::forest_paper(single), 2, "single/paper");
        expect(tp::forest_dense_prefix(single), 2, "single/dense");
        expect(tp::forest_sparse(single), 2, "single/sparse");

        const auto manual = parse("p 3 4 0 2\n0 1 1\n0 1 2\n1 2 2\n1 2 3\n");
        expect(tp::forest_paper(manual), 4, "two-edge/paper");
        expect(tp::forest_dense_prefix(manual), 4, "two-edge/dense");
        expect(tp::forest_sparse(manual), 4, "two-edge/sparse");
        expect(tp::static_path_reference(manual), 4, "two-edge/reference");
        auto strict_manual = manual; strict_manual.strict = true;
        expect(tp::forest_paper(strict_manual), 3, "strict two-edge/paper");
        expect(tp::forest_dense_prefix(strict_manual), 3, "strict two-edge/dense");
        expect(tp::forest_sparse(strict_manual), 3, "strict two-edge/sparse");
        expect(tp::temporal_dfs_reference(strict_manual), 3, "strict independent temporal DFS");

        const auto rejection = parse("p 3 2 0 2\n0 1 2\n1 2 1\n");
        expect(tp::forest_sparse(rejection), 0, "ordering rejection");
        const auto equal = parse("p 3 2 0 2\n0 1 5\n1 2 5\n");
        expect(tp::forest_sparse(equal), 1, "equal timestamps");

        std::ostringstream dense_text;
        constexpr unsigned length = 6;
        constexpr unsigned ranks = 5;
        dense_text << "p " << (length + 1) << ' ' << (length * ranks) << " 0 " << length << '\n';
        for (unsigned e = 0; e < length; ++e) {
            for (unsigned t = 1; t <= ranks; ++t) dense_text << e << ' ' << e + 1 << ' ' << t << '\n';
        }
        const auto dense = parse(dense_text.str());
        const auto closed_path = tp::binomial(ranks + length - 1, length);
        expect(tp::forest_paper(dense), closed_path, "dense closed form/paper");
        expect(tp::forest_dense_prefix(dense), closed_path, "dense closed form/dense");
        expect(tp::forest_sparse(dense), closed_path, "dense closed form/sparse");

        const auto diamond = tp::read_temporal_graph_file(data("diamond.tg"));
        const auto diamond_expected = 2 * tp::binomial(4, 2);
        expect(tp::ttsp_transfer(diamond, data("diamond.sp")), diamond_expected, "diamond transfer");
        expect(tp::ttsp_events(diamond, data("diamond.sp")), diamond_expected, "diamond events");
        expect(tp::cactus_count(diamond), diamond_expected, "diamond cactus");
        expect(tp::treewidth_dp(diamond, data("diamond.ntd")), diamond_expected, "diamond join tw-dp");
        expect(tp::static_path_reference(diamond), diamond_expected, "diamond reference");
        auto strict_diamond = diamond; strict_diamond.strict = true;
        expect(tp::ttsp_transfer(strict_diamond, data("diamond.sp")), 6, "strict diamond transfer");
        expect(tp::ttsp_events(strict_diamond, data("diamond.sp")), 6, "strict diamond events");
        expect(tp::cactus_count(strict_diamond), 6, "strict diamond cactus");
        expect(tp::treewidth_dp(strict_diamond, data("diamond.ntd")), 6, "strict diamond treewidth");
        expect(tp::treewidth_dp(diamond, data("diamond.ntd"), nullptr, {false, false, false}), diamond_expected, "unpruned join baseline");

        const auto triangle = tp::read_temporal_graph_file(data("triangle.tg"));
        expect(tp::treewidth_dp(triangle, data("triangle.ntd")), 2, "triangle tw-dp");
        expect(tp::static_path_reference(triangle), 2, "triangle reference");
        expect(tp::cactus_count(triangle), 2, "triangle cactus");
        auto strict_triangle = triangle; strict_triangle.strict = true;
        expect(tp::treewidth_dp(strict_triangle, data("triangle.ntd")), 1, "strict triangle treewidth");
        expect(tp::cactus_count(strict_triangle), 1, "strict triangle cactus");
        // A triangle with a pendant branch: entering that branch cannot belong
        // to a simple path whose two terminals are in the triangle.
        auto pendant = parse("p 4 4 0 2\n0 1 1\n1 2 1\n0 2 1\n1 3 1\n");
        expect(tp::cactus_count(pendant), 2, "cactus excludes off-route blocks");
        const auto disconnected = parse("p 3 1 0 2\n0 1 1\n");
        expect(tp::cactus_count(disconnected), 0, "disconnected cactus");
        bool rejected = false;
        try { tp::cactus_count(parse("p 4 5 0 3\n0 1 1\n0 2 1\n1 2 1\n1 3 1\n2 3 1\n")); }
        catch (const std::runtime_error&) { rejected = true; }
        if (!rejected) throw std::runtime_error("cactus accepted a non-cactus graph");
        auto overlap = tp::read_temporal_graph_file(data("invalid-overlap.tg"));
        for (bool events : {false, true}) {
            rejected = false;
            try { if (events) tp::ttsp_events(overlap, data("invalid-overlap.sp"));
                  else tp::ttsp_transfer(overlap, data("invalid-overlap.sp")); }
            catch (const std::runtime_error&) { rejected = true; }
            if (!rejected) throw std::runtime_error("TTSP accepted intersecting branch interiors");
        }

        // Limb carry and multiplication identities at >64-bit precision.
        auto big = tp::binomial(200, 100);
        expect(big, tp::binomial(199, 99) + tp::binomial(199, 100), "BigInt Pascal identity");
        tp::BigInt power = 1;
        for (int i = 0; i < 128; ++i) power *= 2;
        if (power.str() != "340282366920938463463374607431768211456") throw std::runtime_error("BigInt power/decimal mismatch");
        expect(power * power, [&] { auto p = power; for (int i = 0; i < 128; ++i) p *= 2; return p; }(), "BigInt limb multiplication");

        std::cout << "all core tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "test failure: " << error.what() << '\n';
        return 1;
    }
}
