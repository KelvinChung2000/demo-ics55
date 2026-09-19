"""Read a FABulous fabric out of its generated Verilog, in the terms ECC needs.

Everything downstream of this module -- the die plan, the pin plan, the DEF
rewrite and the stitch -- is driven by three facts that only `eFPGA.v` and the
tile sources carry together: which tile type sits at each grid position, which
scalar pin of one tile type meets which scalar pin of its neighbour, and which
edge of the die each pin belongs on. FABulous already fixes all three; the job
here is to recover them rather than restate them in a hand-written table, which
is what the single-tile spike did and what stops working the moment a row holds
more than one tile type.

Two conventions are inherited from FABulous and are not negotiable. Grid `Y`
grows southward while die `y` grows northward, so a row index is flipped once,
in `Fabric.row_of_die`. A supertile's ports carry a `Tile_X0Y<k>` prefix naming
the sub-row they belong to, so the pin of sub-row `k` sits in the `k`-th slice
of a macro that is `rows` slices tall.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Side = Literal["N", "E", "S", "W"]
OPPOSITE: dict[Side, Side] = {"N": "S", "S": "N", "E": "W", "W": "E"}
VERTICAL_SEAM_SIDES: tuple[Side, Side] = ("E", "W")

# A grid step, in FABulous coordinates, to the edge a pin arriving from that
# step must sit on. `Y` grows southward, so a wire handed up from `Y + 1` enters
# through the South edge however the port is named: `N1END` is a north-travelling
# wire and sits on the South edge of the tile receiving it.
STEP_TO_SIDE: dict[tuple[int, int], Side] = {(0, 1): "S", (0, -1): "N", (1, 0): "E", (-1, 0): "W"}

INSTANCE_RE = re.compile(
    r"\(\*\s*keep\s*\*\)\s*(\w+)\b[^;]*?"  # module type, then any parameter block
    r"\b(Tile_X(\d+)Y(\d+)_\1)\s*\(\s*\n(.*?)^\s*\)\s*;",
    re.S | re.M,
)
CONNECTION_RE = re.compile(r"\.(\w+)\(\s*(\w+)\s*\)")
PORT_RE = re.compile(
    r"^\s*(input|output|inout)\s+(?:wire\s+|reg\s+)?"
    r"(?:\[\s*([^\]:]+?)\s*:\s*([^\]:]+?)\s*\]\s*)?"
    r"(\w+)\s*[,)]?\s*(?://(.*))?$"
)
PARAMETER_RE = re.compile(r"^\s*parameter\s+(?:\[[^\]]*\]\s*)?(\w+)\s*=\s*([^,\n]+?)\s*,?\s*$", re.M)
TILE_PORT_RE = re.compile(r"TilePort\(\{(\w)\}")
NET_OWNER_RE = re.compile(r"^Tile_X(\d+)Y(\d+)_(.+)$")
SUB_ROW_RE = re.compile(r"^Tile_X0Y(\d+)_(.+)$")


@dataclass(frozen=True)
class Bit:
    """One scalar pin of one tile type, named as iEDA writes it into the DEF.

    iEDA bit-blasts `E1BEG[0]` to `E1BEG_0`, so the name here is the DEF name
    and not the Verilog one. The trailing underscore the older ECC wrote is
    gone: `E1BEG_0_` is what the placer rejects now.
    """

    tile_type: str
    name: str


@dataclass(frozen=True)
class Port:
    """A tile type's port, with the die edge it must be placed on."""

    name: str
    direction: Literal["input", "output"]
    width: int
    annotated_side: Side | None  # from FABulous's `//TilePort({E} ...)` comment
    sub_row: int  # 0 for a plain tile, the sub-row index within a supertile
    vectored: bool  # declared with a range, even a one-bit `[0:0]` one

    def bits(self, tile_type: str) -> list[Bit]:
        """Return the port's scalar DEF pins, low bit first.

        Width alone does not decide the name. iEDA keeps the index on a port
        declared `[0:0]`, so `Ci` reaches the DEF as `Ci_0` while the genuinely
        scalar `UserCLK` does not.
        """
        if not self.vectored:
            return [Bit(tile_type, self.name)]
        return [Bit(tile_type, f"{self.name}_{index}") for index in range(self.width)]


@dataclass(frozen=True)
class TileType:
    """A hardened macro: one tile, or one supertile spanning `rows` grid rows."""

    name: str
    source: Path
    ports: dict[str, Port]
    rows: int

    def bits(self) -> list[Bit]:
        return [bit for port in self.ports.values() for bit in port.bits(self.name)]

    def clock_port(self) -> str:
        """Return the port this tile takes its clock in on, as an SDC name.

        The classic tile library has no per-tile `UserCLK`. A pad drives the
        `SW_term` global buffers through `W_GBUF_FEED_END`, which send the clock
        up each column on `N_GBUF_BEG` and along the bottom row on `E_GBUF_BEG`,
        so a tile sees it on `N_GBUF_END` unless it is itself in that bottom row
        and sees `E_GBUF_END`. Upstream's own tile configs name `N_GBUF_END[0]`
        for every tile including the five that have no such port, which
        constrains nothing there rather than failing.

        The bit is named flat. ECC writes its SDC as Tcl and interpolates the
        clock port unquoted, so a bracketed `N_GBUF_END[0]` is read as a command
        substitution, `all_inputs_wo_clk` is never set and iSTA stops on the
        constraint file it wrote itself.

        A supertile prefixes each port with the sub-tile it belongs to, so the
        match is on the suffix and the lowest-numbered sub-tile carrying the
        port wins, which is the one FABulous numbers from the top down.
        """
        for candidate in ("N_GBUF_END", "E_GBUF_END", "W_GBUF_FEED_END"):
            carried = sorted(
                port.name
                for port in self.ports.values()
                if port.direction == "input"
                and (port.name == candidate or port.name.endswith(f"_{candidate}"))
            )
            if carried:
                return f"{carried[0]}_0"
        raise ValueError(
            f"{self.name} has no global-buffer clock input, so no clock can be "
            f"constrained on it; its inputs are "
            f"{sorted(p.name for p in self.ports.values() if p.direction == 'input')}"
        )


@dataclass(frozen=True)
class Instance:
    """One placed tile. `y` is the FABulous grid row, growing southward."""

    name: str
    tile_type: str
    x: int
    y: int
    connections: dict[str, str]


@dataclass(frozen=True)
class Link:
    """One scalar wire crossing one seam, as `eFPGA.v` declares it."""

    driver: Bit
    receiver: Bit
    driver_side: Side
    driver_sub_row: int
    receiver_sub_row: int
    # Effective grid rows and columns, sub-rows already folded in, so a seam can
    # be located without going back to the instance.
    driver_at: tuple[int, int]
    receiver_at: tuple[int, int]

    @property
    def receiver_side(self) -> Side:
        return OPPOSITE[self.driver_side]

    @property
    def vertical_seam(self) -> bool:
        """True when the link crosses a column boundary, so its slot is a `y`."""
        return self.driver_side in VERTICAL_SEAM_SIDES


@dataclass(frozen=True)
class PortSide:
    """Where one port of one tile type sits, and whether it leaves the fabric."""

    side: Side
    external: bool


@dataclass
class Fabric:
    tile_types: dict[str, TileType]
    instances: dict[tuple[int, int], Instance]
    links: list[Link]
    sides: dict[tuple[str, str], PortSide]
    columns: int
    rows: int

    def die_row(self, y: int) -> int:
        """Convert a FABulous grid row to a die row, counted from the bottom."""
        return self.rows - 1 - y

    def side_of(self, tile_type: str, port: str) -> PortSide:
        placement = self.sides.get((tile_type, port))
        if placement is None:
            raise KeyError(f"{tile_type}.{port} was never given an edge")
        return placement

    def bit_side(self, bit: Bit) -> PortSide:
        return self.side_of(bit.tile_type, self.port_of(bit))

    def port_of(self, bit: Bit) -> str:
        """Recover the port a scalar DEF pin came from."""
        tile = self.tile_types[bit.tile_type]
        if bit.name in tile.ports:
            return bit.name
        stem = re.match(r"^(.*)_\d+$", bit.name)
        if stem is None or stem.group(1) not in tile.ports:
            raise KeyError(f"{bit.name} is not a port of {bit.tile_type}")
        return stem.group(1)

    def occupied_rows(self, tile_type: str) -> set[int]:
        """Every grid row any instance of `tile_type` covers, sub-rows included."""
        height = self.tile_types[tile_type].rows
        return {
            instance.y + offset
            for instance in self.instances.values()
            if instance.tile_type == tile_type
            for offset in range(height)
        }

    def occupied_columns(self, tile_type: str) -> set[int]:
        return {i.x for i in self.instances.values() if i.tile_type == tile_type}

    def placements(self) -> list[Instance]:
        """Each instance once, keyed by its own origin rather than every row it covers."""
        seen: dict[str, Instance] = {i.name: i for i in self.instances.values()}
        return sorted(seen.values(), key=lambda i: (i.y, i.x))


def _evaluate(expression: str, parameters: dict[str, int]) -> int:
    """Evaluate a Verilog bound such as `FrameBitsPerRow-1` against the defaults."""
    cleaned = expression.strip()
    if re.fullmatch(r"-?\d+", cleaned):
        return int(cleaned)
    if not re.fullmatch(r"[\w\s+\-*/()]+", cleaned):
        raise ValueError(f"cannot evaluate port bound {expression!r}")
    return int(eval(cleaned, {"__builtins__": {}}, parameters))  # noqa: S307


def _mask_comments(text: str) -> str:
    """Blank out line comments, keeping every offset, so brackets balance.

    A `//TilePort({E} ...)` annotation carries brackets of its own; counting
    them would end a port list in the middle.
    """
    return re.sub(r"//[^\n]*", lambda match: " " * len(match.group(0)), text)


def _balanced(text: str, masked: str, start: int) -> tuple[str, int]:
    """Return the parenthesised group opening at `start`, and the index after it."""
    depth = 0
    for index in range(start, len(masked)):
        if masked[index] == "(":
            depth += 1
        elif masked[index] == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1], index + 1
    raise ValueError("unterminated parenthesised group")


def _module_header(text: str, module: str) -> tuple[str, str]:
    """Return `module`'s parameter block and its port block.

    The two are separate groups and the parameter one is optional, so the port
    list cannot be found by taking the first bracket after the module name.
    """
    masked = _mask_comments(text)
    start = re.search(rf"^module\s+{re.escape(module)}\b", masked, re.M)
    if start is None:
        raise ValueError(f"{module} is not declared in its own source file")
    position = start.end()
    parameters = ""
    opening = masked.index("(", position)
    if "#" in masked[position:opening]:
        parameters, position = _balanced(text, masked, opening)
        opening = masked.index("(", position)
    ports, _ = _balanced(text, masked, opening)
    return parameters, ports


def read_tile_type(source: Path, module: str) -> TileType:
    """Parse one tile's Verilog into ports, each carrying its declared edge."""
    text = source.read_text()
    parameter_block, header = _module_header(text, module)
    parameters: dict[str, int] = {}
    for name, value in PARAMETER_RE.findall(parameter_block):
        try:
            parameters[name] = _evaluate(value, parameters)
        except (ValueError, SyntaxError, NameError, TypeError):
            continue  # a bitstream default is not a width and is never used as one

    ports: dict[str, Port] = {}
    rows = 1
    for line in header.splitlines():
        match = PORT_RE.match(line)
        if match is None:
            continue
        direction, high, low, name, comment = match.groups()
        if direction == "inout":
            raise ValueError(f"{module}.{name} is inout, which no FABulous tile port is")
        width = 1 if high is None else _evaluate(high, parameters) - _evaluate(low, parameters) + 1

        sub_row = 0
        sub_match = SUB_ROW_RE.match(name)
        if sub_match is not None:
            sub_row = int(sub_match.group(1))
            rows = max(rows, sub_row + 1)

        annotated = TILE_PORT_RE.search(comment or "")
        ports[name] = Port(
            name=name,
            direction=direction,
            width=width,
            annotated_side=annotated.group(1) if annotated else None,
            sub_row=sub_row,
            vectored=high is not None,
        )
    if not ports:
        raise ValueError(f"{module} declares no ports; its header was not understood")
    return TileType(name=module, source=source, ports=ports, rows=rows)


def read_tile_types(tile_root: Path, wanted: set[str]) -> dict[str, TileType]:
    sources = {path.stem: path for path in tile_root.rglob("*.v")}
    missing = wanted - sources.keys()
    if missing:
        raise ValueError(f"no Verilog for tile types {sorted(missing)}")
    return {name: read_tile_type(sources[name], name) for name in sorted(wanted)}


def read_instances(fabric_verilog: Path) -> list[Instance]:
    """Recover the tile grid from `eFPGA.v`'s instance list."""
    text = fabric_verilog.read_text()
    instances = []
    for module, name, x, y, body in INSTANCE_RE.findall(text):
        connections = dict(CONNECTION_RE.findall(body))
        declared = len(re.findall(r"\.\w+\(", body))
        if len(connections) != declared:
            raise ValueError(f"{name} has a connection that is not a plain net name")
        instances.append(
            Instance(name=name, tile_type=module, x=int(x), y=int(y), connections=connections)
        )
    if not instances:
        raise ValueError(f"{fabric_verilog} declares no tile instances")
    return instances


def _boundary_side(instance: Instance, columns: int, rows: int, height: int) -> Side:
    """Return the fabric edge an instance sits on, for a port that leaves the fabric."""
    candidates: list[Side] = []
    if instance.x == 0:
        candidates.append("W")
    if instance.x == columns - 1:
        candidates.append("E")
    if instance.y == 0:
        candidates.append("N")
    if instance.y + height == rows:
        candidates.append("S")
    if not candidates:
        raise ValueError(f"{instance.name} has an external port but touches no fabric edge")
    # A corner instance touches two; the caller only uses this when nothing
    # better is available, and the first is deterministic.
    return candidates[0]


def load_fabric(project: Path) -> Fabric:
    """Build the whole model from a FABulous project directory."""
    fabric_verilog = project / "Fabric" / "eFPGA.v"
    instances = read_instances(fabric_verilog)
    tile_types = read_tile_types(project / "Tile", {i.tile_type for i in instances})

    by_position: dict[tuple[int, int], Instance] = {}
    for instance in instances:
        for offset in range(tile_types[instance.tile_type].rows):
            position = (instance.x, instance.y + offset)
            if position in by_position:
                raise ValueError(f"{instance.name} overlaps {by_position[position].name}")
            by_position[position] = instance
    columns = max(x for x, _ in by_position) + 1
    rows = max(y for _, y in by_position) + 1

    writers: dict[str, tuple[Instance, Port]] = {}
    readers: dict[str, list[tuple[Instance, Port]]] = {}
    for instance in instances:
        tile = tile_types[instance.tile_type]
        for port_name, net in instance.connections.items():
            port = tile.ports[port_name]
            if port.direction == "output":
                if net in writers:
                    raise ValueError(f"net {net} is driven by two tile ports")
                writers[net] = (instance, port)
            else:
                readers.setdefault(net, []).append((instance, port))

    links: list[Link] = []
    linked_side: dict[tuple[str, str], Side] = {}
    boundary_side: dict[tuple[str, str], Side] = {}

    def fix(store: dict[tuple[str, str], Side], key: tuple[str, str], side: Side) -> None:
        """Fix a port's edge, refusing to let two instances disagree about it."""
        if store.setdefault(key, side) != side:
            raise ValueError(f"{key[0]}.{key[1]} is on {store[key]} in one instance and {side} in another")

    for instance in instances:
        tile = tile_types[instance.tile_type]
        for port_name, net in instance.connections.items():
            port = tile.ports[port_name]
            partners = [
                (other, other_port)
                for other, other_port in (
                    [writers[net]] if port.direction == "input" and net in writers else []
                )
                + (readers.get(net, []) if port.direction == "output" else [])
                if other.name != instance.name
            ]
            if not partners:
                # The port leaves the fabric here. That says nothing about the
                # edge it belongs on if the same port links elsewhere, which is
                # exactly the case for a terminator's FrameData in column 1.
                fix(
                    boundary_side,
                    (tile.name, port_name),
                    _boundary_side(instance, columns, rows, tile.rows),
                )
                continue
            for other, other_port in partners:
                if other_port.width != port.width:
                    raise ValueError(
                        f"{instance.name}.{port_name} and {other.name}.{other_port.name} "
                        "differ in width"
                    )
                step = (
                    other.x - instance.x,
                    (other.y + other_port.sub_row) - (instance.y + port.sub_row),
                )
                if step not in STEP_TO_SIDE:
                    raise ValueError(
                        f"{instance.name}.{port_name} reaches {other.name} across {step}, "
                        "which is not one grid step"
                    )
                fix(linked_side, (tile.name, port_name), STEP_TO_SIDE[step])
                if port.direction != "input":
                    continue
                driver_side = OPPOSITE[STEP_TO_SIDE[step]]
                for driver_bit, receiver_bit in zip(
                    other_port.bits(other.tile_type), port.bits(tile.name), strict=True
                ):
                    links.append(
                        Link(
                            driver=driver_bit,
                            receiver=receiver_bit,
                            driver_side=driver_side,
                            driver_sub_row=other_port.sub_row,
                            receiver_sub_row=port.sub_row,
                            driver_at=(other.x, other.y + other_port.sub_row),
                            receiver_at=(instance.x, instance.y + port.sub_row),
                        )
                    )

    # A port that never links anywhere still needs an edge. FABulous gives the
    # same seam signal the same edge in every tile type, so a name that links on
    # one type decides it; only a name that links nowhere falls back to the
    # annotation, and only an unannotated one to the tile's fabric edge.
    by_name: dict[str, set[Side]] = {}
    for (_, port_name), side in linked_side.items():
        by_name.setdefault(port_name, set()).add(side)
    inconsistent = {name: sorted(s) for name, s in by_name.items() if len(s) > 1}
    if inconsistent:
        raise ValueError(f"these port names take more than one edge: {inconsistent}")

    sides = {key: PortSide(side=side, external=False) for key, side in linked_side.items()}
    for key, side in boundary_side.items():
        if key in sides:
            continue
        tile_type, port_name = key
        shared = by_name.get(port_name)
        annotated = tile_types[tile_type].ports[port_name].annotated_side
        resolved = next(iter(shared)) if shared else (annotated or side)
        sides[key] = PortSide(side=resolved, external=True)

    disagreements = [
        f"{tile_type}.{port} sits on {placement.side}, annotated {annotation}"
        for (tile_type, port), placement in sides.items()
        if (annotation := tile_types[tile_type].ports[port].annotated_side) is not None
        and annotation != placement.side
    ]
    if disagreements:
        raise ValueError(
            f"{len(disagreements)} ports contradict their TilePort annotation: {disagreements[:5]}"
        )

    return Fabric(
        tile_types=tile_types,
        instances=by_position,
        links=links,
        sides=sides,
        columns=columns,
        rows=rows,
    )
