"""Write the fabric-level ECC project the hardened tiles are placed into.

The parent run never sees a tile source. It sees the abstract LEF and the
extracted `.lib` of each hardened macro, and both of those bit-blast a bus into
scalars such as `N1BEG_0_`, so a parent netlist saying `.N1BEG(...)` fails Yosys
with "does not have a port named". Everything here is therefore emitted flat: a
scalar-port blackbox stub per tile type, and an `eFPGA` netlist whose every
connection is one scalar. The shape of each scalar comes from `flow.fabric`'s
model of the tile sources rather than from the text of `eFPGA.v`, because only
the model knows that a `[0:0]` port keeps its index while a plain scalar does
not, and because a regex over the instance list would have to re-derive the grid
that the model already holds.

Two things the model cannot supply, both reported rather than guessed. It
carries no `assign`, so `eFPGA.v`'s per-row and per-column slices of `FrameData`
and `FrameStrobe` reach the top level under their own net names, one scalar for
one scalar and no bit lost. And ECC's parameter registry has no die size, so the
die computed here goes into `ecc.toml` as a comment and has to be carried into
`fp_default_config.json` by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

from flow.fabric import Fabric, Port, TileType, load_fabric
from flow.plan import CORE_MARGIN, DBU, SITE_HEIGHT, SITE_WIDTH, Plan

ORIENT = "N"  # a tile is hardened once, so abutment never mirrors or rotates it
CLOCK_PORT = "UserCLK"
CLOCK_MHZ = 100.0
TOP_MODULE = "eFPGA"
PDK_NAME = "ics55"
PDK_ROOT = Path("/home/kelvin/side-project/ecc-spike/pdk")


@dataclass(frozen=True)
class Die:
    """The parent die, in DBU, sized so the core holds the fabric exactly."""

    width: int
    height: int

    @property
    def core_rows(self) -> int:
        return (self.height - 2 * CORE_MARGIN) // SITE_HEIGHT


@dataclass(frozen=True)
class InstanceNetlist:
    """One macro instance, as scalar pin and scalar net pairs."""

    name: str
    tile_type: str
    pins: list[tuple[str, str]]


@dataclass(frozen=True)
class Netlist:
    """The parent netlist, every name already bit-blasted to a scalar."""

    inputs: list[str]
    outputs: list[str]
    wires: list[str]
    instances: list[InstanceNetlist]

    @property
    def connections(self) -> int:
        return sum(len(instance.pins) for instance in self.instances)


def _scalars(stem: str, port: Port) -> list[str]:
    """Bit-blast `stem` into the names iEDA writes, shaped by the port it reaches.

    Same rule as `Port.bits`, applied to a net rather than to the port's own
    name, so a net on a `[0:0]` port gains the `_0_` its macro pin carries.
    """
    if not port.vectored:
        return [stem]
    return [f"{stem}_{index}_" for index in range(port.width)]


def build_netlist(fabric: Fabric) -> Netlist:
    """Flatten the fabric into scalar ports, wires and macro instances.

    Fails when two tile ports on one net disagree about its shape, or when
    bit-blasting collides two nets onto one scalar name, either of which would
    make the parent assert connectivity the abutment does not provide.
    """
    # Insertion order is the emission order, which walks the grid row by row.
    shape: dict[str, Port] = {}
    driver: dict[str, str] = {}
    read: set[str] = set()
    for instance in fabric.placements():
        tile = fabric.tile_types[instance.tile_type]
        for port_name, net in instance.connections.items():
            port = tile.ports[port_name]
            known = shape.setdefault(net, port)
            if (known.width, known.vectored) != (port.width, port.vectored):
                raise ValueError(
                    f"net {net} is [{known.width}] on {known.name} and [{port.width}] on "
                    f"{instance.name}.{port_name}; fix the tile source that disagrees"
                )
            if port.direction == "output":
                driver[net] = port_name
            else:
                read.add(net)

    # A port name that links to a neighbour on any tile type is a seam signal,
    # and `load_fabric` has already refused to let two tile types disagree about
    # it. So a driven net nobody reads is the end of a chain, such as the last
    # `FrameStrobe_O` of a column, and stays an internal wire; only a name that
    # links nowhere is a fabric output.
    seam_names = {port for (_, port), placement in fabric.sides.items() if not placement.external}

    inputs: list[str] = []
    outputs: list[str] = []
    wires: list[str] = []
    for net, port in shape.items():
        if net not in driver:
            inputs.extend(_scalars(net, port))
        elif net in read or driver[net] in seam_names:
            wires.extend(_scalars(net, port))
        else:
            outputs.extend(_scalars(net, port))

    seen: dict[str, str] = {}
    for net, port in shape.items():
        for scalar in _scalars(net, port):
            if scalar in seen and seen[scalar] != net:
                raise ValueError(
                    f"nets {seen[scalar]} and {net} both bit-blast to {scalar}; "
                    "rename one in eFPGA.v"
                )
            seen[scalar] = net

    instances = [
        InstanceNetlist(
            name=instance.name,
            tile_type=instance.tile_type,
            pins=[
                pair
                for port_name, net in instance.connections.items()
                for pair in zip(
                    _scalars(port_name, fabric.tile_types[instance.tile_type].ports[port_name]),
                    _scalars(net, shape[net]),
                    strict=True,
                )
            ],
        )
        for instance in fabric.placements()
    ]
    return Netlist(inputs=inputs, outputs=outputs, wires=wires, instances=instances)


def plan_die(plan: Plan) -> Die:
    """Size the die so its core is the fabric, in whole `core7` rows.

    Fails when the fabric is not a whole number of site widths across, which
    `DieBuilder::buildCore` would answer by trimming the core and leaving the
    eastmost column of macros outside it.
    """
    if plan.width % SITE_WIDTH:
        raise ValueError(
            f"the fabric is {plan.width} DBU wide, not a multiple of the {SITE_WIDTH} DBU site; "
            "quantise the column widths in flow/plan.py"
        )
    core_height = -(-plan.height // SITE_HEIGHT) * SITE_HEIGHT
    return Die(width=plan.width + 2 * CORE_MARGIN, height=core_height + 2 * CORE_MARGIN)


def _micron(value: int) -> str:
    return f"{value / DBU:.3f}"


def _stub(tile: TileType) -> str:
    """Render one tile type as the blackbox its abstract LEF describes."""
    declarations = [
        f"    {port.direction} {bit.name}"
        for port in tile.ports.values()
        for bit in port.bits(tile.name)
    ]
    return (
        f"(* blackbox *)\nmodule {tile.name} (\n"
        + ",\n".join(declarations)
        + "\n);\nendmodule\n"
    )


def _netlist_text(netlist: Netlist) -> str:
    """Render the parent netlist, ports first, then wires, then the macros."""
    header = [f"    input {name}" for name in netlist.inputs]
    header += [f"    output {name}" for name in netlist.outputs]
    body = [f"wire {name};" for name in netlist.wires]
    for instance in netlist.instances:
        connections = ",\n".join(f"    .{pin}({net})" for pin, net in instance.pins)
        body.append(
            f"\n(* keep *) {instance.tile_type} {instance.name} (\n{connections}\n);"
        )
    return (
        f"module {TOP_MODULE} (\n"
        + ",\n".join(header)
        + "\n);\n\n"
        + "\n".join(body)
        + "\n\nendmodule\n"
    )


def _macro_locations(plan: Plan) -> str:
    """Render `macro_locations.txt`, the fixed placement `iFP` reads."""
    return "".join(
        f"{placement.name} {_micron(placement.x + CORE_MARGIN)} "
        f"{_micron(placement.y + CORE_MARGIN)} {ORIENT}\n"
        for placement in plan.placements
    )


def _sdc() -> str:
    """Render the one clock constraint the fabric takes."""
    return (
        "# One clock for the whole fabric. The tile lib carries arcs from UserCLK to\n"
        "# the tile outputs, so a second create_clock on any other tile clock port\n"
        "# makes iSTA abort with overlapping clock trees at the first seam.\n"
        f"create_clock -name {CLOCK_PORT} -period {1000.0 / CLOCK_MHZ:.1f} "
        f"[get_ports {CLOCK_PORT}]\n"
    )


def _filelist(fabric: Fabric) -> str:
    """Render `filelist.f`, since ECC's `resolve_rtl` reads only `rtl[0]`."""
    return "".join(f"rtl/{name}_stub.v\n" for name in sorted(fabric.tile_types)) + (
        f"rtl/{TOP_MODULE}_flat.v\n"
    )


def _ecc_toml(die: Die) -> str:
    """Render `ecc.toml`, with the die it cannot express recorded as a comment."""
    margin = CORE_MARGIN // DBU
    return f"""[design]
name = "{TOP_MODULE}"
top = "{TOP_MODULE}"
rtl = ["filelist.f"]
clock_port = "{CLOCK_PORT}"
frequency_mhz = {CLOCK_MHZ}

[pdk]
name = "{PDK_NAME}"
root = "{PDK_ROOT}"

# Without this ECC writes its own SDC from clock_port and ignores fabric.sdc.
[pdk.overrides]
sdc = "fabric.sdc"

[flow]
preset = "rtl2gds"
run = "default"

# ECC's parameter registry has no die size, so the {_micron(die.width)} x \
{_micron(die.height)} um die
# these files are built for reaches the run only through
# runs/default/config/fp_default_config.json, as die_builder.mode "die_size" and
# die_builder.die_size. The margin below is what makes that core \
{die.core_rows} core7 rows.
[params.floorplan]
core_margin = [{margin}, {margin}]
"""


def write_project(plan: Plan, fabric: Fabric, directory: Path) -> Netlist:
    """Write the whole parent project into `directory` and return its netlist.

    Fails when the plan and the fabric describe different tile types or
    different instances, which means one of the two was regenerated alone.
    """
    if set(plan.tile_size) != set(fabric.tile_types):
        raise ValueError(
            "the plan and the fabric disagree on tile types: "
            f"{sorted(set(plan.tile_size) ^ set(fabric.tile_types))}; rebuild the plan"
        )
    planned = {placement.name for placement in plan.placements}
    modelled = {instance.name for instance in fabric.placements()}
    if planned != modelled:
        raise ValueError(
            f"the plan and the fabric disagree on {len(planned ^ modelled)} instances; "
            "rebuild the plan"
        )

    netlist = build_netlist(fabric)
    if CLOCK_PORT not in netlist.inputs:
        raise ValueError(
            f"{CLOCK_PORT} is not a top-level input of the flattened fabric, so the SDC "
            "would constrain nothing; check which net eFPGA.v drives the bottom row with"
        )

    rtl = directory / "rtl"
    rtl.mkdir(parents=True, exist_ok=True)
    for name, tile in sorted(fabric.tile_types.items()):
        (rtl / f"{name}_stub.v").write_text(_stub(tile))
    (rtl / f"{TOP_MODULE}_flat.v").write_text(_netlist_text(netlist))
    (directory / "macro_locations.txt").write_text(_macro_locations(plan))
    (directory / "fabric.sdc").write_text(_sdc())
    (directory / "filelist.f").write_text(_filelist(fabric))
    (directory / "ecc.toml").write_text(_ecc_toml(plan_die(plan)))
    return netlist


app = typer.Typer(add_completion=False, help="Generate the fabric-level ECC project.")


@app.command()
def main(
    directory: Annotated[Path, typer.Argument(help="where the parent project is written")],
    project: Annotated[Path, typer.Option(help="the FABulous project directory")] = Path("."),
    plan_file: Annotated[Path, typer.Option(help="the plan flow/plan.py wrote")] = Path(
        "build/fabric_plan.json"
    ),
) -> None:
    """Build the parent project from a FABulous project and its plan."""
    fabric = load_fabric(project)
    plan = Plan.read(plan_file)
    netlist = write_project(plan=plan, fabric=fabric, directory=directory)
    die = plan_die(plan)
    typer.echo(
        f"{len(netlist.instances)} macros of {len(fabric.tile_types)} types, "
        f"{len(netlist.inputs)} input and {len(netlist.outputs)} output scalars, "
        f"{len(netlist.wires)} wires, {netlist.connections} connections, "
        f"die {_micron(die.width)} x {_micron(die.height)} um, {die.core_rows} core7 rows"
    )


if __name__ == "__main__":
    app()


def netlist_text(fabric: Fabric) -> str:
    """Return the bit-blasted `eFPGA` netlist on its own, without the macro project.

    A bottom-up flat build needs the same parent this module writes for the macro
    flow, because a tile's gate netlist carries the same scalar port names its
    abstract LEF does, but it needs none of the stubs, locations or `ecc.toml`.
    """
    return _netlist_text(build_netlist(fabric))
