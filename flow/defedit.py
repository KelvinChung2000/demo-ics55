"""Stretch a tile's PDN to its die edge so the tile can abut its neighbours.

The PDN stops at the core box, 2 um inside the die on every side, so two tiles
placed at the die pitch have a 4 um strip between them carrying no power metal
at all. `pdn_generator` has no setting for this, so the rails and stripes are
stretched in the DEF that `postFloorplan` writes: `create_db_engine` falls back
to `read_def` when the previous step's binary database is missing, and every
later step then reads what is written here.

Pin placement used to be fixed the same way, and is not any more. ECC's IO
placer takes a placement file, so `flow.ioplace` hands it the plan before
`postFloorplan` runs and iEDA places the pins itself.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path

DIEAREA_RE = re.compile(
    r"DIEAREA\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)"
)
PINS_RE = re.compile(r"^PINS \d+ ;\n(.*?)^END PINS", re.S | re.M)
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
            "Check that postFloorplan ran its PDN subflow."
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
    size: tuple[int, int],
    *,
    extend_power: bool = True,
) -> str:
    """Stretch one tile's PDN to its die edge, having checked the die is the planned one.

    `extend_power` is a control rather than a preference. Extending the PDN is
    what makes an abutted fabric powered, but it also puts wide metal along all
    four die edges where the router previously had clear space, so leaving it
    off attributes a routing failure to one or the other.
    """
    text = read_def(def_path)
    die = die_of(text)
    if (die.width, die.height) != size:
        raise ValueError(
            f"{def_path} has a {die.width}x{die.height} die, the plan says {size[0]}x{size[1]}. "
            "Set floorplan.die_builder.die_size before running preFloorplan."
        )
    extended = 0
    if extend_power:
        text, extended = extend_pdn(text, die)
    with def_path.open("rb") as handle:
        gzipped = handle.read(2) == b"\x1f\x8b"
    write_def(out_path, text, gzipped=gzipped)
    return f"{extended} power segments extended to the die edge"
