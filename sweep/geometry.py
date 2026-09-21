"""Solve the six free die dimensions the LUT anchor leaves open.

Abutment fixes every other size: the LUT's column width binds columns 1, 2, 4,
5, 7 and 8, and its height binds rows 1 to 14. What is left is the width of
columns 0, 3, 6 and 9 and the height of rows 0 and 15, and the fabric area is
the product of their sums, so the six do not separate.

They almost do. A tile in a core row has its height fixed, so its column's
minimum width follows from its cell area alone; only the twelve terminator
tiles couple a width to a row height. Fixing the two row heights therefore
determines every width.

A terminator row is set to the shortest its own IO tile will take and never
raised to relieve a column beside it, so the fabric grows in one direction only.
That costs area where a corner tile binds a narrow column: SW_term's 346 um^2
takes column 0 from W_IO's own 21.4 um out to 28.8.

Two bounds size a tile, and round 1 produced a failure of each kind.

Placement is the first. DreamPlace refuses a die whose movable area passes 0.99
of its **placeable** area, which is the core less the fixed blockages; see
`placeable`. N_IO at 82.6 x 19.6 sat at 0.844 of its core and 1.05 of its
placeable area, and never reached the router.

Routing is the second, and cell area does not express it. Each IO type is a
sliver carrying 128 or 129 pins on its long edge, and what the router runs out
of is width across the short axis. W_IO failed at a 15.2 um core while E_IO
passed at 17.4 with the higher density of the two, so 17.4 is the proven side of
a cliff somewhere between them.

Both measured 2026-09-21 at anchor 82.5; the runs are in `results.tsv`.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from placeable import DEEPEST, MARGIN, depths, edge_for, placeable  # noqa: E402

SITE_WIDTH = 0.2
HEIGHT_QUANTUM = 2.8

# Which column and which rows each tile type occupies, as the fabric places it.
COLUMN = {
    "W_IO": 0, "NW_term": 0, "SW_term": 0,
    "RegFile": 3, "N_term_RegFile": 3, "S_term_RegFile": 3,
    "MACC": 6, "N_term_MACC": 6, "S_term_MACC": 6,
    "E_IO": 9, "NE_term": 9, "SE_term": 9,
    "LUT4x8_ha": None, "N_IO": None, "S_IO": None,  # a LUT column, fixed
}
ROW = {  # None for a tile in the core rows, whose height the anchor fixes
    "NW_term": 0, "N_term_RegFile": 0, "N_term_MACC": 0, "NE_term": 0, "N_IO": 0,
    "SW_term": 15, "S_term_RegFile": 15, "S_term_MACC": 15, "SE_term": 15, "S_IO": 15,
    "W_IO": None, "RegFile": None, "MACC": None, "E_IO": None, "LUT4x8_ha": None,
}
CORE_ROWS = 14
LUT_COLUMNS = 6
# Shortest core across the short axis a 128-pin IO sliver has been routed at.
SLIVER_CORE = 17.4
SLIVERS = ("W_IO", "E_IO", "N_IO", "S_IO")


def up(value: float, quantum: float) -> float:
    return math.ceil(value / quantum - 1e-9) * quantum


def sliver(quantum: float) -> float:
    """Return the shortest die edge that leaves an IO sliver a routable core."""
    return up(SLIVER_CORE + 2 * MARGIN, quantum)


def need(tile: str, area: float, other: float, target: float, depth: float, quantum: float) -> float:
    """Return the shortest edge this tile takes beside an edge of `other`."""
    wanted = up(edge_for(area, other, target, depth), quantum)
    return max(wanted, sliver(quantum)) if tile in SLIVERS else wanted


def solve(cell: dict[str, float], target: dict[str, float], depth: dict[str, float],
          lut_width: float, core_height: float):
    """Return the six free dimensions, every tile's placement and routing bound met."""
    # N_IO and S_IO sit in a LUT column, so their short axis is the row height
    # and the row is the only lever either of them has.
    rows = {
        row: need(name, cell[name], lut_width, target[name], depth[name], HEIGHT_QUANTUM)
        for row, name in ((0, "N_IO"), (15, "S_IO"))
    }
    height = {**rows, None: core_height}
    width: dict[int, float] = {}
    binder: dict[int, str] = {}
    for tile, column in COLUMN.items():
        if column is None:
            continue
        # MACC is two core rows tall; every other tile spans one.
        own = height[ROW[tile]] * (2 if tile == "MACC" else 1)
        wanted = need(tile, cell[tile], own, target[tile], depth[tile], SITE_WIDTH)
        if wanted > width.get(column, 0.0):
            width[column], binder[column] = wanted, tile
    total_w = LUT_COLUMNS * lut_width + sum(width.values())
    total_h = CORE_ROWS * core_height + sum(rows.values())
    return total_w * total_h, width, binder, rows, total_w, total_h


def report(cell, target, depth, lut_width, core_height) -> None:
    area, width, binder, rows, total_w, total_h = solve(
        cell, target, depth, lut_width, core_height
    )
    print(f"fabric {total_w:.1f} x {total_h:.1f} = {area:.0f} um^2")
    for column, owner in ((0, "W_IO"), (3, "RegFile"), (6, "MACC"), (9, "E_IO")):
        print(
            f"  column {column} {owner:8s} {width[column]:6.1f}  bound by {binder[column]}"
        )
    for row, owner in ((0, "N_IO"), (15, "S_IO")):
        print(f"  row {row:<6d} {owner:8s} {rows[row]:6.1f}")
    print("  placeable utilisation each binding tile would reach:")
    height = {**rows, None: core_height}
    for column, owner in ((0, "W_IO"), (3, "RegFile"), (6, "MACC"), (9, "E_IO")):
        tile = binder[column]
        own = height[ROW[tile]] * (2 if tile == "MACC" else 1)
        free = placeable(width[column], own, depth[tile])
        print(f"    {tile:16s} {cell[tile] / free:.3f}")
    for row, name in ((0, "N_IO"), (15, "S_IO")):
        free = placeable(lut_width, rows[row], depth[name])
        print(f"    {name:16s} {cell[name] / free:.3f}")


if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    # The target is one placeable utilisation for every type, or a JSON file
    # naming the ones that differ: a type that routed in two iterations can be
    # pushed to the density its own run proved while the rest hold station.
    try:
        target = {tile: float(sys.argv[2]) for tile in data}
    except ValueError:
        given = json.load(open(sys.argv[2]))
        target = {tile: float(given.get(tile, given["default"])) for tile in data}
    fitted = depths()
    report(
        cell=data,
        target=target,
        depth={tile: fitted.get(tile, DEEPEST) for tile in data},
        lut_width=float(sys.argv[3]),
        core_height=float(sys.argv[4]),
    )
