"""Collect each tile type's least measured cell area, for the geometry solver.

The area a column has to hold is the area of the netlist the tile will actually
be hardened with, which is the strategy `setstrategy` writes, so the solver is
fed the sweep's minimum rather than ECC's `DELAY 4` default.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SWEEP = Path(__file__).resolve().parent


def areas() -> dict[str, float]:
    found = {}
    for path in sorted(SWEEP.glob("strategies_*.tsv")):
        rows = [
            line.split("\t")
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        found[path.stem.removeprefix("strategies_")] = min(float(r[2]) for r in rows)
    return found


if __name__ == "__main__":
    json.dump(areas(), open(sys.argv[1], "w"), indent=2)
    for tile, area in sorted(areas().items(), key=lambda item: -item[1]):
        print(f"{tile:16s} {area:9.1f}")
