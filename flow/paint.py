"""Draw back the two kinds of geometry `Def2GdsWrite` leaves out of a routed tile.

iEDA emits a `PINS` cell, instances it under `DIEAREA` and writes nothing into
it, and it drops every special-net segment that reaches the die boundary for the
same reason, so a routed tile carries no metal within a quarter micron of any
die edge. Two tiles placed at the die pitch then abut on paper and touch nowhere.
The final DEF does carry both sets of rectangles, so they are painted back here
rather than recovered by re-running a step that has already been shown to lose
them.
"""

from __future__ import annotations

import gzip
import re
from collections.abc import Iterator
from pathlib import Path

import klayout.db as kdb

# Read off a routed net: N1BEG_0 runs MET3 -> VIA3 -> MET4 -> VIA3 -> MET3 ->
# VIA2 -> MET2, and its GDS shapes land on 11, 12, 13, 12, 11, 10, 9.
GDS_LAYER = {"MET1": 7, "MET2": 9, "MET3": 11, "MET4": 13, "MET5": 15}
PIN_CELL = "PINS"
TOP_CELL = "DIEAREA"
POWER_NETS = ("VDD", "VSS")

DIE_RE = re.compile(r"DIEAREA\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)")
PINS_RE = re.compile(r"^PINS \d+ ;\n(.*?)^END PINS", re.S | re.M)
SPECIAL_RE = re.compile(r"^SPECIALNETS \d+ ;\n(.*?)^END SPECIALNETS", re.S | re.M)
ENTRY_RE = re.compile(r"^\s*- (\S+)(.*?)^\s*;\n", re.S | re.M)
NET_RE = re.compile(r"\+ NET (\S+)")
PLACEMENT_RE = re.compile(
    r"\+ LAYER (\S+) \(\s*(-?\d+)\s+(-?\d+)\s*\) \(\s*(-?\d+)\s+(-?\d+)\s*\)"
    r"\s*\+ (?:PLACED|FIXED|COVER) \(\s*(-?\d+)\s+(-?\d+)\s*\)",
    re.S,
)
# A wiring statement opens with the net's status once and with NEW after that.
SEGMENT_RE = re.compile(r"(?:^|\s)(?:NEW|\+ (?:ROUTED|FIXED|COVER))\s+")
WIRE_RE = re.compile(r"(\w+)\s+(\d+)")
POINT_RE = re.compile(r"\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)")


def read_def(path: Path) -> str:
    """Return a DEF's text, whether or not it is gzipped."""
    opener = gzip.open if path.read_bytes()[:2] == b"\x1f\x8b" else open
    with opener(path, "rt") as handle:
        return handle.read()


def die_area(text: str) -> kdb.Box:
    """Return the die rectangle in DBU, and refuse a DEF that declares none."""
    match = DIE_RE.search(text)
    if match is None:
        raise ValueError("the DEF declares no DIEAREA, so no boundary can be recognised")
    llx, lly, urx, ury = (int(group) for group in match.groups())
    return kdb.Box(llx, lly, urx, ury)


def def_pins(text: str) -> dict[str, tuple[str, str, kdb.Box]]:
    """Return each pin's net, layer and absolute box, in DBU.

    The net matters because Yosys merges a FABulous feedthrough into one net, so
    `N4BEG_0` sits on `N4END_4` and its routing is filed under that name.
    Raises when a pin carries no placed layer rectangle to paint.
    """
    block = PINS_RE.search(text)
    if block is None:
        raise ValueError("the DEF has no PINS section, so it is not a final DEF")
    pins: dict[str, tuple[str, str, kdb.Box]] = {}
    for entry in ENTRY_RE.finditer(block.group(1)):
        name, body = entry.group(1), entry.group(2)
        net = NET_RE.search(body)
        placement = PLACEMENT_RE.search(body)
        if net is None or placement is None:
            raise ValueError(f"pin {name} has no net or no placed layer rectangle")
        layer, x1, y1, x2, y2, x, y = placement.groups()
        box = kdb.Box(int(x1) + int(x), int(y1) + int(y), int(x2) + int(x), int(y2) + int(y))
        pins[name] = (net.group(1), layer, box)
    return pins


def _points(chunk: str) -> list[tuple[int, int]]:
    """Resolve one wiring statement's coordinates, expanding DEF's `*` repeats."""
    points: list[tuple[int, int]] = []
    for raw_x, raw_y in POINT_RE.findall(chunk):
        if not points and "*" in (raw_x, raw_y):
            raise ValueError(f"a wiring statement opens on a * repeat: {chunk[:60]}")
        points.append(
            (
                points[-1][0] if raw_x == "*" else int(raw_x),
                points[-1][1] if raw_y == "*" else int(raw_y),
            )
        )
    return points


def _wires(body: str) -> Iterator[tuple[str, kdb.Box]]:
    """Turn one special net's wiring into a rectangle per straight run, in DBU.

    A statement holding a single point is a via and contributes no rectangle of
    its own, which is why the runs are taken pairwise rather than counted.
    Raises on a diagonal run and on a width that has no centre on the DBU grid.
    """
    for chunk in SEGMENT_RE.split(body)[1:]:
        head = WIRE_RE.match(chunk)
        if head is None:
            raise ValueError(f"a wiring statement names no layer and width: {chunk[:60]}")
        layer, width = head.group(1), int(head.group(2))
        points = _points(chunk)
        for (x1, y1), (x2, y2) in zip(points, points[1:], strict=False):
            if not width or width % 2:
                raise ValueError(f"{layer} run at {x1} {y1} is {width} DBU wide")
            if x1 != x2 and y1 != y2:
                raise ValueError(f"{layer} run from {x1} {y1} to {x2} {y2} is diagonal")
            box = kdb.Box(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            yield layer, box.enlarged(0, width // 2) if y1 == y2 else box.enlarged(width // 2, 0)


def def_power(text: str, die: kdb.Box) -> list[tuple[str, kdb.Box]]:
    """Return the VDD and VSS rectangles that reach the die boundary, in DBU.

    Interior PDN survives `Def2GdsWrite`, so painting all of it back would double
    every stripe; only a segment touching the boundary is missing. Raises when
    the DEF carries no special nets, and when none of them reaches the edge,
    which means the fabric PDN step did not extend the grid and has to be re-run.
    """
    block = SPECIAL_RE.search(text)
    if block is None:
        raise ValueError("the DEF has no SPECIALNETS, so it carries no PDN to paint")
    boundary = [
        (layer, box)
        for entry in ENTRY_RE.finditer(block.group(1))
        if entry.group(1) in POWER_NETS
        for layer, box in _wires(entry.group(2))
        if box.left <= die.left
        or box.right >= die.right
        or box.bottom <= die.bottom
        or box.top >= die.top
    ]
    if not boundary:
        raise ValueError(
            f"no {'/'.join(POWER_NETS)} segment reaches {die}; extend the PDN to the die edge"
        )
    return boundary


def paint(def_path: Path, gds_path: Path, out_path: Path) -> str:
    """Write the GDS back out with its pin and boundary PDN geometry drawn in.

    Returns a one-line summary of what was drawn, for the caller to report.
    Refuses to write when a painted pin misses the routing on its own net, which
    is the only available evidence that the DEF and the GDS come from one run,
    and when the GDS already carries painted geometry.
    """
    text = read_def(def_path)
    pins = def_pins(text)
    power = def_power(text, die_area(text))

    layout = kdb.Layout()
    layout.read(str(gds_path))
    top, pin_cell = layout.cell(TOP_CELL), layout.cell(PIN_CELL)
    if top is None or pin_cell is None:
        raise ValueError(f"{gds_path} has no {TOP_CELL} over {PIN_CELL}, so iEDA did not write it")
    if not pin_cell.bbox().empty():
        raise ValueError(f"{gds_path} already has painted geometry")

    unrouted = []
    disconnected = []
    for name, (net, layer_name, box) in pins.items():
        index = layout.layer(GDS_LAYER[layer_name], 0)
        # The net's own routing lives in a cell named after the net, so the
        # overlap test stays local instead of sweeping the whole tile.
        net_cell = layout.cell(net)
        if net_cell is None:
            # Nothing drives this port, so the net carries no wiring at all; the
            # shape still has to exist for the tiles to abut.
            unrouted.append(name)
        elif (kdb.Region(net_cell.begin_shapes_rec(index)) & kdb.Region(box)).is_empty():
            disconnected.append(name)
        pin_cell.shapes(index).insert(box)

    if disconnected:
        raise ValueError(
            f"{len(disconnected)} routed pins miss their own wire: {sorted(disconnected)[:5]}"
        )

    for layer_name, box in power:
        pin_cell.shapes(layout.layer(GDS_LAYER[layer_name], 0)).insert(box)

    layout.write(str(out_path))
    return (
        f"painted {len(pins)} pins, {len(pins) - len(unrouted)} on routed nets, "
        f"{len(unrouted)} on nets nothing drives and {len(power)} boundary PDN runs, "
        f"{out_path} spans {top.dbbox()}"
    )
