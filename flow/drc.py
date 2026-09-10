"""Check the stitched fabric against the tech LEF's own geometry rules.

iDRC never sees this layout. It runs inside a workspace on a DEF, and the
stitched fabric is a KLayout assembly with no workspace behind it, so the zero
each tile signed off at covers that tile alone and says nothing about the one
place per-tile DRC cannot look: the seam, where metal from two independently
routed dies comes within a track of itself for the first time.

The rules are read from the tech LEF rather than written down here, because
`drc_default_config.json` is empty and iDRC runs off that same file, so this
checks what iDRC checks. Antenna rules are not among them; the ICS55 release
ships no DRC deck and signoff happens at ICsprout.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import klayout.db as kdb

GDS_LAYER = {"MET1": 7, "MET2": 9, "MET3": 11, "MET4": 13, "MET5": 15}


@dataclass(frozen=True)
class Rule:
    """One routing layer's minimum geometry, in microns as the LEF states it."""

    layer: str
    width: float
    spacing: float
    area: float


@dataclass(frozen=True)
class Result:
    layer: str
    width: int
    spacing: int
    area: int

    @property
    def total(self) -> int:
        return self.width + self.spacing + self.area


def read_rules(tech_lef: Path) -> list[Rule]:
    """Return the minimum width, spacing and area of every routing layer."""
    text = tech_lef.read_text()
    rules = []
    for block in re.finditer(r"^LAYER (\w+)\n(.*?)^END \1", text, re.S | re.M):
        name, body = block.group(1), block.group(2)
        if "TYPE ROUTING" not in body or name not in GDS_LAYER:
            continue
        values = dict(re.findall(r"^\s+(WIDTH|SPACING|AREA)\s+([\d.]+)\s*;", body, re.M))
        missing = {"WIDTH", "SPACING", "AREA"} - values.keys()
        if missing:
            raise ValueError(f"{name} in {tech_lef} states no {sorted(missing)}")
        rules.append(
            Rule(
                layer=name,
                width=float(values["WIDTH"]),
                spacing=float(values["SPACING"]),
                area=float(values["AREA"]),
            )
        )
    if not rules:
        raise ValueError(f"{tech_lef} declares no routing layer this flow knows about")
    return rules


def check_layer(cell: kdb.Cell, layout: kdb.Layout, rule: Rule) -> Result:
    """Count width, spacing and area failures on one layer of a whole layout.

    The region is merged first, so metal from two abutted tiles meeting at a seam
    is measured as the one shape it has become rather than as two that touch.
    """
    index = layout.layer(GDS_LAYER[rule.layer], 0)
    merged = kdb.Region(cell.begin_shapes_rec(index)).merged()
    return Result(
        layer=rule.layer,
        width=merged.width_check(round(rule.width / layout.dbu)).count(),
        spacing=merged.space_check(round(rule.spacing / layout.dbu)).count(),
        area=merged.with_area(0, round(rule.area / layout.dbu**2)).count(),
    )
