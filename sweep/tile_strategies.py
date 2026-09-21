"""Measure every ABC strategy's cell area, for every tile type.

Synthesis is the cheap part of a build, twenty seconds against fifteen minutes
for a harden, and on `LUT4x8_ha` cell area ordered the strategies exactly as
routability did. So the strategy for each type is chosen here and only the
winner is hardened.

Each point runs in its own copy of the type's `_nl` synthesis step, because two
Yosys runs sharing one workspace would overwrite each other's netlist and tmp
directory. The copy is the `script/` and `data/` pair plus a rewritten
`global_var.tcl`; the RTL it names is read in place.

Run `flow synth` first, which is what writes the `_nl` workspaces this reads.
"""

from __future__ import annotations

import gzip
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD = PROJECT / "build"
SWEEP = PROJECT / "sweep"
SCRATCH = Path(os.environ.get("TMPDIR", "/tmp")) / "strategysweep"
TECHMAP = PROJECT / "techmap" / "ics55_models.v"
LIBERTY = Path(
    "/home/kelvin/side-project/ecc-spike/pdk/IP/STD_cell/ics55_LLSC_H7C_V1p10C100"
)
# The script validates the index and exits 1 past the end of a family, so the
# ranges are the counts in `yosys_synthesis.tcl` and an overrun records nothing.
STRATEGIES = (
    [f"DELAY {i}" for i in range(18)]
    + [f"AREA {i}" for i in range(16)]
    + [f"BALANCE {i}" for i in range(12)]
)
CELL = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s+\\?\S+\s*\(", re.M)


def cell_areas() -> dict[str, float]:
    """Read every standard cell's area from the typical-corner liberty files."""
    areas: dict[str, float] = {}
    for lib in LIBERTY.glob("*/liberty/*typ_tt*.lib"):
        cell = None
        for line in lib.read_text().splitlines():
            found = re.match(r"\s*cell\s*\((\w+)\)", line)
            if found:
                cell = found.group(1)
            found = re.match(r"\s*area\s*:\s*([\d.]+)", line)
            if found and cell:
                areas.setdefault(cell, float(found.group(1)))
                cell = None
    return areas


def synthesis_step(tile: str) -> Path:
    return BUILD / "tiles" / f"{tile}_nl" / "default" / "Synthesis_yosys"


def measure(argument: tuple[str, str]) -> tuple[str, str, int, float] | None:
    """Synthesise one tile under one strategy and return its cell count and area."""
    tile, strategy = argument
    source = synthesis_step(tile)
    work = SCRATCH / tile / strategy.replace(" ", "-")
    shutil.rmtree(work, ignore_errors=True)
    (work / "data" / "tmp").mkdir(parents=True)
    (work / "output").mkdir()
    (work / "report").mkdir()
    (work / "feature").mkdir()
    shutil.copytree(source / "script", work / "script")
    (work / "data" / "global_var.tcl").write_text(
        (source / "data" / "global_var.tcl").read_text().replace(str(source), str(work))
    )

    subprocess.run(
        ["yosys", "yosys_synthesis.tcl"],
        cwd=work / "script",
        env={
            **os.environ,
            "YOSYS_TECHMAP_FILES": str(TECHMAP),
            "YOSYS_SYNTH_STRATEGY": strategy,
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    netlist = next(work.glob("output/*_Synthesis.v.gz"), None)
    if netlist is None:
        return None

    areas = AREAS
    with gzip.open(netlist, "rt") as handle:
        cells = [c for c in CELL.findall(handle.read()) if c in areas]
    shutil.rmtree(work, ignore_errors=True)
    return tile, strategy, len(cells), sum(areas[c] for c in cells)


AREAS = cell_areas()


def main(tiles: list[str], jobs: int) -> None:
    missing = [t for t in tiles if not (synthesis_step(t) / "data").exists()]
    if missing:
        raise SystemExit(f"no _nl synthesis workspace for {missing}; run flow synth")

    points = [(tile, strategy) for tile in tiles for strategy in STRATEGIES]
    best: dict[str, tuple[str, int, float]] = {}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for result in pool.map(measure, points):
            if result is None:
                continue
            tile, strategy, count, area = result
            if tile not in best or area < best[tile][2]:
                best[tile] = (strategy, count, area)
            with (SWEEP / f"strategies_{tile}.tsv").open("a") as handle:
                handle.write(f"{strategy}\t{count}\t{area:.1f}\n")
            print(f"{tile}\t{strategy}\t{count}\t{area:.1f}", flush=True)

    print("\n=== best per tile ===", flush=True)
    for tile in sorted(best):
        strategy, count, area = best[tile]
        print(f"{tile}\t{strategy}\t{count}\t{area:.1f}", flush=True)


if __name__ == "__main__":
    main(sys.argv[2:], jobs=int(sys.argv[1]))
