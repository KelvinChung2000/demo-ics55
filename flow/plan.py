"""Turn the fabric model into the die sizes and pin offsets every tile is built to.

Two decisions are made here and nowhere else. The first is the die of each tile
type, which abutment forces to be one width per fabric column and one height per
fabric row; the shape of the reference `eFPGA_geometry.csv` run is kept and only
its scale changes, anchored on a measured ICS55 LUT. The second is the offset
of every scalar pin along its edge, which has to be agreed fabric-wide rather
than per tile: `LUT4x8_ha`'s East edge faces `LUT4x8_ha` in column 2 and
`RegFile` in column 3, so an offset chosen for one seam is binding on the other.

Three quantisations are not cosmetic. A row height that is an even multiple of
the `core7` site height keeps the `VDD`/`VSS` rail order running across a
horizontal seam. A row height that is a whole number of PDN stripe pitches makes
the `MACC` supertile's stripes meet those of the single-height tiles beside it. A
pin offset on the routing track grid was worth 3x in router runtime and the
difference between zero and 41 `metal_short` in the single-tile spike.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from flow.fabric import Bit, Fabric, Side
from flow import ioyaml
from flow.ioyaml import Rank

DBU = 1000  # DEF database units per micron, from the ICS55 tech LEF
SITE_WIDTH = 200  # DBU, core7
SITE_HEIGHT = 1400  # DBU, core7
TRACK_OFFSET = 100  # DBU, tech LEF OFFSET
TRACK_STEP = 200  # DBU, tech LEF PITCH
CORE_MARGIN = 2000  # DBU per side, ECC's Core.Margin default
PIN_WIDTH = 100  # DBU across the wire, the MET3/MET4 minimum width
STRIPE_WIDTH = 1000  # DBU, from ECC's pdn_generator defaults
STRIPE_OFFSET = 500  # DBU, from ECC's pdn_generator defaults
STRIPE_KEEPOUT = 200  # DBU either side of a stripe, the MET4 minimum spacing
SIDE_LAYER: dict[Side, str] = {"N": "MET4", "S": "MET4", "E": "MET3", "W": "MET3"}
# A row height must be a whole number of these for the PDN and the cell rows to
# survive abutment; 2 x SITE_HEIGHT because the rail order alternates per row.
HEIGHT_QUANTUM = 2 * SITE_HEIGHT


@dataclass(frozen=True)
class TilePlacement:
    """One instance, on the die rather than on the grid."""

    name: str
    tile_type: str
    column: int
    row: int  # FABulous grid row of the instance origin, growing southward
    x: int  # DBU, die coordinates of the macro's lower left corner
    y: int


@dataclass(frozen=True)
class PinPlacement:
    """One scalar pin of one tile type, on that type's own die."""

    tile_type: str
    name: str
    side: Side
    offset: int  # DBU along the edge, from the tile's own origin
    layer: str
    external: bool


@dataclass(frozen=True)
class Seam:
    """One boundary between two abutted tiles, and what has to cross it."""

    orientation: str  # "vertical" when the two tiles sit side by side
    at: int  # DBU, the shared coordinate
    low: int  # DBU, the extent of the shared edge
    high: int
    crossings: int


@dataclass
class Plan:
    column_width: list[int]  # DBU, one per fabric column
    row_height: list[int]  # DBU, one per fabric grid row
    column_x: list[int]  # DBU, die x of each column's left edge
    row_y: list[int]  # DBU, die y of each grid row's bottom edge
    tile_size: dict[str, tuple[int, int]]
    placements: list[TilePlacement]
    pins: dict[str, list[PinPlacement]]
    seams: list[Seam]
    stripe_pitch: int
    width: int
    height: int

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(_encode(self), indent=2) + "\n")

    @staticmethod
    def read(path: Path) -> "Plan":
        return _decode(json.loads(path.read_text()))

    def window(self, columns: range, rows: range) -> "Plan":
        """Return the part of the fabric inside a grid window, seams and all.

        The tiles keep their coordinates, so a window is the same layout the full
        fabric would have there, and a check on it is exact for the seams it
        contains. A supertile straddling the edge is refused rather than cut,
        since half a macro is not a thing that can be placed.
        """
        kept, cut = [], []
        for placement in self.placements:
            covered = range(placement.row, placement.row + self.rows_of(placement.tile_type))
            if placement.column not in columns:
                continue
            if all(row in rows for row in covered):
                kept.append(placement)
            elif any(row in rows for row in covered):
                cut.append(placement.name)
        if cut:
            raise ValueError(f"the window cuts {len(cut)} supertiles in half: {cut[:3]}")
        if not kept:
            raise ValueError(f"no tile sits in columns {columns} and rows {rows}")

        left = min(p.x for p in kept)
        right = max(p.x + self.tile_size[p.tile_type][0] for p in kept)
        bottom = min(p.y for p in kept)
        top = max(p.y + self.tile_size[p.tile_type][1] for p in kept)
        # An interior seam has a tile on both sides; one on the window's own edge
        # does not, so it is dropped rather than checked against nothing. A
        # vertical seam's `at` is an x and its band a y range, and a horizontal
        # seam's the other way round.
        def inside(seam: Seam) -> bool:
            if seam.orientation == "vertical":
                return left < seam.at < right and bottom <= seam.low and seam.high <= top
            return bottom < seam.at < top and left <= seam.low and seam.high <= right

        seams = [seam for seam in self.seams if inside(seam)]
        return Plan(
            column_width=self.column_width,
            row_height=self.row_height,
            column_x=self.column_x,
            row_y=self.row_y,
            tile_size={name: self.tile_size[name] for name in {p.tile_type for p in kept}},
            placements=kept,
            pins={name: self.pins[name] for name in {p.tile_type for p in kept}},
            seams=seams,
            stripe_pitch=self.stripe_pitch,
            # A window's tiles keep their fabric coordinates, so its width and
            # height are the far edge rather than the extent; everything that
            # reads them uses them as the far bound of a search from zero.
            width=right,
            height=top,
        )

    def rows_of(self, tile_type: str) -> int:
        """Return how many grid rows a tile type covers, from its planned height."""
        height = self.tile_size[tile_type][1]
        covered = {
            length
            for length in range(1, len(self.row_height) + 1)
            for start in range(len(self.row_height) - length + 1)
            if sum(self.row_height[start : start + length]) == height
        }
        if not covered:
            raise ValueError(f"{tile_type}'s height matches no run of rows")
        return min(covered)

    def pins_of(self, tile_type: str) -> dict[str, PinPlacement]:
        return {pin.name: pin for pin in self.pins[tile_type]}


def _encode(plan: Plan) -> dict:
    data = asdict(plan)
    data["tile_size"] = {name: list(size) for name, size in plan.tile_size.items()}
    return data


def _decode(data: dict) -> Plan:
    return Plan(
        column_width=data["column_width"],
        row_height=data["row_height"],
        column_x=data["column_x"],
        row_y=data["row_y"],
        tile_size={name: tuple(size) for name, size in data["tile_size"].items()},
        placements=[TilePlacement(**item) for item in data["placements"]],
        pins={name: [PinPlacement(**item) for item in pins] for name, pins in data["pins"].items()},
        seams=[Seam(**item) for item in data["seams"]],
        stripe_pitch=data["stripe_pitch"],
        width=data["width"],
        height=data["height"],
    )


def read_reference_geometry(path: Path) -> tuple[list[int], list[int]]:
    """Return the reference run's column widths and row heights, in its own units.

    `eFPGA_geometry.csv` records a completed FABulous run of this same fabric on
    another PDK. Only the proportions are taken from it; the scale comes from a
    measured ICS55 tile.
    """
    text = path.read_text()
    width = int(re.search(r"^Width,(\d+)", text, re.M).group(1))
    height = int(re.search(r"^Height,(\d+)", text, re.M).group(1))
    block = text[text.index("FABRIC_LOCS") :].split("\n\n")[0].splitlines()[1:]
    grid = [
        [tuple(int(v) for v in cell.split("/")) if "/" in cell else None for cell in line.split(",")]
        for line in block
        if line.strip()
    ]
    xs = [next(cell[0] for cell in column if cell) for column in zip(*grid, strict=True)]
    ys = [next(cell[1] for cell in row if cell) for row in grid]
    widths = [b - a for a, b in zip(xs, xs[1:] + [width], strict=True)]
    heights = [b - a for a, b in zip(ys, ys[1:] + [height], strict=True)]
    return widths, heights


def _quantise(value: float, quantum: int) -> int:
    """Round `value` DBU up to the next whole `quantum`."""
    return -(-int(round(value)) // quantum) * quantum


def stripe_keepout(extent: int, pitch: int) -> list[tuple[int, int]]:
    """Return the offsets a MET4 pin may not take, because a power stripe is there.

    The N and S pins share MET4 with the vertical PDN stripes, and extending
    those stripes to the die edge for abutment runs them straight through the
    pin row. A stripe centre is the core's low edge plus the generator's offset
    plus half the stripe width, so the pattern is the same in every tile
    whatever its width. The step is half the configured pitch, because
    `pdn_generator` states the pitch of one power net and iEDA interleaves `VDD`
    and `VSS`, so a tile configured at 16 um carries a stripe every 8 um.
    """
    first = CORE_MARGIN + STRIPE_OFFSET + STRIPE_WIDTH // 2
    guard = STRIPE_WIDTH // 2 + STRIPE_KEEPOUT
    return [
        (centre - guard, centre + guard)
        for centre in range(first, extent - CORE_MARGIN, pitch // 2)
    ]


def core_edge(extent: int, site: int) -> tuple[int, int]:
    """Return the core's two bounds along an edge of a die `extent` DBU long.

    The core is the die inset by `CORE_MARGIN`, but its far side is then pulled
    back to a whole number of sites, because iEDA lays the standard-cell rows
    from the near margin and stops at the last one that fits: a 112 um tile has
    77 core7 rows and a core that ends at 109.8 rather than at 110.
    """
    return CORE_MARGIN, CORE_MARGIN + (extent - 2 * CORE_MARGIN) // site * site


def _tracks(
    low: int, high: int, count: int, blocked: list[tuple[int, int]], site: int
) -> list[int]:
    """Return `count` track-snapped offsets spread between the die edges `low` and `high`.

    Snapping to the routing grid is not cosmetic: in the single-tile spike it cut
    routing from 81 s to 27 s and took DRC from 41 `metal_short` to zero.

    ECC's IO placer rejects an offset that is not exactly on a track of the pin's
    own layer, and rejects a pin shape that leaves the core, so the usable range
    is `core_edge`'s pulled in by the pin's half-width.
    """
    half = PIN_WIDTH // 2
    core_low, core_high = core_edge(high - low, site)
    first = -(-(low + core_low + half - TRACK_OFFSET) // TRACK_STEP)
    last = (low + core_high - (PIN_WIDTH - half) - TRACK_OFFSET) // TRACK_STEP
    grid = (TRACK_OFFSET + TRACK_STEP * index for index in range(first, last + 1))
    candidates = [
        offset for offset in grid if not any(lo <= offset <= hi for lo, hi in blocked)
    ]
    if len(candidates) < count:
        raise ValueError(
            f"{count} pins need {count} tracks between {low} and {high}, "
            f"{len(candidates)} are free of the power stripes"
        )
    if count == 1:
        return [candidates[len(candidates) // 2]]
    # A pin can only land on a track, so the choice is which track indices to
    # take, not which coordinates. The stride is the widest that still fits
    # every pin, which keeps neighbouring pins as far apart as the edge allows,
    # and the block it spans is then centred: the corners route worst and the
    # core-edge rule has already made them unusable on both sides.
    stride = (len(candidates) - 1) // (count - 1)
    span = (count - 1) * stride
    middle = (low + high) // 2
    start = min(
        range(len(candidates) - span),
        key=lambda first: abs(candidates[first] + candidates[first + span] - 2 * middle),
    )
    return [candidates[start + index * stride] for index in range(count)]


class _Union:
    """Union-find over scalar pins, so one offset can serve a whole link chain."""

    def __init__(self) -> None:
        self.parent: dict[Bit, Bit] = {}

    def find(self, item: Bit) -> Bit:
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: Bit, right: Bit) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def _components(fabric: Fabric) -> dict[Bit, list[Bit]]:
    """Group every scalar pin with the pins it must share an offset with."""
    union = _Union()
    for tile in fabric.tile_types.values():
        for bit in tile.bits():
            union.find(bit)
    for link in fabric.links:
        union.union(link.driver, link.receiver)
    groups: dict[Bit, list[Bit]] = {}
    for bit in list(union.parent):
        groups.setdefault(union.find(bit), []).append(bit)
    return groups


def _lane_groups(members: dict[int, set[int]]) -> list[list[int]]:
    """Group lanes that share at least one component, so slots stay distinct there.

    Two components may reuse one offset when no tile edge ever carries both. A
    terminator row and a core row share no component, so the whole offset range
    is available to each; the core rows all share `LUT4x8_ha`'s and must not.
    """
    parent: dict[int, int] = {lane: lane for lane in members}

    def find(lane: int) -> int:
        while parent[lane] != lane:
            parent[lane] = parent[parent[lane]]
            lane = parent[lane]
        return lane

    by_component: dict[int, list[int]] = {}
    for lane, components in members.items():
        for component in components:
            by_component.setdefault(component, []).append(lane)
    for lanes in by_component.values():
        for lane in lanes[1:]:
            a, b = find(lanes[0]), find(lane)
            if a != b:
                parent[b] = a
    groups: dict[int, list[int]] = {}
    for lane in members:
        groups.setdefault(find(lane), []).append(lane)
    return [sorted(lanes) for lanes in groups.values()]


def _assign(
    fabric: Fabric,
    groups: dict[Bit, list[Bit]],
    vertical: bool,
    extent: dict[int, int],
    lanes_of: dict[Bit, set[int]],
    stripe_pitch: int,
    ranks: dict[Bit, "Rank"],
) -> dict[Bit, int]:
    """Give every pin on one seam class an offset, shared across its component."""
    # Only a pin that meets another tile needs an offset agreed fabric-wide. A
    # boundary pin has no partner, so numbering it here would spend a slot every
    # tile type has to leave empty: on this fabric that is 126 of 254 slots per
    # vertical edge, which halves the spacing and is what iEDA's own placer,
    # spacing its pins three to four tracks apart, never has to do.
    wanted = {
        root: members
        for root, members in groups.items()
        if (fabric.bit_side(members[0]).side in ("E", "W")) == vertical
        and any(not fabric.bit_side(bit).external for bit in members)
    }
    for root, members in wanted.items():
        mixed = {fabric.bit_side(bit).side for bit in members}
        if not mixed <= ({"E", "W"} if vertical else {"N", "S"}):
            raise ValueError(f"component of {root} spans edges {sorted(mixed)}")

    def order(members: list[Bit]) -> tuple[int, int]:
        """Sort key placing a component where FABulous's edge order puts it.

        A union-find root is whichever pin the merge happened to reach first,
        so ordering by it scatters `E1BEG_0` and `E1BEG_1` to opposite ends of
        the edge and every wire from there to the switch matrix detours; the
        single-tile spike put a contiguous bus at 3x in router runtime. The
        rank comes from `io_pin_order.yaml` rather than from the port name, so
        the order is FABulous's rather than this flow's guess at it.

        Every member agrees on the rank, because facing sides list the same
        buses at the same positions; `min` picks one rather than arbitrating.
        """
        keys = {ranks[bit].key for bit in members}
        if len(keys) > 1:
            raise ValueError(
                f"the pins of one component disagree on their edge order: "
                f"{sorted((bit.tile_type, bit.name, ranks[bit].key) for bit in members)[:4]}"
            )
        return keys.pop()

    index_of = {
        root: index
        for index, root in enumerate(sorted(wanted, key=lambda root: order(wanted[root])))
    }
    lane_members: dict[int, set[int]] = {lane: set() for lane in extent}
    for root, members in wanted.items():
        for bit in members:
            for lane in lanes_of[bit]:
                lane_members[lane].add(index_of[root])

    # A vertical seam runs along the die's y, where the core ends on a row
    # boundary; a horizontal one along x, where it ends on a site boundary.
    site = SITE_HEIGHT if vertical else SITE_WIDTH
    offsets: dict[Bit, int] = {}
    for lanes in _lane_groups(lane_members):
        components = sorted({index for lane in lanes for index in lane_members[lane]})
        bound = min(extent[lane] for lane in lanes)
        # Only the N and S pins share a layer with the PDN stripes; the E and W
        # pins are on MET3, which the stripes never occupy.
        blocked = [] if vertical else stripe_keepout(bound, stripe_pitch)
        slots = _tracks(0, bound, len(components), blocked, site)
        by_index = {index_of[root]: members for root, members in wanted.items()}
        for slot, index in zip(slots, components, strict=True):
            for bit in by_index[index]:
                offsets[bit] = slot
    return offsets


def _boundary_offsets(
    *,
    fabric: Fabric,
    tile,
    shared: dict[Bit, int],
    width: int,
    height: int,
    stripe_pitch: int,
    ranks: dict[Bit, "Rank"],
) -> dict[Bit, int]:
    """Place a tile's boundary pins in the space its shared pins leave free.

    A pin that leaves the fabric answers to nothing on the far side, so it is
    placed on its own tile's edge, on tracks no shared pin and no power stripe
    already holds.
    """
    placed: dict[Bit, int] = {}
    for side in ("N", "E", "S", "W"):
        vertical = side in ("E", "W")
        outside = [
            bit
            for bit in tile.bits()
            if fabric.bit_side(bit).side == side and bit not in shared
        ]
        if not outside:
            continue
        taken = {
            shared[bit]
            for bit in tile.bits()
            if fabric.bit_side(bit).side == side and bit in shared
        }
        extent = height if vertical else width
        site = SITE_HEIGHT if vertical else SITE_WIDTH
        blocked = [(offset, offset) for offset in taken]
        if not vertical:
            blocked += stripe_keepout(extent, stripe_pitch)
        # The same order the shared pins take, for the same reason.
        outside.sort(key=lambda bit: ranks[bit].key)
        tracks = _tracks(0, extent, len(outside), blocked, site)
        for bit, offset in zip(outside, tracks, strict=True):
            placed[bit] = offset
    return placed


def build_plan(fabric: Fabric, geometry: Path, anchor_micron: float, anchor_type: str) -> Plan:
    """Size every tile and place every pin, from the fabric and one measured tile."""
    widths, heights = read_reference_geometry(geometry)
    if len(widths) != fabric.columns or len(heights) != fabric.rows:
        raise ValueError(
            f"{geometry} describes a {len(widths)}x{len(heights)} fabric, "
            f"eFPGA.v a {fabric.columns}x{fabric.rows} one"
        )
    anchor_columns = fabric.occupied_columns(anchor_type)
    anchor_rows = fabric.occupied_rows(anchor_type)
    reference_width = {widths[column] for column in anchor_columns}
    reference_height = {heights[row] for row in anchor_rows}
    if len(reference_width) != 1 or len(reference_height) != 1:
        raise ValueError(f"{anchor_type} does not have one reference size to anchor on")
    anchor = int(anchor_micron * DBU)
    x_scale = anchor / reference_width.pop()
    y_scale = anchor / reference_height.pop()

    column_width = [_quantise(width * x_scale, SITE_WIDTH) for width in widths]
    row_height = [_quantise(height * y_scale, HEIGHT_QUANTUM) for height in heights]

    # The supertile's stripes only meet its neighbours' if a core row is a whole
    # number of pitches; the core row is the tallest row and every stripe pitch
    # divides it, so derive the pitch from it rather than carrying ECC's default.
    core_height = max(row_height)
    stripe_pitch = core_height // round(core_height / 16000)
    # The pitch iEDA is configured with is the pitch of one power net, and VDD
    # and VSS interleave, so the supertile's stripes meet its neighbours' only if
    # the row divides by the half pitch.
    if core_height % (stripe_pitch // 2):
        raise ValueError(
            f"a {core_height} DBU row is not a whole number of {stripe_pitch // 2} DBU stripe "
            "spacings, so the supertile's power stripes would miss its neighbours'. "
            "Choose a different --anchor-micron."
        )

    column_x, x = [], 0
    for width in column_width:
        column_x.append(x)
        x += width
    # Grid rows grow southward and die rows northward, so the row at grid index 0
    # sits at the top of the die.
    row_y, y = [0] * len(row_height), 0
    for grid_row in reversed(range(len(row_height))):
        row_y[grid_row] = y
        y += row_height[grid_row]

    tile_size: dict[str, tuple[int, int]] = {}
    for name, tile in fabric.tile_types.items():
        column_widths = {column_width[column] for column in fabric.occupied_columns(name)}
        rows = sorted(fabric.occupied_rows(name))
        if len(column_widths) != 1:
            raise ValueError(f"{name} sits in columns of {len(column_widths)} different widths")
        spans = {
            sum(row_height[instance.y + offset] for offset in range(tile.rows))
            for instance in fabric.placements()
            if instance.tile_type == name
        }
        if len(spans) != 1:
            raise ValueError(f"{name} spans rows of {len(spans)} different heights")
        tile_size[name] = (column_widths.pop(), spans.pop())

    placements = [
        TilePlacement(
            name=instance.name,
            tile_type=instance.tile_type,
            column=instance.x,
            row=instance.y,
            x=column_x[instance.x],
            y=row_y[instance.y + fabric.tile_types[instance.tile_type].rows - 1],
        )
        for instance in fabric.placements()
    ]

    groups = _components(fabric)
    ranks = {
        bit: rank
        for name in fabric.tile_types
        for bit, rank in ioyaml.read(fabric, name, geometry.parent).items()
    }
    # A pin's offset is bounded by the narrowest column, or shortest row, any
    # tile carrying it ever sits in.
    row_lanes: dict[Bit, set[int]] = {}
    column_lanes: dict[Bit, set[int]] = {}
    for name, tile in fabric.tile_types.items():
        columns = fabric.occupied_columns(name)
        for bit in tile.bits():
            port = tile.ports[fabric.port_of(bit)]
            rows = {
                instance.y + port.sub_row
                for instance in fabric.placements()
                if instance.tile_type == name
            }
            row_lanes[bit] = rows
            column_lanes[bit] = columns
    vertical = _assign(
        fabric,
        groups,
        True,
        {row: row_height[row] for row in range(fabric.rows)},
        row_lanes,
        stripe_pitch,
        ranks,
    )
    horizontal = _assign(
        fabric,
        groups,
        False,
        {column: column_width[column] for column in range(fabric.columns)},
        column_lanes,
        stripe_pitch,
        ranks,
    )
    offsets = vertical | horizontal

    pins: dict[str, list[PinPlacement]] = {}
    for name, tile in fabric.tile_types.items():
        offsets |= _boundary_offsets(
            fabric=fabric,
            tile=tile,
            shared=offsets,
            width=tile_size[name][0],
            height=tile_size[name][1],
            stripe_pitch=stripe_pitch,
            ranks=ranks,
        )
        placed = []
        for bit in tile.bits():
            side = fabric.bit_side(bit)
            port = tile.ports[fabric.port_of(bit)]
            offset = offsets[bit]
            if side.side in ("E", "W"):
                # A supertile's pin sits in the slice its sub-row names, and the
                # first sub-row is the northernmost, so it is the topmost slice.
                offset += sum(
                    row_height[row]
                    for row in sorted(fabric.occupied_rows(name))[: tile.rows - 1 - port.sub_row]
                )
            placed.append(
                PinPlacement(
                    tile_type=name,
                    name=bit.name,
                    side=side.side,
                    offset=offset,
                    layer=SIDE_LAYER[side.side],
                    external=side.external,
                )
            )
        pins[name] = placed

    return Plan(
        column_width=column_width,
        row_height=row_height,
        column_x=column_x,
        row_y=row_y,
        tile_size=tile_size,
        placements=placements,
        pins=pins,
        seams=_seams(fabric, column_x, row_y, column_width, row_height),
        stripe_pitch=stripe_pitch,
        width=sum(column_width),
        height=sum(row_height),
    )


def _seams(
    fabric: Fabric,
    column_x: list[int],
    row_y: list[int],
    column_width: list[int],
    row_height: list[int],
) -> list[Seam]:
    """Enumerate every abutment boundary and how many wires must cross it."""
    counts: dict[tuple[str, int, int, int], int] = {}
    for link in fabric.links:
        (dx, dy), (rx, ry) = link.driver_at, link.receiver_at
        if link.vertical_seam:
            column = max(dx, rx)
            key = ("vertical", column_x[column], row_y[dy], row_y[dy] + row_height[dy])
        else:
            row = min(dy, ry)  # the northern of the two, so the seam is its bottom edge
            key = ("horizontal", row_y[row], column_x[dx], column_x[dx] + column_width[dx])
        counts[key] = counts.get(key, 0) + 1
    return [
        Seam(orientation=orientation, at=at, low=low, high=high, crossings=crossings)
        for (orientation, at, low, high), crossings in sorted(counts.items())
    ]
