"""Write and power the top-level ECC run: the tile macros, the loader and the front-ends.

The top is one ECC project. The fabric's macros sit fixed at the positions the
plan abutted them at, moved up by a strip of standard-cell rows along the south
edge and right by a channel along the west edge, and the configuration logic is
synthesised into those rows. Each region sits where its wires are:
`FrameStrobe` enters every column on the fabric's south edge, above the strip,
and `FrameData` enters every row on its west edge, beside the channel.

ECC's PDN generator lays one grid over the whole core and has no region to
confine it to, so over the fabric it would draw a second grid across the tiles'
own. Its stripe list is emptied, as in the fabric-level run, and `write_pdn`
draws the power in the floorplan DEF instead, the same way `flow.defedit`
stretches a tile's. Every stripe it draws in the strip continues one of the
bottom-row tiles' MET4 stripes, and every MET5 stripe in the channel continues
one of the west-column tiles', so the two grids meet end to end on the same net
at the fabric edge rather than through vias over a tile.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, replace
from pathlib import Path

from flow import defedit, repair, topwrap
from flow import project as ecc_project
from flow.config import FabricSettings, Param
from flow.fabric import Fabric
from flow.plan import CORE_MARGIN, DBU, SITE_HEIGHT, SITE_WIDTH, PinPlacement, Plan
from flow.topdesign import Netlist, _stub, build_netlist
from flow.variant import Paths

TOP_MODULE = "eFPGA_top"
CONFIG_SOURCES = (
    "fabric_config.sv",
    "config_frontend.v",
    "config_UART.v",
    "bitbang.v",
    "config_spi.v",
)
# The tiles' own PDN, as their hardened DEFs draw it: 1 um stripes on MET4 and
# MET5, VDD then VSS 8.4 um apart and each net every 16.8 um, and 0.16 um MET1
# rails with VDD on the core's bottom edge.
STRIPE_WIDTH = 1000
STRIPE_PITCH = 16800
STRIPE_FIRST = {"VDD": 3000, "VSS": 11400}
RAIL_WIDTH = 160
# The fabric sits this far above the strip's top row. A tile's abstract reserves
# all of its MET1, and the rail on that row's top edge reaches 0.08 um past it,
# so 0.2 um leaves the 0.09 um MET1 spacing and keeps the tiles on the track grid.
# ECC's core is whole rows, so the die grows by a row to keep the fabric inside.
FABRIC_GAP = 200
# The top-level routing blockage over the fabric stops this far inside its
# edge, so the tiles' edge pins, 0.55 um deep, stay reachable from outside.
BLOCKAGE_INSET = 1000
BLOCKED_LAYERS = ("MET1", "MET2", "MET3", "MET4", "MET5")
# Pins for the configuration ports sit on the south edge under the channel, on
# every third MET4 track, at 0.1 um plus a multiple of 0.2 um.
CONFIG_PIN_LAYER = "MET4"
CONFIG_PIN_PITCH = 600
TRACK_ORIGIN = 100
TRACK_STEP = 200
VIAS = """- VIA1_1000x160 + VIARULE MET2_MET1 + CUTSIZE 90 90 + LAYERS MET1 VIA1 MET2 + CUTSPACING 110 110 + ENCLOSURE 55 35 55 35  + ROWCOL 1 5
 ;
- VIA2_1000x160 + VIARULE MET3_MET2 + CUTSIZE 90 90 + LAYERS MET2 VIA2 MET3 + CUTSPACING 110 110 + ENCLOSURE 55 35 55 35  + ROWCOL 1 5
 ;
- VIA3_1000x160 + VIARULE MET4_MET3 + CUTSIZE 90 90 + LAYERS MET3 VIA3 MET4 + CUTSPACING 110 110 + ENCLOSURE 55 35 55 35  + ROWCOL 1 5
 ;
- VIA4_1000x1000 + VIARULE MET5_MET4 + CUTSIZE 90 90 + LAYERS MET4 VIA4 MET5 + CUTSPACING 110 110 + ENCLOSURE 55 55 55 55  + ROWCOL 5 5
 ;
"""
STRIPE_RE = re.compile(
    r"(MET[45]) 1000 \+ SHAPE STRIPE \( (-?\d+) (-?\d+) \) \( (-?\d+|\*) (-?\d+|\*) \)"
)


@dataclass(frozen=True)
class Geometry:
    """The top die around the fabric, in DBU."""

    channel: int  # west of the fabric
    strip: int  # south of the fabric
    fabric_width: int
    fabric_height: int

    def __post_init__(self) -> None:
        if self.channel % SITE_WIDTH:
            raise ValueError(
                f"channel {self.channel} DBU is not a whole number of sites"
            )
        if self.strip % SITE_HEIGHT:
            raise ValueError(
                f"strip {self.strip} DBU is not a whole number of core7 rows"
            )

    @property
    def origin(self) -> tuple[int, int]:
        """The fabric's lower-left corner in die coordinates."""
        return CORE_MARGIN + self.channel, CORE_MARGIN + self.strip + FABRIC_GAP

    @property
    def width(self) -> int:
        return 2 * CORE_MARGIN + self.channel + self.fabric_width

    @property
    def height(self) -> int:
        gap = -(-FABRIC_GAP // SITE_HEIGHT) * SITE_HEIGHT
        return 2 * CORE_MARGIN + self.strip + gap + self.fabric_height


def geometry(plan: Plan, channel_micron: float, strip_micron: float) -> Geometry:
    core_height = -(-plan.height // SITE_HEIGHT) * SITE_HEIGHT
    return Geometry(
        channel=round(channel_micron * DBU),
        strip=round(strip_micron * DBU),
        fabric_width=plan.width,
        fabric_height=core_height,
    )


def _micron(value: int) -> str:
    return f"{value / DBU:.3f}"


def _macro_placements(plan: Plan, shape: Geometry) -> str:
    """Render `[params.macro]` with every tile moved by the channel and the strip."""
    x0, y0 = shape.origin
    rows = ",\n".join(
        f'    {{ instance = "{placement.name}", '
        f"x = {_micron(placement.x + x0)}, y = {_micron(placement.y + y0)}, "
        f'orientation = "R0" }}'
        for placement in plan.placements
    )
    return f"\n[params.macro]\nplacements = [\n{rows},\n]\n"


def write_project(
    *,
    paths: Paths,
    plan: Plan,
    fabric: Fabric,
    directory: Path,
    settings: FabricSettings,
    params: tuple[Param, ...],
    shape: Geometry,
) -> Netlist:
    """Write the top's RTL, filelist, SDC and `ecc.toml` into `directory`."""
    netlist = build_netlist(fabric)
    text = paths.fabric_verilog.read_text()
    source = str(paths.fabric_verilog.relative_to(paths.root))
    rtl = directory / "rtl"
    rtl.mkdir(parents=True, exist_ok=True)
    for name, tile in sorted(fabric.tile_types.items()):
        (rtl / f"{name}_stub.v").write_text(_stub(tile))
    for name in CONFIG_SOURCES:
        shutil.copyfile(paths.root / "Fabric" / name, rtl / name)
    (rtl / f"{TOP_MODULE}.v").write_text(topwrap.render(fabric, text, source, netlist))
    (directory / "filelist.f").write_text(
        "".join(f"rtl/{name}_stub.v\n" for name in sorted(fabric.tile_types))
        + "".join(f"rtl/{name}\n" for name in CONFIG_SOURCES)
        + f"rtl/{TOP_MODULE}.v\n"
    )
    (directory / "top.sdc").write_text(
        "# The configuration clock. The fabric's user clock is rooted in SW_term's\n"
        "# GBUF and depends on the bitstream, so it is not constrained here.\n"
        f"create_clock -name CLK -period {1000.0 / settings.frequency_mhz:.1f} [get_ports CLK]\n"
        # Without it STA after CTS still times an ideal clock and hold ignores skew.
        "set_propagated_clock [get_clocks CLK]\n"
    )
    ecc_project.write_ecc_toml(
        directory,
        top=TOP_MODULE,
        settings=replace(settings, clock_port="CLK"),
        params=[
            *params,
            Param("floorplan.die_builder", "mode", "die_size"),
            Param("floorplan.die_builder.die_size", "width_micron", shape.width / DBU),
            Param(
                "floorplan.die_builder.die_size", "height_micron", shape.height / DBU
            ),
        ],
        preset="rtl2gds",
        sdc="top.sdc",
        # No stripes: over the fabric they would lie across the tiles' own grid,
        # and `write_pdn` draws the strip's and the channel's instead.
        stripe_pitch_micron=None,
    )
    with (directory / "ecc.toml").open("a") as handle:
        handle.write(_macro_placements(plan, shape))
    return netlist


PORT_RE = re.compile(
    r"^\s*(input|output)\s+(?:wire\s+)?(?:\[(\d+):(\d+)\]\s+)?(\\?[\w\[\]]+)", re.M
)


def top_ports(netlist: Path) -> list[str]:
    """Return the synthesised top's ports, one name per bit as ECC's DEF spells it."""
    text = defedit.read_def(netlist)
    module = re.search(rf"^module {TOP_MODULE}\b.*?^endmodule", text, re.S | re.M)
    if module is None:
        raise ValueError(f"{netlist} holds no module {TOP_MODULE}")
    names = []
    for _, high, low, name in PORT_RE.findall(module.group(0)):
        if high:
            names += [f"{name}_{bit}" for bit in range(int(low), int(high) + 1)]
        else:
            names.append(name.lstrip("\\"))
    return names


def fabric_pins(
    plan: Plan,
    fabric: Fabric,
    netlist: Netlist,
    text: str,
    shape: Geometry,
    ports: set[str],
) -> list[PinPlacement]:
    """Place each fabric IO bit on the die edge facing the tile pin it connects to.

    The north and east tiles meet the die edge as they did in the fabric-level
    run. A south or west tile faces the strip or the channel instead, so its pin
    moves out across it to the die edge at the same coordinate along the edge,
    and the router draws the straight wire between them.
    """
    bound = topwrap.bindings(text)

    def port_name(bit: str) -> str:
        # ECC's synthesis bit-blasts a bus into `A_OUT_top_16`, and a one-bit
        # bus into its bare name.
        name, index = re.fullmatch(r"(\w+)\[(\d+)\]", bit).groups()
        for candidate in (f"{name}_{index}", name):
            if candidate in ports:
                return candidate
        raise ValueError(f"synthesis wrote no port for {bit}")

    origin = {placement.name: placement for placement in plan.placements}
    by_type = {
        name: {pin.name: pin for pin in pins} for name, pins in plan.pins.items()
    }
    x0, y0 = shape.origin
    placed = []
    for instance in netlist.instances:
        for pin, net in instance.pins:
            if net not in bound or bound[net] == "configured":
                continue
            placement = origin[instance.name]
            tile = by_type[placement.tile_type][pin]
            along = (
                x0 + placement.x if tile.side in ("N", "S") else y0 + placement.y
            ) + tile.offset
            placed.append(
                PinPlacement(
                    tile_type=TOP_MODULE,
                    name=port_name(bound[net]),
                    side=tile.side,
                    offset=along,
                    layer=tile.layer,
                    external=True,
                )
            )
    names = [pin.name for pin in placed]
    if len(names) != len(set(names)):
        raise ValueError("two tile pins claim the same top-level IO bit")
    return placed


def config_pins(names: list[str], shape: Geometry) -> list[PinPlacement]:
    """Spread the configuration ports along the south edge under the channel.

    A pin keeps clear of the channel's MET4 stripes, which the pins share a
    layer with and which run from the strip to the top of the channel.
    """
    stripes = [
        centre
        for first in STRIPE_FIRST.values()
        for centre in range(
            first + CORE_MARGIN, CORE_MARGIN + shape.channel, STRIPE_PITCH
        )
    ]
    guard = STRIPE_WIDTH // 2 + 400
    offsets = [
        track
        for track in range(TRACK_ORIGIN, CORE_MARGIN + shape.channel, CONFIG_PIN_PITCH)
        if track > CORE_MARGIN
        and all(abs(track - centre) > guard for centre in stripes)
    ]
    if len(offsets) < len(names):
        raise ValueError(
            f"the channel's south edge has {len(offsets)} free tracks for "
            f"{len(names)} configuration pins; widen the channel"
        )
    return [
        PinPlacement(
            tile_type=TOP_MODULE,
            name=name,
            side="S",
            offset=offset,
            layer=CONFIG_PIN_LAYER,
            external=True,
        )
        for name, offset in zip(names, offsets)
    ]


def _tile_stripes(def_text: str, layer: str) -> list[tuple[str, int]]:
    """Return one tile's stripes on `layer` as (net, centre across the stripe)."""
    block = defedit.SPECIALNETS_RE.search(def_text)
    if block is None:
        raise ValueError("a tile DEF has no SPECIALNETS")
    found = []
    for net_block in re.split(r"^- ", block.group(1), flags=re.M)[1:]:
        net = net_block.split(None, 1)[0]
        for match in STRIPE_RE.finditer(net_block):
            stripe_layer, x, y, _, _ = match.groups()
            if stripe_layer == layer:
                found.append((net, int(x) if layer == "MET4" else int(y)))
    return found


def write_pdn(
    def_path: Path, plan: Plan, shape: Geometry, tile_defs: dict[str, Path]
) -> str:
    """Draw the strip's and the channel's PDN into the floorplan DEF.

    Replaces whatever SPECIALNETS the floorplan wrote, since any grid ECC drew
    here spans the fabric. Returns a one-line account of what was drawn.
    """
    text = defedit.read_def(def_path)
    x0, y0 = shape.origin
    left, bottom = CORE_MARGIN, CORE_MARGIN
    right, top = shape.width - CORE_MARGIN, shape.height - CORE_MARGIN
    tiles = {name: defedit.read_def(path) for name, path in tile_defs.items()}
    bottom_row = [p for p in plan.placements if p.y == 0]
    west_column = [p for p in plan.placements if p.x == 0]

    wires: dict[str, list[str]] = {"VDD": [], "VSS": []}

    def segment(
        net: str, layer: str, width: int, start: tuple[int, int], end: tuple[int, int]
    ) -> None:
        kind = "FOLLOWPIN" if layer == "MET1" else "STRIPE"
        wires[net].append(
            f"{layer} {width} + SHAPE {kind} ( {start[0]} {start[1]} ) ( {end[0]} {end[1]} )"
        )

    def via(net: str, layer: str, at: tuple[int, int], name: str) -> None:
        wires[net].append(f"{layer} 0 + SHAPE STRIPE ( {at[0]} {at[1]} ) {name}")

    # MET4 in the strip: every bottom-row tile's stripe carried down to the core
    # edge, plus the channel's own, which run the full height beside the fabric.
    strip_met4 = [
        (net, x0 + placement.x + x)
        for placement in bottom_row
        for net, x in _tile_stripes(tiles[placement.tile_type], "MET4")
    ]
    channel_met4 = [
        (net, centre)
        for net, first in STRIPE_FIRST.items()
        for centre in range(left + first, x0 - STRIPE_WIDTH, STRIPE_PITCH)
    ]
    for net, x in strip_met4:
        segment(net, "MET4", STRIPE_WIDTH, (x, bottom), (x, y0))
    for net, x in channel_met4:
        segment(net, "MET4", STRIPE_WIDTH, (x, bottom), (x, top))

    # MET5 in the channel: every west-column tile's stripe carried west to the
    # core edge; in the strip, the strip's own across the whole width.
    channel_met5 = [
        (net, y0 + placement.y + y)
        for placement in west_column
        for net, y in _tile_stripes(tiles[placement.tile_type], "MET5")
    ]
    strip_met5 = [
        (net, centre)
        for net, first in STRIPE_FIRST.items()
        for centre in range(bottom + first, y0 - STRIPE_WIDTH, STRIPE_PITCH)
    ]
    for net, y in channel_met5:
        segment(net, "MET5", STRIPE_WIDTH, (left, y), (x0, y))
    for net, y in strip_met5:
        segment(net, "MET5", STRIPE_WIDTH, (left, y), (right, y))

    for net_a, x in strip_met4 + channel_met4:
        for net_b, y in strip_met5:
            if net_a == net_b:
                via(net_a, "MET5", (x, y), "VIA4_1000x1000")
    for net_a, x in channel_met4:
        for net_b, y in channel_met5:
            if net_a == net_b:
                via(net_a, "MET5", (x, y), "VIA4_1000x1000")

    # MET1 rails on every row boundary the strip or the channel holds, VDD on
    # the core's bottom edge and alternating upward, as in every tile. A channel
    # rail runs to the fabric: LVS counts a cell's supply only where its pin
    # overlaps a drawn rail, and the west-column tiles' own rails lie 0.6 um off
    # this grid, 0.44 um clear of it.
    rails = 0
    for index, y in enumerate(range(bottom, top + 1, SITE_HEIGHT)):
        net = "VDD" if index % 2 == 0 else "VSS"
        end = right if y <= y0 else x0
        segment(net, "MET1", RAIL_WIDTH, (left, y), (end, y))
        rails += 1
        # A via stack where a same-net MET4 stripe crosses the rail.
        for stripe_net, x in strip_met4 + channel_met4:
            if stripe_net == net and x + STRIPE_WIDTH // 2 < end:
                via(net, "MET2", (x, y), "VIA1_1000x160")
                via(net, "MET3", (x, y), "VIA2_1000x160")
                via(net, "MET4", (x, y), "VIA3_1000x160")

    nets = []
    for net, use in (("VDD", "POWER"), ("VSS", "GROUND")):
        first, *rest = wires[net]
        body = f"  + ROUTED {first}\n" + "".join(f"    NEW {wire}\n" for wire in rest)
        # ECC names a hardened tile's supply pins after the stripes it drew.
        pins = f"( * {net} ) ( * {net.lower()}_stripe_generate )"
        nets.append(f"- {net} {pins} + USE {use}\n{body} ;\n")
    special = f"SPECIALNETS 2 ;\n{''.join(nets)}END SPECIALNETS"
    if defedit.SPECIALNETS_RE.search(text):
        text = re.sub(
            r"^SPECIALNETS \d+ ;\n.*?^END SPECIALNETS",
            lambda _: special,
            text,
            flags=re.S | re.M,
        )
    else:
        text = text.replace("\nNETS ", f"\n{special}\n\nNETS ", 1)
    vias = re.search(r"^VIAS (\d+) ;\n(.*?)^END VIAS", text, re.S | re.M)
    if vias is None:
        text = text.replace(
            "\nCOMPONENTS ", f"\nVIAS 4 ;\n{VIAS}END VIAS\n\nCOMPONENTS ", 1
        )
    else:
        missing = [
            entry
            for entry in VIAS.split(" ;\n")
            if entry.strip() and entry.split()[1] not in vias.group(2)
        ]
        if missing:
            count = int(vias.group(1)) + len(missing)
            addition = "".join(f"{entry} ;\n" for entry in missing)
            text = (
                text[: vias.start()]
                + f"VIAS {count} ;\n{vias.group(2)}{addition}END VIAS"
                + text[vias.end() :]
            )
    # A tile's abstract LEF leaves MET3 and MET4 tracks open over it, which the
    # top-level router otherwise takes for free space: it spread the fabric's
    # boundary nets across the tiles and hit their pins at 860,000 violations.
    fabric = (
        x0 + BLOCKAGE_INSET,
        y0 + BLOCKAGE_INSET,
        x0 + shape.fabric_width - BLOCKAGE_INSET,
        y0 + shape.fabric_height - BLOCKAGE_INSET,
    )
    blockages = "".join(
        f"- LAYER {layer} RECT ( {fabric[0]} {fabric[1]} ) ( {fabric[2]} {fabric[3]} ) ;\n"
        for layer in BLOCKED_LAYERS
    )
    if re.search(r"^BLOCKAGES \d+ ;", text, re.M):
        raise ValueError(
            f"{def_path} already has BLOCKAGES; merge them rather than replace"
        )
    text = text.replace(
        "\nSPECIALNETS ",
        f"\nBLOCKAGES {len(BLOCKED_LAYERS)} ;\n{blockages}END BLOCKAGES\n\nSPECIALNETS ",
        1,
    )
    defedit.write_def(def_path, text, gzipped=def_path.suffix == ".gz")
    return (
        f"routing blocked over the fabric on {len(BLOCKED_LAYERS)} layers; PDN drawn: {len(strip_met4)} strip and {len(channel_met4)} channel MET4 stripes, "
        f"{len(strip_met5)} strip and {len(channel_met5)} channel MET5 stripes, {rails} MET1 rails"
    )


NETS_RE = re.compile(r"^NETS (\d+) ;\n(.*?)^END NETS", re.S | re.M)


def _nets(text: str) -> tuple[re.Match[str], list[str]]:
    block = NETS_RE.search(text)
    if block is None:
        raise ValueError("the DEF has no NETS section")
    entries = [
        f"- {entry}" for entry in re.split(r"^- ", block.group(2), flags=re.M)[1:]
    ]
    return block, entries


def withhold_seam_nets(def_path: Path, seams: set[str]) -> list[str]:
    """Take every tile-to-tile net out of the DEF the router reads, and return them.

    Each of these nets joins two macro pins that abutment already lays on top
    of one another, so it needs no wire. iRT has no notion of a pin pair done by
    construction: it jogs each onto a track, collides with both pin shapes, and
    the top run reached 660,000 violations by the second detailed-route
    iteration. Withheld, the router sees only the nets that need wire.
    """
    text = defedit.read_def(def_path)
    block, entries = _nets(text)
    kept, withheld = [], []
    for entry in entries:
        name = entry.split(None, 2)[1]
        (withheld if name in seams else kept).append(entry)
    missing = seams - {entry.split(None, 2)[1] for entry in withheld}
    if missing:
        raise ValueError(
            f"{len(missing)} seam nets are not in {def_path}: {sorted(missing)[:4]}"
        )
    text = (
        text[: block.start()]
        + f"NETS {len(kept)} ;\n{''.join(kept)}END NETS"
        + text[block.end() :]
    )
    defedit.write_def(def_path, text, gzipped=def_path.suffix == ".gz")
    return withheld


def restore_seam_nets(def_path: Path, withheld: list[str]) -> None:
    """Put the withheld nets back, unrouted, so the layout's netlist is whole again."""
    text = defedit.read_def(def_path)
    block, entries = _nets(text)
    names = {entry.split(None, 2)[1] for entry in entries}
    clash = names & {entry.split(None, 2)[1] for entry in withheld}
    if clash:
        raise ValueError(
            f"{len(clash)} seam nets were routed after all: {sorted(clash)[:4]}"
        )
    merged = entries + withheld
    text = (
        text[: block.start()]
        + f"NETS {len(merged)} ;\n{''.join(merged)}END NETS"
        + text[block.end() :]
    )
    defedit.write_def(def_path, text, gzipped=def_path.suffix == ".gz")


# The full-chip signoff STA times hold against this uncertainty, and the repair
# adds HOLD_MARGIN on top for the gap between placement-estimated and
# extracted parasitics.
HOLD_UNCERTAINTY_NS = 0.05
HOLD_MARGIN_NS = 0.05


def repair_placement(
    def_path: Path, *, pdk_root: Path, macros: Path, sdc: Path, reports: Path
) -> str:
    """Repair slew, capacitance and hold on the legalised top in OpenROAD, in place,
    with `flow.repair.run`."""
    summary = repair.run(
        repair.TOP_TCL,
        def_path,
        env={
            "PDK": str(pdk_root),
            "MACROS": str(macros),
            "SDC": str(sdc),
            "HOLD_UNCERTAINTY": str(HOLD_UNCERTAINTY_NS),
            "HOLD_MARGIN": str(HOLD_MARGIN_NS),
        },
        reports=reports,
        keep_pins=False,
    )
    holds = [
        line
        for line in (reports / "repair.log").read_text().splitlines()
        if line.startswith(("hold after:", "setup after:"))
    ]
    return f"OpenROAD repair: {summary}; " + "; ".join(holds)
