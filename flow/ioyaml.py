"""Read FABulous's IO pin order config, which decides the order along each edge.

FABulous writes one `io_pin_order.yaml` per tile, listing for each side an
ordered sequence of segments, each a regex over Verilog port names. It carries
no coordinates: the file says which pins share an edge and in what order, and
`flow.plan` turns that order into track offsets.

Two facing sides list the same buses at the same positions, because FABulous
emits a side's outgoing wires and the incoming wires of the opposite direction
in one fixed sequence. `LUT4x8_ha`'s East begins `E1BEG, E2BEG, E2BEGb` and its
West begins `E1END, E2MID, E2END`, so segment `i` of one edge always faces
segment `i` of its neighbour's, bus width included. That is what makes an order
chosen per tile safe for an abutted fabric, and `flow.verify` still tests the
consequence rather than trusting it.

The patterns are Verilog names with brackets, `E1BEG\\[\\d+\\]`, while a pin
reaches the DEF as `E1BEG_0`, so matching reconstructs the Verilog name from
the port model rather than rewriting the pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from flow.fabric import Bit, Fabric, Side

FILENAME = "io_pin_order.yaml"
SIDE_OF: dict[str, Side] = {"NORTH": "N", "EAST": "E", "SOUTH": "S", "WEST": "W"}
# `fabric.csv` sets `DisableUserCLK`, so the clock reaches a tile on the
# global-buffer network and FABulous's unconditional per-tile clock segments
# match nothing. Every other empty segment is a tile whose YAML and Verilog
# have drifted apart.
ABSENT_BY_DESIGN = re.compile(r"(?:^|_)UserCLKo?$")


@dataclass(frozen=True)
class Rank:
    """Where a pin sits in its side's order: which segment, and where within it."""

    side: Side
    segment: int
    position: int

    @property
    def key(self) -> tuple[int, int]:
        return self.segment, self.position


def _verilog_names(fabric: Fabric, tile_type: str) -> dict[str, Bit]:
    """Map each of a tile's Verilog scalar names to the DEF pin it becomes."""
    names: dict[str, Bit] = {}
    for port in fabric.tile_types[tile_type].ports.values():
        for index, bit in enumerate(port.bits(tile_type)):
            names[f"{port.name}[{index}]" if port.vectored else port.name] = bit
    return names


def _matches(pattern: str, name: str) -> bool:
    """Whether a segment pattern covers one Verilog scalar name.

    A pattern naming no index, `CO`, has to reach a port declared `[0:0]`,
    whose scalar is `CO[0]`; FABulous writes the port name alone for those.
    """
    return bool(re.fullmatch(pattern, name) or re.fullmatch(f"{pattern}\\[0\\]", name))


def read(fabric: Fabric, tile_type: str, root: Path) -> dict[Bit, Rank]:
    """Return every pin of one tile type, ranked by its place in the edge order.

    Raises if a pin matches no segment or two, or if a segment matches nothing
    it was not expected to, since either means the vendored YAML no longer
    describes the vendored Verilog.
    """
    path = root / "Tile" / tile_type / FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist, so nothing says what order {tile_type}'s "
            "edges take. Run `task gen-io-order`, which re-vendoring the tile "
            "library always needs following by."
        )
    document = yaml.safe_load(path.read_text())
    remaining = _verilog_names(fabric, tile_type)
    ranked: dict[Bit, Rank] = {}

    for sides in document.values():
        for side_name, segments in sides.items():
            for segment, entry in enumerate(segments):
                for pattern in entry["pins"]:
                    hits = [name for name in remaining if _matches(pattern, name)]
                    if not hits and not ABSENT_BY_DESIGN.search(pattern):
                        raise ValueError(
                            f"{path} names {pattern} on {side_name}, which matches no "
                            f"port of {tile_type}"
                        )
                    for position, name in enumerate(sorted(hits, key=_bit_order)):
                        ranked[remaining.pop(name)] = Rank(
                            SIDE_OF[side_name], segment, position
                        )

    if remaining:
        raise ValueError(
            f"{path} leaves {len(remaining)} pins of {tile_type} unordered: "
            f"{sorted(remaining)[:5]}"
        )
    return ranked


def _bit_order(name: str) -> tuple[str, int]:
    """Sort a segment's matches bus-major, low bit first, as `sort_mode` asks."""
    match = re.match(r"^(.*)\[(\d+)\]$", name)
    return (match.group(1), int(match.group(2))) if match else (name, 0)
