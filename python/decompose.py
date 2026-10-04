#!/usr/bin/env python3
"""Recognize width<=2 and generate a normalized nice TD for arbitrary queries."""
import argparse
import json
from pathlib import Path
import subprocess

from generators import edge, write_nice_decomposition
from research_audit import elimination_decomposition

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("instance", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    info = json.loads(subprocess.check_output([str(ROOT / "build" / "tpcount"), "info", str(args.instance)], text=True))
    edges = set(); header = False
    for line in args.instance.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not header:
            header = True; continue
        u, v, _ = map(int, line.split()); edges.add(edge(u, v))
    graph = elimination_decomposition(info["n"], edges)
    if graph is None:
        raise SystemExit("Underlying graph has treewidth greater than 2; no file written.")
    write_nice_decomposition(args.output, graph, info["s"], info["z"])
    print(json.dumps({"width": graph.width, "output": str(args.output), "s": info["s"], "z": info["z"]}))


if __name__ == "__main__":
    main()
