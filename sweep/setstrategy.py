"""Write each tile type's winning ABC strategy into its own `ecc_config.toml`.

The strategy is chosen on cell area alone. That is the right criterion here
because cell area is what sizes a column: every tile in this fabric is a mux
and configuration-latch structure with no timing slack to trade, and on
LUT4x8_ha cell area ordered the strategies exactly as routability did.

A `[die]` table already in the file is kept, since the two are set by different
sweeps and neither should erase the other.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SWEEP = PROJECT / "build" / "sweep"


def best(tile_type: str) -> tuple[str, float]:
    """Return the least-area strategy this type was measured under."""
    rows = [
        line.split("\t")
        for line in (SWEEP / f"strategies_{tile_type}.tsv").read_text().splitlines()
        if line.strip()
    ]
    strategy, _, area = min(rows, key=lambda row: float(row[2]))
    return strategy, float(area)


def write(tile_type: str, strategy: str, area: float, baseline: float) -> None:
    path = PROJECT / "Tile" / tile_type / "ecc_config.toml"
    kept = [
        block
        for block in path.read_text().split("\n\n")
        if "[synthesis]" not in block
    ] if path.exists() else []
    saved = "" if baseline <= area else f", {baseline - area:.1f} um^2 below DELAY 4's {baseline:.1f}"
    block = (
        "# Least cell area of the 46 ABC strategies, measured on this tile's own\n"
        f"# netlist in sweep/strategies_{tile_type}.tsv: {area:.1f} um^2{saved}.\n"
        "[synthesis]\n"
        f'strategy = "{strategy}"\n'
    )
    path.write_text("\n\n".join([*[b for b in kept if b.strip()], block]))


if __name__ == "__main__":
    for tile_type in sys.argv[1:]:
        strategy, area = best(tile_type)
        rows = {
            line.split("\t")[0]: float(line.split("\t")[2])
            for line in (SWEEP / f"strategies_{tile_type}.tsv").read_text().splitlines()
            if line.strip()
        }
        baseline = rows["DELAY 4"]
        # A tile whose area no strategy moves is pure configuration latch and
        # routing mux with nothing for ABC to restructure. Naming a winner there
        # would record a tie as a measurement, so ECC's own default stands and
        # the file gets no [synthesis] block at all.
        if baseline <= area:
            print(f"{tile_type:16s} {'-':10s} {area:8.1f}  no strategy beats DELAY 4")
            continue
        write(tile_type, strategy, area, baseline)
        print(
            f"{tile_type:16s} {strategy:10s} {area:8.1f}  "
            f"{baseline - area:5.1f} um^2 below DELAY 4's {baseline:.1f}"
        )
