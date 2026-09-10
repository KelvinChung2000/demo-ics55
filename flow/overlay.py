"""Colour a layout by what each shape belongs to, rather than by which layer it is on.

KLayout draws a colour per layer and offers no per-cell or per-instance colour,
so grouping has to be expressed as layers. This writes a second GDS holding one
named layer per group alongside a `.lyp` that gives each of those layers its own
colour, to be loaded over the original as an overlay.

Grouping by cell reads the placements themselves and names each group after the
cell placed, so it separates standard cell types in an ECC layout and tile types
in a stitched fabric. Grouping by tile reads the `Tile_XnYm_TYPE.` prefix ECC
gives its net cells in the flat build, so it colours routing but not cells: a
flat placement records no tile, and the standard cells sit directly under the
top cell.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import klayout.db as kdb

TILE_RE = re.compile(r"^(Tile_X\d+Y\d+)_")
MASTER_PREFIX = "Master_"
FIRST_LAYER = 1000
"""Overlay layers start well above the PDK's own numbering, which stops at 15."""

# Eight hues at two lightnesses, so adjacent groups stay distinguishable when a
# design has more groups than the eye can separate by hue alone.
PALETTE = (
    "#ff3030",
    "#30ff30",
    "#4060ff",
    "#ffd020",
    "#ff30ff",
    "#20e0e0",
    "#ff8020",
    "#a060ff",
    "#a01818",
    "#18a018",
    "#2038a0",
    "#a08010",
    "#a018a0",
    "#109090",
    "#a05010",
    "#6030a0",
)


# The ICS55 layers ECC writes, identified in FINDINGS.md from the geometry
# itself: the cut layers are the ones whose every shape is one 0.09 um square.
# The GDS names no layer, so without this table KLayout shows bare numbers.
BASE_LAYERS = (
    (0, 0, "outline", "#808080", "I1"),
    (0, 2, "die", "#c0c0c0", "I1"),
    (7, 0, "MET1", "#2040ff", "I5"),
    (8, 0, "VIA1", "#8090ff", "I0"),
    (9, 0, "MET2", "#20c020", "I5"),
    (10, 0, "VIA2", "#80e080", "I0"),
    (11, 0, "MET3", "#d02020", "I5"),
    (12, 0, "VIA3", "#e08080", "I0"),
    (13, 0, "MET4", "#c0a020", "I5"),
    (14, 0, "VIA4", "#e0d080", "I0"),
    (15, 0, "MET5", "#c020c0", "I5"),
)


class By(str, Enum):
    """What decides a shape's group."""

    CELL = "cell"
    TILE = "tile"


@dataclass(frozen=True)
class Group:
    """One output layer: its name, and the boxes drawn on it."""

    name: str
    boxes: list[kdb.Box]


def _key(by: By, cell_name: str) -> str | None:
    """Return the group a top-level placement belongs to, or None to skip it."""
    if by is By.CELL:
        return cell_name.removeprefix(MASTER_PREFIX)
    match = TILE_RE.match(cell_name)
    return match.group(1) if match else None


def collect(layout: kdb.Layout, top: kdb.Cell, by: By, minimum: int) -> list[Group]:
    """Group every placement under `top`, largest group first.

    `minimum` drops groups below a size. It matters on ECC output, where every
    net is a cell placed exactly once, so grouping by cell without it buries the
    sixty real masters under a thousand groups of one.
    """
    boxes: dict[str, list[kdb.Box]] = {}
    for instance in top.each_inst():
        key = _key(by, layout.cell(instance.cell_index).name)
        if key is not None:
            boxes.setdefault(key, []).append(instance.bbox())
    ranked = sorted(boxes.items(), key=lambda item: -len(item[1]))
    return [
        Group(name=name, boxes=group) for name, group in ranked if len(group) >= minimum
    ]


def write_overlay(
    source: Path, out_gds: Path, out_lyp: Path, by: By, minimum: int = 1
) -> list[Group]:
    """Write the overlay and its colour file, returning the groups in layer order."""
    layout = kdb.Layout()
    layout.read(str(source))
    tops = layout.top_cells()
    top = max(tops, key=lambda cell: cell.child_instances())
    groups = collect(layout, top, by, minimum)
    if not groups:
        raise ValueError(
            f"nothing in {source} groups by {by.value} with at least {minimum} placements"
        )

    overlay = kdb.Layout()
    overlay.dbu = layout.dbu
    cell = overlay.create_cell(f"BY_{by.value.upper()}")
    for number, group in enumerate(groups):
        layer = overlay.layer(FIRST_LAYER + number, 0, group.name)
        for box in group.boxes:
            cell.shapes(layer).insert(box)
    overlay.write(str(out_gds))
    out_lyp.write_text(_properties(groups))
    return groups


def _entry(*, source: str, name: str, colour: str, dither: str) -> str:
    return "\n".join(
        (
            " <properties>",
            f"  <frame-color>{colour}</frame-color>",
            f"  <fill-color>{colour}</fill-color>",
            f"  <dither-pattern>{dither}</dither-pattern>",
            "  <visible>true</visible>",
            "  <transparent>false</transparent>",
            "  <width>1</width>",
            f"  <name>{name}</name>",
            f"  <source>{source}</source>",
            " </properties>",
        )
    )


def _properties(groups: list[Group]) -> str:
    """Render a layer properties file for the PDK layers and the overlay groups.

    Applying a properties file replaces the view's whole layer list, so the base
    layers are written out too. Without them MET1 to MET5 vanish from the view
    the moment the overlay's colours are loaded. Sources carry `@*` rather than a
    cellview number so the file does not depend on the order the two layouts were
    opened in, at the cost of one empty duplicate entry per layer per cellview.
    """
    entries = [
        _entry(source=f"{number}/{datatype}@*", name=name, colour=colour, dither=dither)
        for number, datatype, name, colour, dither in BASE_LAYERS
    ]
    entries += [
        _entry(
            source=f"{FIRST_LAYER + number}/0@*",
            name=f"{group.name} ({len(group.boxes)})",
            colour=PALETTE[number % len(PALETTE)],
            dither="I5",
        )
        for number, group in enumerate(groups)
    ]
    body = "\n".join(entries)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<layer-properties>\n{body}\n</layer-properties>\n'
