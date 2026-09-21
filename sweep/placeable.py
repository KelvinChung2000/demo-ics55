"""Estimate the area DreamPlace will place into, which is not the core area.

The limit that refuses a die is `movable <= 0.99 * placeable`, and placeable
drops whatever the fixed blockages take. On the abutted tiles that is mostly the
pin rows: `flow.plan` drives every pin `PIN_DEPTH` into the die around the whole
border, so the loss scales with core perimeter rather than with core area, and a
small tile pays a far larger fraction of it. `NW_term` at 19.2 x 19.6 keeps 0.756
of its core where `MACC` at 75.8 x 168.0 keeps 0.963.

Modelled as a border of uniform depth, `placeable = core - 2 d (core_w + core_h)`,
with `d` fitted per tile from its own run. The fit is one point per tile, so it
predicts a nearby die and nothing further; a tile with no measurement takes the
deepest border seen, which is N_IO's 1.34 um.
"""

from __future__ import annotations

import csv
from pathlib import Path

SWEEP = Path(__file__).resolve().parent
MARGIN = 2.0
DEEPEST = 1.34  # um, N_IO's fitted border, the worst measured


def depths() -> dict[str, float]:
    """Return each tile type's fitted border depth, from every run that reported one."""
    found: dict[str, float] = {}
    results = SWEEP / "results.tsv"
    if not results.exists():
        return found
    for row in csv.DictReader(results.open(), delimiter="\t"):
        if row["dp_util"] == "-":
            continue
        width = float(row["die_w"]) - 2 * MARGIN
        height = float(row["die_h"]) - 2 * MARGIN
        lost = width * height - float(row["cell_area"]) / float(row["dp_util"])
        found[row["tile"]] = lost / 2 / (width + height)
    return found


def placeable(width: float, height: float, depth: float) -> float:
    core_w, core_h = width - 2 * MARGIN, height - 2 * MARGIN
    return core_w * core_h - 2 * depth * (core_w + core_h)


def edge_for(area: float, other: float, target: float, depth: float) -> float:
    """Return the edge at which `area` of cells reaches `target` of placeable area.

    Solves `area / target = (e - 2m)(o - 2m) - 2 d ((e - 2m) + (o - 2m))` for e.
    """
    other_core = other - 2 * MARGIN
    return (area / target + 2 * depth * other_core) / (other_core - 2 * depth) + 2 * MARGIN
