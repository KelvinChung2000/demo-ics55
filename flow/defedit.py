"""Rewrite a tile's floorplan DEF so the tile can abut its neighbours.

Two things iEDA writes are wrong for abutment and neither is reachable through
configuration. `ifp::IOPlacer` is fully automatic: it cuts the pin list into four
index-quarters and hands them to the four edges in turn, so a bus is torn across
three edges and a driver never faces the receiver it feeds. And the PDN stops at
the core box, 2 um inside the die on every side, so two tiles placed at the die
pitch have a 4 um strip between them carrying no power metal at all.

Both are fixed in the DEF rather than in iEDA, because `create_db_engine` falls
back to `read_def` when the previous step's binary database is missing, and every
later step then reads what is written here. The pins are written `+ FIXED`, which
is the status that survived to the routed DEF in the one spike workspace that
kept its placement.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path

from flow.plan import PIN_DEPTH, PIN_WIDTH, PinPlacement, Side

DIEAREA_RE = re.compile(
    r"DIEAREA\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)"
)
PINS_RE = re.compile(r"^PINS \d+ ;\n(.*?)^END PINS", re.S | re.M)
PIN_ENTRY_RE = re.compile(
    r"^\s*- (\S+) \+ NET (\S+) \+ DIRECTION (\S+)\s*\+ USE (\S+)", re.M
)
SPECIALNETS_RE = re.compile(r"^SPECIALNETS \d+ ;\n(.*?)^END SPECIALNETS", re.S | re.M)
SEGMENT_RE = re.compile(
    r"((?:ROUTED|NEW) (\w+) (\d+) \+ SHAPE \w+ )"
    r"\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)\s*\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)"
)


@dataclass(frozen=True)
class Die:
    llx: int
    lly: int
    urx: int
    ury: int

    @property
    def width(self) -> int:
        return self.urx - self.llx

    @property
    def height(self) -> int:
        return self.ury - self.lly


def read_def(path: Path) -> str:
    """Read a DEF whether or not it is really gzipped.

    ECC names every output `.def.gz` and compresses only some of them, so the
    suffix cannot be trusted and the magic number decides.
    """
    with path.open("rb") as handle:
        gzipped = handle.read(2) == b"\x1f\x8b"
    opener = gzip.open if gzipped else open
    with opener(path, "rt") as handle:
        return handle.read()


def write_def(path: Path, text: str, *, gzipped: bool) -> None:
    opener = gzip.open if gzipped else open
    with opener(path, "wt") as handle:
        handle.write(text)


def die_of(text: str) -> Die:
    match = DIEAREA_RE.search(text)
    if match is None:
        raise ValueError("the DEF has no DIEAREA")
    return Die(*(int(value) for value in match.groups()))


def _geometry(side: Side, offset: int, die: Die) -> tuple[str, int, int]:
    """Return the pin's rectangle relative to its anchor, and the anchor itself."""
    half = PIN_WIDTH // 2
    match side:
        case "N":
            return f"( -{half} -{PIN_DEPTH} ) ( {half} 0 )", die.llx + offset, die.ury
        case "S":
            return f"( -{half} 0 ) ( {half} {PIN_DEPTH} )", die.llx + offset, die.lly
        case "E":
            return f"( -{PIN_DEPTH} -{half} ) ( 0 {half} )", die.urx, die.lly + offset
        case "W":
            return f"( 0 -{half} ) ( {PIN_DEPTH} {half} )", die.llx, die.lly + offset
    raise ValueError(f"{side} is not an edge")


def rewrite_pins(
    text: str, placements: dict[str, PinPlacement], die: Die, status: str = "FIXED"
) -> str:
    """Replace the PINS section with the fabric-wide plan's offsets.

    Raises if the DEF and the plan disagree about which pins exist, which is the
    symptom of a tile whose elaborated bus widths differ from its Verilog.
    """
    block = PINS_RE.search(text)
    if block is None:
        raise ValueError("the DEF has no PINS section")
    entries = PIN_ENTRY_RE.findall(block.group(1))
    declared = int(re.search(r"^PINS (\d+) ;", text, re.M).group(1))
    if len(entries) != declared:
        raise ValueError(f"the PINS section declares {declared} pins and lists {len(entries)}")
    names = {name for name, *_ in entries}
    if names != placements.keys():
        missing = sorted(names - placements.keys())[:5]
        extra = sorted(placements.keys() - names)[:5]
        raise ValueError(
            f"the DEF and the plan disagree on {len(names ^ placements.keys())} pins. "
            f"In the DEF only: {missing}. In the plan only: {extra}."
        )

    lines = [f"PINS {len(entries)} ;"]
    for name, net, direction, use in entries:
        placement = placements[name]
        rectangle, x, y = _geometry(placement.side, placement.offset, die)
        lines.append(f" - {name} + NET {net} + DIRECTION {direction}  + USE {use}")
        lines.append(f" + LAYER {placement.layer} {rectangle} + {status} ( {x} {y} ) N")
        lines.append(" ;")
    lines.append("END PINS")
    return text[: block.start()] + "\n".join(lines) + "\n" + text[block.end() :]


def extend_pdn(text: str, die: Die) -> tuple[str, int]:
    """Stretch the full-length power rails and stripes out to the die boundary.

    Only segments already spanning the whole core are touched. The via stacks
    that connect a rail to a stripe are single points with a via name and the
    short MET2 and MET3 pads beside them span nothing, so neither is matched.
    """
    block = SPECIALNETS_RE.search(text)
    if block is None:
        raise ValueError("the DEF has no SPECIALNETS section")
    body = block.group(1)

    spans = [
        (int(x1), int(y1), int(x2) if x2 != "*" else None, int(y2) if y2 != "*" else None)
        for _, _, width, x1, y1, x2, y2 in SEGMENT_RE.findall(body)
        if int(width) > 0 and x1 != "*" and y1 != "*"
    ]
    horizontal = max((x2 - x1 for x1, _, x2, y2 in spans if y2 is None), default=0)
    vertical = max((y2 - y1 for _, y1, x2, y2 in spans if x2 is None), default=0)
    if not horizontal or not vertical:
        raise ValueError(
            "the PDN has no full-length rail or stripe, so nothing can be extended. "
            "Check that Floorplan ran its PDN subflow."
        )

    extended = 0

    def stretch(match: re.Match[str]) -> str:
        nonlocal extended
        head, _, width, x1, y1, x2, y2 = match.groups()
        if int(width) == 0 or x1 == "*" or y1 == "*":
            return match.group(0)
        if y2 == "*" and x2 != "*" and int(x2) - int(x1) == horizontal:
            extended += 1
            return f"{head}( {die.llx} {y1} ) ( {die.urx} * )"
        if x2 == "*" and y2 != "*" and int(y2) - int(y1) == vertical:
            extended += 1
            return f"{head}( {x1} {die.lly} ) ( * {die.ury} )"
        return match.group(0)

    return text[: block.start(1)] + SEGMENT_RE.sub(stretch, body) + text[block.end(1) :], extended


def prepare(
    def_path: Path,
    out_path: Path,
    pins: list[PinPlacement],
    size: tuple[int, int],
    *,
    extend_power: bool = True,
    status: str = "FIXED",
) -> str:
    """Rewrite one tile's floorplan DEF in place of iEDA's own pins and PDN extent.

    `extend_power` and `status` are controls rather than preferences. Extending
    the PDN is what makes an abutted fabric powered, but it also puts wide metal
    along all four die edges where the router previously had clear space. And
    FINDINGS.md leaves open whether `+ FIXED` is what kept a pin placement from
    reverting at routing, or whether the single uninterrupted invocation did it;
    `PLACED` is what `ifp::IOPlacer` writes itself.
    """
    text = read_def(def_path)
    die = die_of(text)
    if (die.width, die.height) != size:
        raise ValueError(
            f"{def_path} has a {die.width}x{die.height} die, the plan says {size[0]}x{size[1]}. "
            "Patch fp_default_config.json before running Floorplan."
        )
    text = rewrite_pins(text, {pin.name: pin for pin in pins}, die, status)
    extended = 0
    if extend_power:
        text, extended = extend_pdn(text, die)
    with def_path.open("rb") as handle:
        gzipped = handle.read(2) == b"\x1f\x8b"
    write_def(out_path, text, gzipped=gzipped)
    return f"{len(pins)} pins fixed, {extended} power segments extended to the die edge"
