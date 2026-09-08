"""Abut a heterogeneous fabric of painted tiles, and prove every seam is wired.

Assembly needs no fabric-level route: tiles whose paired pins sit at the same
offset on opposite edges connect by touching, so this places masters and nothing
else. The checks afterwards are the point of the module. iEDA's own pin
placement spaces every edge by the same formula, so it lands east and west pins
at matching offsets by construction and passes a crossing count while shorting
unrelated signals at 254 of 256 crossings. Only resolving which pin meets which,
against the links `eFPGA.v` itself declares, tells a wired fabric from one whose
tiles merely sit next to each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import klayout.db as kdb

from flow.fabric import Fabric, Side, load_fabric
from flow.plan import DBU, PIN_WIDTH, Plan, Seam, TilePlacement

TILE_CELL = "DIEAREA"
FABRIC_CELL = "FABRIC"
GDS_LAYER = {"MET1": 7, "MET3": 11, "MET4": 13, "MET5": 15}
SIGNAL_LAYER: dict[str, str] = {"vertical": "MET3", "horizontal": "MET4"}
PDN_LAYER: dict[str, tuple[str, ...]] = {"vertical": ("MET1", "MET5"), "horizontal": ("MET4",)}
# The side each of the two tiles a seam separates presents to it, the tile on the
# lower coordinate first.
FACING: dict[str, tuple[Side, Side]] = {"vertical": ("E", "W"), "horizontal": ("N", "S")}

# Column, grid row with the sub-row folded in, and DEF pin name: enough to name
# one end of one link without going back to the instance.
Endpoint = tuple[int, int, str]


@dataclass(frozen=True)
class Crossing:
    """One merged shape conducting through a seam, measured along the seam."""

    centre: int  # DBU along the seam
    width: int


def _masters(layout: kdb.Layout, tile_gds: dict[str, Path]) -> dict[str, kdb.Cell]:
    """Import each tile type's `DIEAREA` once, under a cell named for the type.

    Raises when a tile GDS disagrees with the plan's database unit, because
    `copy_tree` moves shapes between layouts without scaling them.
    """
    masters: dict[str, kdb.Cell] = {}
    for tile_type, path in sorted(tile_gds.items()):
        source = kdb.Layout()
        source.read(str(path))
        if abs(source.dbu * DBU - 1) > 1e-9:
            raise ValueError(f"{path} is {source.dbu} um per DBU, the plan is 1/{DBU}")
        top = source.cell(TILE_CELL)
        if top is None:
            raise ValueError(f"{path} has no {TILE_CELL} cell, so iEDA did not write it")
        masters[tile_type] = layout.create_cell(tile_type)
        masters[tile_type].copy_tree(top)
    return masters


def _place(layout: kdb.Layout, plan: Plan, masters: dict[str, kdb.Cell]) -> kdb.Cell:
    """Instance every planned tile at its own die corner.

    One `CellInstArray` cannot do this. The fabric has five column widths, two
    row heights and a double-height DSP supertile, so there is no single pitch.
    """
    missing = sorted({placement.tile_type for placement in plan.placements} - masters.keys())
    if missing:
        raise ValueError(f"no painted GDS given for tile types {missing}")
    fabric = layout.create_cell(FABRIC_CELL)
    for placement in plan.placements:
        fabric.insert(
            kdb.CellInstArray(
                masters[placement.tile_type].cell_index(),
                kdb.Trans(kdb.Vector(placement.x, placement.y)),
            )
        )
    return fabric


def _crossings(
    cell: kdb.Cell, layer: int, orientation: str, at: int, extent: int
) -> list[Crossing]:
    """Return the centre and the width, along the seam, of every shape crossing it.

    Counting shapes inside the window is not enough: two pins that stop dead on
    the boundary give the same count as one pin pair that merges through it.
    Only a merged shape with metal strictly either side of `at` conducts. The
    width separates a signal pin from a PDN stripe, which share MET4 on a
    horizontal seam. The whole seam line is taken at once and each crossing is
    filed by its centre rather than clipped to one seam's band, so a stripe
    sitting on the boundary between two bands is measured at its own width and
    counted once.
    """
    vertical = orientation == "vertical"
    window = kdb.Box(at - 1, 0, at + 1, extent) if vertical else kdb.Box(0, at - 1, extent, at + 1)
    metal = kdb.Region(cell.begin_shapes_rec_touching(layer, window))
    found = []
    for polygon in (metal & kdb.Region(window)).merged().each():
        box = polygon.bbox()
        before, after = (box.left, box.right) if vertical else (box.bottom, box.top)
        if before < at < after:
            centre, width = (
                (box.center().y, box.height()) if vertical else (box.center().x, box.width())
            )
            found.append(Crossing(centre=centre, width=width))
    return found


def _seam_lines(plan: Plan) -> dict[tuple[str, int], list[Seam]]:
    """Group the seams that share one line, so its metal is read once."""
    lines: dict[tuple[str, int], list[Seam]] = {}
    for seam in plan.seams:
        lines.setdefault((seam.orientation, seam.at), []).append(seam)
    return lines


def _within(crossings: list[Crossing], seam: Seam) -> list[Crossing]:
    """Keep the crossings whose centre falls in one seam's band, each in one band."""
    return [crossing for crossing in crossings if seam.low <= crossing.centre < seam.high]


def _facing(plan: Plan, seam: Seam) -> tuple[TilePlacement, TilePlacement]:
    """Return the two tiles a seam separates, the one on the lower coordinate first.

    Raises when a seam does not resolve to exactly one tile a side, which means
    the plan's tile sizes and its own seam list disagree.
    """
    vertical = seam.orientation == "vertical"
    lower: list[TilePlacement] = []
    upper: list[TilePlacement] = []
    for placement in plan.placements:
        width, height = plan.tile_size[placement.tile_type]
        x, y = (placement.x, placement.x + width), (placement.y, placement.y + height)
        across, along = (x, y) if vertical else (y, x)
        if along[0] > seam.low or along[1] < seam.high:
            continue
        if across[1] == seam.at:
            lower.append(placement)
        elif across[0] == seam.at:
            upper.append(placement)
    if len(lower) != 1 or len(upper) != 1:
        raise ValueError(
            f"{seam.orientation} seam at {seam.at} over {seam.low}..{seam.high} borders "
            f"{len(lower)} tiles below and {len(upper)} above, not one each"
        )
    return lower[0], upper[0]


def _edge_pins(plan: Plan, placement: TilePlacement, side: Side, seam: Seam) -> dict[int, str]:
    """Map each die offset along a seam to the pin of one tile sitting there.

    Raises when two pins of one tile share an offset on the same edge, which
    would make the meeting pin ambiguous.
    """
    origin = placement.y if seam.orientation == "vertical" else placement.x
    here: dict[int, str] = {}
    for pin in plan.pins[placement.tile_type]:
        offset = origin + pin.offset
        if pin.side != side or not seam.low <= offset <= seam.high:
            continue
        if offset in here:
            raise ValueError(
                f"{placement.name} has {pin.name} and {here[offset]} both at {offset} on {side}"
            )
        here[offset] = pin.name
    return here


def _endpoint(placement: TilePlacement, pin: str, sub_row: dict[tuple[str, str], int]) -> Endpoint:
    """Name one end of a link by the grid position of the tile carrying the pin."""
    return (placement.column, placement.row + sub_row[placement.tile_type, pin], pin)


def _sub_rows(fabric: Fabric) -> dict[tuple[str, str], int]:
    """Give every scalar pin the supertile slice its port belongs to."""
    return {
        (tile.name, bit.name): tile.ports[fabric.port_of(bit)].sub_row
        for tile in fabric.tile_types.values()
        for bit in tile.bits()
    }


def _link_pairs(fabric: Fabric) -> set[frozenset[Endpoint]]:
    """Return every declared link as the unordered pair of pin positions it joins."""
    return {
        frozenset(
            (
                (link.driver_at[0], link.driver_at[1], link.driver.name),
                (link.receiver_at[0], link.receiver_at[1], link.receiver.name),
            )
        )
        for link in fabric.links
    }


def _check_crossings(cell: kdb.Cell, layout: kdb.Layout, plan: Plan) -> list[str]:
    """Count the signal shapes merging through each seam, against the plan."""
    failures = []
    found = 0
    for (orientation, at), seams in _seam_lines(plan).items():
        extent = plan.height if orientation == "vertical" else plan.width
        layer = layout.layer(GDS_LAYER[SIGNAL_LAYER[orientation]], 0)
        line = _crossings(cell=cell, layer=layer, orientation=orientation, at=at, extent=extent)
        for seam in seams:
            # A PDN stripe shares MET4 with the north-south pins. A pin pair
            # merges to exactly one pin width, so anything wider is power or a
            # pin shorted to it, and neither is a crossing this seam asked for.
            signals = [crossing for crossing in _within(line, seam) if crossing.width <= PIN_WIDTH]
            found += len(signals)
            if len(signals) != seam.crossings:
                failures.append(
                    f"{orientation} seam at {at} over {seam.low}..{seam.high}: "
                    f"{len(signals)} crossings, expected {seam.crossings}"
                )
    wanted = sum(seam.crossings for seam in plan.seams)
    print(
        f"crossings: {found} of {wanted} conduct over {len(plan.seams)} seams, "
        f"{len(failures)} seams miscounted"
    )
    return failures


def _check_pairing(plan: Plan, fabric: Fabric) -> list[str]:
    """Check that the two pins meeting at each seam offset are the ends of one link."""
    sub_row = _sub_rows(fabric)
    links = _link_pairs(fabric)
    failures = []
    met = 0
    for seam in plan.seams:
        lower, upper = _facing(plan, seam)
        lower_side, upper_side = FACING[seam.orientation]
        below = _edge_pins(plan=plan, placement=lower, side=lower_side, seam=seam)
        above = _edge_pins(plan=plan, placement=upper, side=upper_side, seam=seam)
        meeting = sorted(set(below) & set(above))
        met += len(meeting)
        if len(meeting) != seam.crossings:
            failures.append(
                f"{lower.name} meets {upper.name} at {len(meeting)} offsets, "
                f"{seam.crossings} links cross that seam"
            )
        for offset in meeting:
            pair = frozenset(
                (
                    _endpoint(lower, below[offset], sub_row),
                    _endpoint(upper, above[offset], sub_row),
                )
            )
            if pair not in links:
                failures.append(
                    f"{lower.name}.{below[offset]} meets {upper.name}.{above[offset]} "
                    f"at {offset}, which eFPGA.v does not link"
                )
    print(f"pairing: {met} pin pairs meet across {len(plan.seams)} seams, {len(failures)} wrong")
    return failures


def _check_pdn(cell: kdb.Cell, layout: kdb.Layout, plan: Plan) -> list[str]:
    """Count the power shapes merging through each seam, failing only where none do."""
    failures = []
    totals: dict[str, int] = {name: 0 for names in PDN_LAYER.values() for name in names}
    for (orientation, at), seams in _seam_lines(plan).items():
        extent = plan.height if orientation == "vertical" else plan.width
        for name in PDN_LAYER[orientation]:
            line = _crossings(
                cell=cell,
                layer=layout.layer(GDS_LAYER[name], 0),
                orientation=orientation,
                at=at,
                extent=extent,
            )
            for seam in seams:
                power = _within(line, seam)
                # MET4 carries the north-south pins too, so on that seam a
                # crossing is power only when it is wider than one pin.
                if name == SIGNAL_LAYER[orientation]:
                    power = [crossing for crossing in power if crossing.width > PIN_WIDTH]
                totals[name] += len(power)
                if not power:
                    failures.append(
                        f"{orientation} seam at {at} over {seam.low}..{seam.high} "
                        f"has no {name} power crossing"
                    )
    counted = ", ".join(f"{name} {total}" for name, total in sorted(totals.items()))
    print(f"PDN: {counted} crossings, {len(failures)} seams carry none")
    return failures


def stitch(plan: Plan, tile_gds: dict[str, Path], out_gds: Path) -> None:
    """Abut the planned fabric from painted tile GDS files and check every seam.

    The layout is written before the checks run, so a fabric that fails is still
    on disk to look at. Raises `SystemExit` listing every seam that fails.
    """
    layout = kdb.Layout()
    layout.dbu = 1 / DBU
    cell = _place(layout, plan, _masters(layout, tile_gds))
    layout.write(str(out_gds))
    print(f"{out_gds}  {len(plan.placements)} tiles  bbox {cell.dbbox()}")

    # The plan carries the seams but not the links, and the link table is the one
    # thing that must come from FABulous rather than from this flow.
    fabric = load_fabric(Path("."))
    failures = _check_crossings(cell, layout, plan)
    failures += _check_pairing(plan, fabric)
    failures += _check_pdn(cell, layout, plan)
    if failures:
        raise SystemExit("\n".join(failures))
