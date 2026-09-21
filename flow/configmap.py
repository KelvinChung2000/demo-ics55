"""Fit a tile's configuration-bit mapping to the placement ECC produced for it.

FABulous searches this mapping from a placement it reads out of OpenDB, which
this project has no route to: `flow` drives ECC's iEDA flow and the tile never
enters a LibreLane step. The search itself needs none of that. It takes a
`Placement`, which is four fields, and every one of them is in the DEF that
`legalization` writes, so the ECC run supplies the placement and FABulous
supplies the assignment.

The coupling between the two is one file. A tile's `<tile>_ConfigMem.csv` says
which crosspoint holds which logical bit, `<tile>_ConfigMem.v` is generated from
it, and nothing else in the tile depends on the choice. Rewriting both is
therefore the whole of applying a new mapping.

`FABULOUS_ROOT` has to point at a checkout carrying the configuration-mapping
search, which is FABulous PR #1042 and not yet on main.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

DBU_PER_MICRON = 1000.0

# `Inst_<tile>_ConfigMem.Inst_frame<f>_bit<b>.<leaf> <cell> + PLACED ( x y )`.
# The crosspoint is in the instance path, so no netlist walk is needed to say
# which frame line a latch currently sits on.
LATCH = re.compile(
    r"^\s*-\s+(?P<instance>\S*Inst_frame(?P<frame>\d+)_bit(?P<bit>\d+)\.\S*DLATCH\S*)"
    r"\s+\S+\s+\+\s+PLACED\s+\(\s*(?P<x>-?\d+)\s+(?P<y>-?\d+)\s*\)"
)
PIN = re.compile(r"^\s*-\s+(?P<name>Frame(?:Data|Strobe)(?:_O)?_(?P<index>\d+))\s")
FIXED = re.compile(r"\+\s+FIXED\s+\(\s*(?P<x>-?\d+)\s+(?P<y>-?\d+)\s*\)")
DIEAREA = re.compile(
    r"^DIEAREA\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)"
)


@dataclass(frozen=True)
class Dump:
    """The `FABulous.DumpPlacement` JSON, built from a DEF instead of OpenDB."""

    die: tuple[float, float, float, float]
    data_y: dict[int, tuple[float, float]]
    strobe_x: dict[int, tuple[float, float]]
    latches: list[dict[str, object]]

    def write(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "die": list(self.die),
                    "data_y": {str(k): list(v) for k, v in self.data_y.items()},
                    "strobe_x": {str(k): list(v) for k, v in self.strobe_x.items()},
                    "latches": self.latches,
                },
                indent=2,
            )
        )


def _lines(def_path: Path):
    opener = gzip.open if def_path.suffix == ".gz" else open
    with opener(def_path, "rt", errors="replace") as handle:
        yield from handle


def read_def(def_path: Path) -> Dump:
    """Build the placement dump from one DEF.

    A frame net enters on one border and leaves on the opposite one, so its two
    pins differ only on the axis the trunk does not run along: `FrameData_i` and
    `FrameData_O_i` share a y, `FrameStrobe_j` and `FrameStrobe_O_j` share an x.
    That shared coordinate is what the search fits, and taking both pins rather
    than assuming they agree lets a skewed floorplan report a real interval.
    """
    die: tuple[float, float, float, float] | None = None
    latches: list[dict[str, object]] = []
    pins: dict[str, tuple[float, float]] = {}
    pending: str | None = None

    for line in _lines(def_path):
        if die is None and (area := DIEAREA.match(line)):
            die = tuple(int(v) / DBU_PER_MICRON for v in area.groups())  # type: ignore[assignment]
        if latch := LATCH.match(line):
            frame, bit = int(latch["frame"]), int(latch["bit"])
            latches.append(
                {
                    "frame": frame,
                    "data_bit": bit,
                    "instance": latch["instance"],
                    "x": int(latch["x"]) / DBU_PER_MICRON,
                    "y": int(latch["y"]) / DBU_PER_MICRON,
                    "data_pin": "D",
                    "strobe_pin": "E",
                }
            )
        if pin := PIN.match(line):
            pending = pin["name"]
        elif pending is not None and (fixed := FIXED.search(line)):
            pins[pending] = (
                int(fixed["x"]) / DBU_PER_MICRON,
                int(fixed["y"]) / DBU_PER_MICRON,
            )
            pending = None

    if die is None:
        raise ValueError(f"{def_path} carries no DIEAREA")
    if not latches:
        raise ValueError(f"{def_path} holds no Inst_frame<f>_bit<b> latch instance")

    data_y, strobe_x = {}, {}
    for name, (x, y) in pins.items():
        index = int(name.rsplit("_", 1)[1])
        if name.startswith("FrameData"):
            data_y.setdefault(index, []).append(y)  # type: ignore[union-attr]
        else:
            strobe_x.setdefault(index, []).append(x)  # type: ignore[union-attr]
    return Dump(
        die=die,
        data_y={k: (min(v), max(v)) for k, v in data_y.items()},  # type: ignore[arg-type]
        strobe_x={k: (min(v), max(v)) for k, v in strobe_x.items()},  # type: ignore[arg-type]
        latches=latches,
    )


def main() -> None:
    tile, def_path, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    root = Path(os.environ["FABULOUS_ROOT"])
    sys.path.insert(0, str(root))

    from fabulous.fabric_definition.configmem import ConfigMem
    from fabulous.fabric_generator.gds_generator.opt.config_mapping import (
        solve_config_mapping,
    )
    from fabulous.fabric_generator.gds_generator.opt.placement import Placement

    dump = read_def(def_path)
    dump_path = out / f"{tile}_placement.json"
    dump.write(dump_path)

    csv = Path("Tile") / tile / f"{tile}_ConfigMem.csv"
    frames = max(dump.strobe_x) + 1
    width = max(dump.data_y) + 1
    memory = ConfigMem.from_csv(
        csv, frame_bits_per_row=width, max_frames_per_col=frames
    )
    proposal, metrics = solve_config_mapping(Placement.from_json(dump_path), memory)

    print(f"{len(dump.latches)} latches on a {frames} x {width} frame grid")
    print(f"stub length {metrics.stub_before:.1f} -> {metrics.stub_after:.1f} um "
          f"({100 * (1 - metrics.stub_after / metrics.stub_before):.2f}% shorter), "
          f"{len(metrics.unplaced_bits)} bits with no placed latch")

    # `to_csv` writes to the memory's own `source`, and the proposal inherits
    # the tile's, so the file is rebound rather than the tile overwritten in place.
    written = out / f"{tile}_ConfigMem.csv"
    proposal = replace(proposal, source=written)
    proposal.to_csv()

    # The module is generated from the same object the CSV was written from, so
    # the two cannot describe different mappings.
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import (
        VerilogCodeGenerator,
    )
    from fabulous.fabric_generator.gen_fabric.gen_configmem import generate_config_mem

    writer = VerilogCodeGenerator()
    writer.outFileName = out / f"{tile}_ConfigMem.v"
    generate_config_mem(writer, tile, proposal)  # writes the file itself
    print(f"wrote {written} and {writer.outFileName}")


if __name__ == "__main__":
    main()
