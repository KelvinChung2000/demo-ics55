"""Add a fabric's extra IO pads to the foundry's post-route chip netlist.

`flow cli chip-top` writes a netlist from the macro alone. The foundry's `top.v`
also holds the buffers and tie cells its place and route added, so this module
extends that file: every foundry instance keeps its name and connections, and a
new bit of `PAD_IO` copies the pad, one tie cell per tied pin, of `PAD_IO[0]`.

The supply and corner pads keep their DEF coordinates. West of the macro the ring
has one slot more than the new IO need below the supply pads, so `PAD_USER_CLK`,
whose macro pin is on the west edge, keeps a west slot and the other west signal
pads move to the free south slots. The foundry owns the final pad ring, so
`pad_plan.csv` states a request and carries no routed wire length, only the
Manhattan distance from a pad's inner edge to its macro pin.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from flow.chiptop import MACRO, PAD_CELL, SIGNALS, TOP, USER_IO_PIN, USER_IO_PORT
from flow.defedit import read_def
from flow.plan import DBU

PAD_PITCH = 65 * DBU
# A pad's depth into the die, which is also the corner cell's side.
PAD_DEPTH = 130 * DBU
PAD_INSTANCE = "u_pad_{}"
TIE_PREFIX = {"TIELOH7R": "top_LTIELO", "TIEHIH7R": "top_LTIEHI"}
PAD_DATA_PINS = ("OE", "I", "C", "PAD", "A")
# The foundry's pin order, kept so a new pad reads like its neighbours.
TIE_PIN_ORDER = ("OD", "DS1", "DS0", "PU", "PD", "IE", "CS")
SUPPLY_CELL = re.compile(r"P65_1233_(VDD|VSS|VDDIO|VSSIO)3")
DEF_PAD = re.compile(
    r"^- (\S+) (P65_1233_(?!FILLER)\w+) .*?\+ FIXED \( (\d+) (\d+) \) (\w+)", re.MULTILINE
)
DEF_MACRO = re.compile(rf"^- u_efpga {MACRO} .*?\+ FIXED \( (\d+) (\d+) \) N", re.MULTILINE)
DEF_DIE = re.compile(r"^DIEAREA \( 0 0 \) \( (\d+) (\d+) \)", re.MULTILINE)

WEST_KEPT = "PAD_USER_CLK"
# Nearest the macro's configuration pins first: the SPI data path before the
# slow control pins, whose edges the configuration logic does not time.
SOUTH_ORDER = ("PAD_SPI_MOSI", "PAD_SPI_CSN", "PAD_UART_RX", "PAD_RSTN", "PAD_USER_RESET")


class Edge(Enum):
    WEST = "E"  # the DEF orientation of a pad on this edge
    SOUTH = "N"
    EAST = "W"
    NORTH = "S"


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def distance(self, other: Point) -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass(frozen=True)
class PadSite:
    instance: str
    cell: str
    origin: Point
    edge: Edge

    def inner(self, die: Point) -> Point:
        """The middle of the pad's edge that faces the core."""
        half = PAD_PITCH // 2
        match self.edge:
            case Edge.WEST:
                return Point(PAD_DEPTH, self.origin.y + half)
            case Edge.EAST:
                return Point(die.x - PAD_DEPTH, self.origin.y + half)
            case Edge.SOUTH:
                return Point(self.origin.x + half, PAD_DEPTH)
            case Edge.NORTH:
                return Point(self.origin.x + half, die.y - PAD_DEPTH)


@dataclass(frozen=True)
class Macro:
    """The hardened macro's pins, in macro coordinates, and its size."""

    pins: dict[str, Point]
    size: Point

    def edge(self, pin: str) -> Edge:
        point = self.pins[pin]
        if point.x == 0:
            return Edge.WEST
        if point.y == 0:
            return Edge.SOUTH
        if point.x == self.size.x:
            return Edge.EAST
        if point.y == self.size.y:
            return Edge.NORTH
        raise ValueError(f"macro pin {pin} at {point} is on no edge")


def read_lef(path: Path) -> Macro:
    """Each pin's outer edge midpoint, from the first RECT of its first PORT."""
    pins: dict[str, Point] = {}
    size: Point | None = None
    pin: str | None = None
    for line in path.read_text().splitlines():
        fields = line.split()
        if fields[:1] == ["SIZE"]:
            size = Point(round(float(fields[1]) * DBU), round(float(fields[3]) * DBU))
        elif fields[:1] == ["PIN"]:
            pin = fields[1]
        elif fields[:1] == ["RECT"] and pin is not None:
            if size is None:
                raise ValueError(f"{path}: PIN {pin} precedes SIZE")
            llx, lly, urx, ury = (round(float(f) * DBU) for f in fields[1:5])
            x = (llx + urx) // 2 if ury - lly > urx - llx else (0 if llx == 0 else urx)
            y = (lly + ury) // 2 if urx - llx > ury - lly else (0 if lly == 0 else ury)
            pins[pin] = Point(x, y)
            pin = None
    if size is None:
        raise ValueError(f"{path} holds no SIZE statement")
    return Macro(pins, size)


def read_netlist(path: Path) -> dict:
    """The `top` module of a netlist as Yosys JSON; library cells stay unresolved."""
    with tempfile.TemporaryDirectory() as scratch:
        out = Path(scratch) / "top.json"
        subprocess.run(["yosys", "-q", "-p", f"read_verilog {path}; write_json {out}"], check=True)
        return json.loads(out.read_text())["modules"][TOP]


def net_names(module: dict) -> dict[int, str]:
    return {
        bit: name if len(net["bits"]) == 1 else f"{name}[{index}]"
        for name, net in module["netnames"].items()
        for index, bit in enumerate(net["bits"])
    }


def pad_ports(module: dict) -> dict[str, str]:
    """Each PBMUX instance's chip port, `PAD_IO[3]` style for a bus bit."""
    names = net_names(module)
    return {
        instance: names[cell["connections"]["PAD"][0]]
        for instance, cell in module["cells"].items()
        if cell["type"] == PAD_CELL
    }


def tie_pattern(module: dict) -> dict[str, str]:
    """The tie cell type on each tied pin, which every user IO pad must share."""
    tie_of = {
        cell["connections"]["Z"][0]: cell["type"]
        for cell in module["cells"].values()
        if cell["type"] in TIE_PREFIX
    }
    patterns = {
        instance: {
            pin: tie_of[bits[0]]
            for pin, bits in module["cells"][instance]["connections"].items()
            if pin not in PAD_DATA_PINS
        }
        for instance, port in pad_ports(module).items()
        if port.startswith(f"{USER_IO_PORT}[")
    }
    distinct = {tuple(sorted(pattern.items())) for pattern in patterns.values()}
    if len(distinct) != 1:
        raise ValueError(f"the user IO pads tie their pins {len(distinct)} different ways")
    pattern = next(iter(patterns.values()))
    if set(pattern) != set(TIE_PIN_ORDER):
        raise ValueError(f"expected ties on {TIE_PIN_ORDER}, found {sorted(pattern)}")
    return pattern


def read_ring(text: str) -> dict[str, PadSite]:
    return {
        match[1]: PadSite(
            instance=match[1],
            cell=match[2],
            origin=Point(int(match[3]), int(match[4])),
            edge=Edge(match[5]) if match[2] != "P65_1233_CORNER" else Edge.SOUTH,
        )
        for match in DEF_PAD.finditer(text)
    }


def _supply_extent(ring: dict[str, PadSite], edge: Edge) -> tuple[int, int]:
    along = [
        site.origin.x if edge in (Edge.NORTH, Edge.SOUTH) else site.origin.y
        for site in ring.values()
        if site.edge is edge and SUPPLY_CELL.fullmatch(site.cell)
    ]
    return min(along), max(along)


def _slots(start: int, stop: int) -> list[int]:
    return list(range(start, stop - PAD_PITCH + 1, PAD_PITCH))


def plan_ring(
    *,
    ring: dict[str, PadSite],
    ports: dict[str, str],
    macro: Macro,
    new_bits: list[int],
    origin: Point,
    die: Point,
) -> tuple[dict[str, PadSite], dict[int, str]]:
    """Every pad's site, and the instance of each new user IO bit.

    A pad's order along an edge follows its macro pin's, so no two new wires cross.
    """
    by_port = {port: instance for instance, port in ports.items()}
    plan = dict(ring)

    def site(instance: str, cell: str, edge: Edge, along: int) -> PadSite:
        vertical = edge in (Edge.WEST, Edge.EAST)
        fixed = {
            Edge.WEST: 0,
            Edge.SOUTH: 0,
            Edge.EAST: die.x - PAD_DEPTH,
            Edge.NORTH: die.y - PAD_DEPTH,
        }[edge]
        point = Point(fixed, along) if vertical else Point(along, fixed)
        return PadSite(instance=instance, cell=cell, origin=point, edge=edge)

    west_signals = {
        ports[i] for i, s in ring.items() if s.edge is Edge.WEST and i in ports
    }
    if west_signals != {WEST_KEPT, *SOUTH_ORDER}:
        raise ValueError(f"unexpected west signal pads {sorted(west_signals)}")

    south_slots = _slots(_supply_extent(ring, Edge.SOUTH)[1] + PAD_PITCH, die.x - PAD_DEPTH)
    if len(south_slots) < len(SOUTH_ORDER):
        raise ValueError(f"south has {len(south_slots)} free slots for {len(SOUTH_ORDER)} pads")
    for port, x in zip(SOUTH_ORDER, south_slots, strict=False):
        plan[by_port[port]] = site(by_port[port], PAD_CELL, Edge.SOUTH, x)

    edges: dict[Edge, list[int]] = {Edge.WEST: [], Edge.NORTH: []}
    for bit in new_bits:
        edge = macro.edge(f"A_IN_top_{bit}")
        if edge not in edges:
            raise ValueError(f"new bit {bit} sits on the {edge.name} edge of the macro")
        edges[edge].append(bit)

    instances: dict[int, str] = {}
    next_pad = len(ports)

    def assign(edge: Edge, bits: list[int], slots: list[int]) -> None:
        nonlocal next_pad
        for bit, along in zip(bits, slots, strict=True):
            instances[bit] = PAD_INSTANCE.format(next_pad)
            plan[instances[bit]] = site(instances[bit], PAD_CELL, edge, along)
            next_pad += 1

    west_slots = _slots(PAD_DEPTH, _supply_extent(ring, Edge.WEST)[0])
    west_bits = sorted(edges[Edge.WEST], key=lambda b: macro.pins[f"A_IN_top_{b}"].y)
    if len(west_slots) < len(west_bits) + 1:
        raise ValueError(f"west has {len(west_slots)} slots for {len(west_bits) + 1} pads")
    plan[by_port[WEST_KEPT]] = site(by_port[WEST_KEPT], PAD_CELL, Edge.WEST, west_slots[0])
    assign(Edge.WEST, west_bits, west_slots[1:])

    north_slots = _slots(PAD_DEPTH, _supply_extent(ring, Edge.NORTH)[0])
    north_bits = sorted(edges[Edge.NORTH], key=lambda b: macro.pins[f"A_IN_top_{b}"].x)
    if len(north_slots) < len(north_bits):
        raise ValueError(f"north has {len(north_slots)} slots for {len(north_bits)} pads")

    def north_cost(first: int) -> int:
        return sum(
            abs(origin.x + macro.pins[f"A_IN_top_{bit}"].x - x - PAD_PITCH // 2)
            for bit, x in zip(north_bits, north_slots[first:], strict=False)
        )

    best = min(range(len(north_slots) - len(north_bits) + 1), key=north_cost)
    assign(Edge.NORTH, north_bits, north_slots[best : best + len(north_bits)])
    return plan, instances


def extended_netlist(*, text: str, module: dict, instances: dict[int, str]) -> str:
    """The foundry netlist with one more pad per bit of `instances`."""
    pattern = tie_pattern(module)
    used = {
        prefix: max(
            (
                int(match[1])
                for name in module["cells"]
                if (match := re.fullmatch(rf"{prefix}_(\d+)", name))
            ),
            default=0,
        )
        for prefix in TIE_PREFIX.values()
    }
    wires: list[str] = []
    cells: list[str] = []
    macro_pins: list[str] = []
    for bit, instance in sorted(instances.items()):
        pins = {name: f"A_{name}_top_{bit}" for name in ("EN", "IN", "OUT")}
        wires += [f"   wire {net};" for net in pins.values()]
        macro_pins += [f"{net}({net})" for net in pins.values()]
        ties: dict[str, str] = {}
        for pin in TIE_PIN_ORDER:
            cell_type = pattern[pin]
            prefix = TIE_PREFIX[cell_type]
            used[prefix] += 1
            name = f"{prefix}_{used[prefix]}"
            ties[pin] = f"{name}_NET"
            wires.append(f"   wire {name}_NET;")
            cells.append(f"   {cell_type} {name} (.Z({name}_NET));")
        tied = "".join(f"\t.{pin}({ties[pin]}),\n" for pin in TIE_PIN_ORDER)
        cells.append(
            f"   {PAD_CELL} {instance} (.OE({pins['EN']}),\n\t.I({pins['IN']}),\n{tied}"
            f"\t.A(),\n\t.PAD({USER_IO_PORT}[{bit}]),\n\t.C({pins['OUT']}));"
        )

    width = max(instances) + 1
    old_port = f"   inout [{width - len(instances) - 1}:0] {USER_IO_PORT};\n"
    macro_head = f"   {MACRO} u_efpga ("
    tail = "endmodule\n"
    for anchor in (old_port, macro_head, tail):
        if text.count(anchor) != 1:
            raise ValueError(f"expected one {anchor.strip()!r} in the netlist")
    new_macro_pins = "".join(f".{pin},\n\t" for pin in macro_pins)
    return (
        text.replace(
            old_port,
            f"   inout [{width - 1}:0] {USER_IO_PORT};\n" + "\n".join(wires) + "\n",
        )
        .replace(macro_head, macro_head + new_macro_pins)
        .replace(tail, "\n".join(cells) + "\n" + tail)
    )


def check_extended(*, before: dict, after: dict, macro: Macro, instances: dict[int, str]) -> None:
    """Refuse a netlist that changed a foundry cell or left a macro pin or new pad open."""

    def wiring(module: dict) -> dict[str, tuple[str, dict[str, list[str]]]]:
        names = net_names(module)
        return {
            instance: (
                cell["type"],
                {
                    pin: [names.get(bit, str(bit)) for bit in bits]
                    for pin, bits in cell["connections"].items()
                },
            )
            for instance, cell in module["cells"].items()
        }

    old, new = wiring(before), wiring(after)
    for instance, (cell_type, pins) in old.items():
        new_type, new_pins = new[instance]
        kept = {pin: new_pins[pin] for pin in pins}
        if new_type != cell_type or kept != pins:
            raise ValueError(f"foundry cell {instance} changed")
    open_pins = set(macro.pins) - set(new["u_efpga"][1]) - {"VDD", "VSS"}
    open_pins = {p for p in open_pins if "stripe" not in p}
    if open_pins:
        raise ValueError(f"macro pins left open: {sorted(open_pins)}")
    for bit, instance in instances.items():
        pins = new[instance][1]
        macro_pins = new["u_efpga"][1]
        for pad_pin, macro_pin in (("OE", "EN"), ("I", "IN"), ("C", "OUT")):
            if pins[pad_pin] != macro_pins[f"A_{macro_pin}_top_{bit}"]:
                raise ValueError(f"{instance}.{pad_pin} misses A_{macro_pin}_top_{bit}")
        if pins["PAD"] != [f"{USER_IO_PORT}[{bit}]"]:
            raise ValueError(f"{instance} is not on {USER_IO_PORT}[{bit}]")


def macro_pin_of(port: str) -> str | None:
    """The macro pin a chip port reaches; a user IO port names its A_IN pin."""
    if port.startswith(f"{USER_IO_PORT}["):
        return f"A_IN_top_{port[len(USER_IO_PORT) + 1 : -1]}"
    return next((pin for pin, signal in SIGNALS.items() if signal.port == port), None)


def write_plan(
    *,
    path: Path,
    plan: dict[str, PadSite],
    ring: dict[str, PadSite],
    ports: dict[str, str],
    macro: Macro,
    origin: Point,
    die: Point,
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["instance", "cell", "port", "x_um", "y_um", "orient", "change", "to_pin_um"])
        for site in sorted(plan.values(), key=lambda s: (s.edge.name, s.origin.x, s.origin.y)):
            old = ring.get(site.instance)
            change = "new" if old is None else "kept" if old.origin == site.origin else "moved"
            port = ports.get(site.instance, "")
            pin = macro_pin_of(port) if port else None
            reach = ""
            if pin is not None:
                local = macro.pins[pin]
                target = Point(origin.x + local.x, origin.y + local.y)
                reach = f"{site.inner(die).distance(target) / DBU:.1f}"
            writer.writerow(
                [
                    site.instance,
                    site.cell,
                    port,
                    f"{site.origin.x / DBU:g}",
                    f"{site.origin.y / DBU:g}",
                    site.edge.value,
                    change,
                    reach,
                ]
            )


def write(*, foundry_netlist: Path, foundry_def: Path, lef: Path, out: Path) -> dict[str, PadSite]:
    """Write `top.v` and `pad_plan.csv` into `out`, returning the plan."""
    module = read_netlist(foundry_netlist)
    macro = read_lef(lef)
    text = read_def(foundry_def)
    origin_match = DEF_MACRO.search(text)
    die_match = DEF_DIE.search(text)
    if origin_match is None or die_match is None:
        raise ValueError(f"{foundry_def} names no {MACRO} placement or DIEAREA")
    origin = Point(int(origin_match[1]), int(origin_match[2]))
    die = Point(int(die_match[1]), int(die_match[2]))
    ring = read_ring(text)
    ports = pad_ports(module)

    wired = set(module["cells"]["u_efpga"]["connections"])
    bits = sorted(int(m[2]) for pin in macro.pins if (m := USER_IO_PIN.fullmatch(pin)) and m[1] == "IN")
    new_bits = [bit for bit in bits if f"A_IN_top_{bit}" not in wired]
    plan, instances = plan_ring(
        ring=ring, ports=ports, macro=macro, new_bits=new_bits, origin=origin, die=die
    )

    netlist = extended_netlist(
        text=foundry_netlist.read_text(), module=module, instances=instances
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "top.v").write_text(netlist)
    check_extended(
        before=module, after=read_netlist(out / "top.v"), macro=macro, instances=instances
    )
    all_ports = ports | {
        instance: f"{USER_IO_PORT}[{bit}]" for bit, instance in instances.items()
    }
    write_plan(
        path=out / "pad_plan.csv",
        plan=plan,
        ring=ring,
        ports=all_ports,
        macro=macro,
        origin=origin,
        die=die,
    )
    return plan
