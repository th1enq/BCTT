#!/usr/bin/env python3
"""Deterministic instance and decomposition generators for tpcount."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import random
from typing import Iterable

MASTER_SEED = 20260928


def derived_seed(family: str, grid_cell: str, replicate: int) -> int:
    payload = f"{MASTER_SEED}:{family}:{grid_cell}:{replicate}".encode()
    return int.from_bytes(sha256(payload).digest()[:8], "big")


def edge(u: int, v: int) -> tuple[int, int]:
    if u == v:
        raise ValueError("self-loop")
    return (u, v) if u < v else (v, u)


def write_temporal_graph(
    path: Path,
    n: int,
    static_edges: Iterable[tuple[int, int]],
    labels: dict[tuple[int, int], list[int]],
    s: int,
    z: int,
) -> None:
    rows: list[tuple[int, int, int]] = []
    for u, v in sorted({edge(*e) for e in static_edges}):
        for t in sorted(set(labels[(u, v)])):
            rows.append((u, v, t))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        out.write(f"p {n} {len(rows)} {s} {z}\n")
        for u, v, t in rows:
            out.write(f"{u} {v} {t}\n")


def all_labels(edges: Iterable[tuple[int, int]], ranks: int) -> dict[tuple[int, int], list[int]]:
    return {edge(*e): list(range(1, ranks + 1)) for e in edges}


def fixed_labels(
    edges: Iterable[tuple[int, int]], ranks: int, count: int, rng: random.Random
) -> dict[tuple[int, int], list[int]]:
    count = min(count, ranks)
    return {e: sorted(rng.sample(range(1, ranks + 1), count)) for e in sorted({edge(*raw) for raw in edges})}


def bernoulli_labels(
    edges: Iterable[tuple[int, int]], ranks: int, probability: float, rng: random.Random
) -> dict[tuple[int, int], list[int]]:
    result = {}
    for raw in sorted({edge(*e) for e in edges}):
        chosen = [t for t in range(1, ranks + 1) if rng.random() < probability]
        if not chosen:
            chosen = [rng.randint(1, ranks)]  # structure-preserving policy from the handoff
        result[edge(*raw)] = chosen
    return result


def path_graph(length: int) -> tuple[int, set[tuple[int, int]]]:
    return length + 1, {edge(i, i + 1) for i in range(length)}


def diamond_chain(k: int) -> tuple[int, set[tuple[int, int]], list[tuple[str, tuple[int, ...]]], int]:
    """Return graph plus postorder SP nodes. Poles are 0 and k."""
    edges: set[tuple[int, int]] = set()
    nodes: list[tuple[str, tuple[int, ...]]] = []
    next_vertex = k + 1
    diamond_roots: list[int] = []
    for i in range(k):
        left, right = i, i + 1
        a, b = next_vertex, next_vertex + 1
        next_vertex += 2
        branch_roots = []
        for middle in (a, b):
            e1, e2 = edge(left, middle), edge(middle, right)
            edges.update((e1, e2))
            first = len(nodes); nodes.append(("edge", (left, middle)))
            second = len(nodes); nodes.append(("edge", (middle, right)))
            series = len(nodes); nodes.append(("series", (first, second)))
            branch_roots.append(series)
        root = len(nodes); nodes.append(("parallel", tuple(branch_roots)))
        diamond_roots.append(root)
    root = diamond_roots[0]
    for other in diamond_roots[1:]:
        combined = len(nodes); nodes.append(("series", (root, other)))
        root = combined
    return next_vertex, edges, nodes, root


def write_sp(path: Path, nodes: list[tuple[str, tuple[int, ...]]], root: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        out.write(f"sp {len(nodes)} {root}\n")
        for node_id, (kind, args) in enumerate(nodes):
            out.write(f"{node_id} {kind} {' '.join(map(str, args))}\n")


def random_ttsp(
    leaves: int, parallel_probability: float, rng: random.Random
) -> tuple[int, set[tuple[int, int]], list[tuple[str, tuple[int, ...]]], int]:
    """Generate a simple TTSP graph with exactly ``leaves`` edge leaves."""
    if leaves < 1:
        raise ValueError("leaves must be positive")
    nodes: list[tuple[str, tuple[int, ...]]] = []
    edges: set[tuple[int, int]] = set()
    next_vertex = 2

    def base(x: int, y: int) -> int:
        pair = edge(x, y)
        if pair in edges:
            raise ValueError("generator attempted a duplicate static edge")
        edges.add(pair)
        result = len(nodes); nodes.append(("edge", (x, y)))
        return result

    def series_only(x: int, y: int, count: int) -> int:
        nonlocal next_vertex
        if count < 2:
            raise ValueError("parallel branch must contain at least two leaves")
        middle = next_vertex; next_vertex += 1
        left_count = rng.randint(1, count - 1)
        left = build(x, middle, left_count)
        right = build(middle, y, count - left_count)
        result = len(nodes); nodes.append(("series", (left, right)))
        return result

    def build(x: int, y: int, count: int) -> int:
        nonlocal next_vertex
        if count == 1:
            return base(x, y)
        use_parallel = count >= 4 and rng.random() < parallel_probability
        if use_parallel:
            first_count = rng.randint(2, count - 2)
            first = series_only(x, y, first_count)
            second = series_only(x, y, count - first_count)
            result = len(nodes); nodes.append(("parallel", (first, second)))
            return result
        middle = next_vertex; next_vertex += 1
        left_count = rng.randint(1, count - 1)
        left = build(x, middle, left_count)
        right = build(middle, y, count - left_count)
        result = len(nodes); nodes.append(("series", (left, right)))
        return result

    root = build(0, 1, leaves)
    return next_vertex, edges, nodes, root


@dataclass
class PartialKTree:
    n: int
    edges: set[tuple[int, int]]
    bags: list[set[int]]
    tree_edges: list[tuple[int, int]]
    width: int


def random_partial_ktree(n: int, width: int, delete_probability: float, rng: random.Random) -> PartialKTree:
    if width < 1 or n < width + 1:
        raise ValueError("need n >= width + 1")
    initial = set(range(width + 1))
    bags = [initial]
    edges = {edge(u, v) for u in initial for v in initial if u < v}
    # Each entry remembers a bag that contains the clique.
    cliques: list[tuple[tuple[int, ...], int]] = []
    for omitted in initial:
        cliques.append((tuple(sorted(initial - {omitted})), 0))
    tree_edges: list[tuple[int, int]] = []
    for vertex in range(width + 1, n):
        clique, owner = rng.choice(cliques)
        bag = set(clique) | {vertex}
        bag_id = len(bags)
        bags.append(bag)
        tree_edges.append((owner, bag_id))
        for u in clique:
            edges.add(edge(u, vertex))
        for omitted in bag:
            new_clique = tuple(sorted(bag - {omitted}))
            cliques.append((new_clique, bag_id))
    if delete_probability:
        full_edges = set(edges)
        adjacency = [[] for _ in range(n)]
        for u, v in sorted(full_edges):
            adjacency[u].append(v); adjacency[v].append(u)
        # Protect a DFS spanning tree; delete only non-tree edges.
        protected: set[tuple[int, int]] = set()
        seen = {0}; stack = [0]
        while stack:
            u = stack.pop()
            for v in adjacency[u]:
                if v not in seen:
                    seen.add(v); stack.append(v); protected.add(edge(u, v))
        edges = protected | {e for e in sorted(full_edges - protected) if rng.random() >= delete_probability}
    return PartialKTree(n, edges, bags, tree_edges, width)


class NiceBuilder:
    def __init__(self) -> None:
        self.nodes: list[tuple[str, tuple[int, ...], tuple[int, ...]]] = []

    def add(self, kind: str, args: tuple[int, ...], bag: set[int]) -> int:
        node = len(self.nodes)
        self.nodes.append((kind, args, tuple(sorted(bag))))
        return node

    def convert_bag(self, node: int, current: set[int], target: set[int]) -> int:
        for vertex in sorted(current - target):
            current = current - {vertex}
            node = self.add("forget-v", (node, vertex), current)
        for vertex in sorted(target - current):
            current = current | {vertex}
            node = self.add("introduce-v", (node, vertex), current)
        return node


def write_nice_decomposition(
    path: Path,
    graph: PartialKTree,
    s: int,
    z: int,
) -> None:
    """Normalize a supplied tree decomposition and introduce every edge once."""
    adjacency = [[] for _ in graph.bags]
    for a, b in graph.tree_edges:
        adjacency[a].append(b); adjacency[b].append(a)
    parent = [-1] * len(graph.bags)
    depth = [0] * len(graph.bags)
    order = [0]
    for bag_id in order:
        for neighbor in adjacency[bag_id]:
            if neighbor == parent[bag_id]:
                continue
            parent[neighbor] = bag_id
            depth[neighbor] = depth[bag_id] + 1
            order.append(neighbor)
    assigned: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(graph.bags))}
    for u, v in graph.edges:
        candidates = [i for i, bag in enumerate(graph.bags) if u in bag and v in bag]
        if not candidates:
            raise ValueError(f"decomposition covers no bag for edge {(u, v)}")
        assigned[min(candidates, key=lambda i: depth[i])].append((u, v))

    normalized = [bag | {s, z} for bag in graph.bags]
    builder = NiceBuilder()

    def build(bag_id: int) -> int:
        bag = normalized[bag_id]
        children = [x for x in adjacency[bag_id] if parent[x] == bag_id]
        branches = []
        for child in children:
            child_node = build(child)
            branches.append(builder.convert_bag(child_node, set(normalized[child]), set(bag)))
        if not branches:
            node = builder.add("leaf", (), bag)
        else:
            node = branches[0]
            for branch in branches[1:]:
                node = builder.add("join", (node, branch), bag)
        for u, v in sorted(assigned[bag_id]):
            node = builder.add("introduce-e", (node, u, v), bag)
        return node

    root = build(0)
    root = builder.convert_bag(root, set(normalized[0]), {s, z})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        out.write(f"ntd {len(builder.nodes)} {root} {graph.width}\n")
        for node_id, (kind, args, bag) in enumerate(builder.nodes):
            prefix = " ".join(map(str, args))
            if prefix:
                prefix += " "
            out.write(f"{node_id} {kind} {prefix}{len(bag)} {' '.join(map(str, bag))}\n")
