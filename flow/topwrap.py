"""Write a variant's `eFPGA_top`: its fabric, the frame loader and the serial front-ends.

FABulous writes its top wrapper once, for the grid it was generated with, around
a `ConfigFSM` that reads a fixed number of row words per frame. Change the grid
and that count goes stale while `bit_gen` keeps emitting one word per row, so
every frame after the first loads misaligned. This top is written from the
variant's own `eFPGA.v` instead. The loader is `fabric_config` from
fabulous-fabrics, sized by the row and column counts the grid has, and the words
it takes come from `config_frontend`, which serves UART, bitbang and SPI. Its
32-bit parallel port and the bitbang port are tied off, since the MPW allows 36
pads: only UART and SPI reach a pin.

A tile port `eFPGA.v` marks `//EXTERNAL` becomes one bit of a top-level bus
named after the port, numbered the way FABulous numbers them: bottom row first,
west to east within a row. A user design's pin constraints index those buses, so
keeping FABulous's order is what lets a wrapper written against the old top load
unchanged. `CONFIGURED_top` is the exception. It tells a BEL the fabric has
finished loading, which only the loader knows, so `configured_o` drives it
rather than a pin. A one-bit port in `PAD_NAMES` is the other exception: it
becomes a scalar named for what the pad carries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from flow.fabric import Fabric
from flow.topdesign import Netlist
from flow.variant import Paths

# The header word carries the column in its top five bits, as `bit_gen` writes it.
FRAME_SELECT_WIDTH = 5
CONFIGURED_PORT = "CONFIGURED_top"
# The SW_term pads: SYS_RESET carries the user reset and USER_CLK the user clock,
# each reaching the fabric only through the global-buffer input muxes.
PAD_NAMES = {
    "SYS_RESET_RESET_top": "USER_RESET",
    "USER_CLOCK_top": "USER_CLK",
}

EXTERNAL_RE = re.compile(
    r"^\s*(input|output)\s+Tile_X(\d+)Y(\d+)_(\w+)\s*,?\s*//EXTERNAL\s*$", re.M
)
PARAMETER_RE = re.compile(r"parameter\s+(MaxFramesPerCol|FrameBitsPerRow)\s*=\s*(\d+)")


@dataclass(frozen=True)
class External:
    direction: Literal["input", "output"]
    x: int
    y: int
    port: str

    @property
    def scalar(self) -> str:
        return f"Tile_X{self.x}Y{self.y}_{self.port}"


def read_externals(text: str) -> dict[str, list[External]]:
    """Group `eFPGA.v`'s external scalars by port, each bus in FABulous's order."""
    buses: dict[str, list[External]] = {}
    for direction, x, y, port in EXTERNAL_RE.findall(text):
        buses.setdefault(port, []).append(External(direction, int(x), int(y), port))
    if not buses:
        raise ValueError("eFPGA.v declares no //EXTERNAL tile port")
    for port, bits in buses.items():
        if len({bit.direction for bit in bits}) != 1:
            raise ValueError(f"{port} is an input on one tile and an output on another")
        bits.sort(key=lambda bit: (-bit.y, bit.x))
    return buses


def _frame_parameters(text: str, source: str) -> tuple[int, int]:
    parameters = dict(PARAMETER_RE.findall(text))
    if parameters.keys() != {"MaxFramesPerCol", "FrameBitsPerRow"}:
        raise ValueError(f"{source} does not declare MaxFramesPerCol and FrameBitsPerRow")
    return int(parameters["MaxFramesPerCol"]), int(parameters["FrameBitsPerRow"])


def bindings(text: str) -> dict[str, str]:
    """Map every external tile scalar to the top-level expression it connects to."""
    bound = {}
    externals = read_externals(text)
    for port in sorted(externals, key=lambda name: (name == CONFIGURED_PORT, name)):
        if port in PAD_NAMES:
            (bit,) = _single_bit(port, externals[port])
            bound[bit.scalar] = PAD_NAMES[port]
            continue
        for index, bit in enumerate(externals[port]):
            bound[bit.scalar] = "configured" if port == CONFIGURED_PORT else f"{port}[{index}]"
    return bound


def _single_bit(port: str, bits: list[External]) -> list[External]:
    if len(bits) != 1:
        raise ValueError(f"{port} is {len(bits)} bits wide; a named pad must be one")
    return bits


def _port_declaration(port: str, bits: list[External]) -> tuple[str, str]:
    if port in PAD_NAMES:
        (bit,) = _single_bit(port, bits)
        return PAD_NAMES[port], f"    {bit.direction} wire {PAD_NAMES[port]},"
    return port, f"    {bits[0].direction} wire [{len(bits) - 1}:0] {port},"


def _rtl_body(text: str) -> str:
    connections = [f"        .{scalar}({net})," for scalar, net in bindings(text).items()]
    return f"""    eFPGA #(
        .MaxFramesPerCol(MAX_FRAMES_PER_COL),
        .FrameBitsPerRow(FRAME_BITS_PER_ROW)
    ) fabric (
{chr(10).join(connections)}
        .FrameData(frame_data),
        .FrameStrobe(frame_strobe)
    );
"""


def _hard_body(text: str, netlist: Netlist, frame_bits: int, frames: int) -> str:
    """Instantiate every macro under its own name, the frame bits wired to the loader.

    The macros keep the names `eFPGA.v` gives them, so the placements the plan
    derived for the fabric-level run bind here unchanged. A frame bit reaches the
    fabric as one scalar per row or column in the macro netlist, and is wired to
    the bit of `frame_data` or `frame_strobe` `eFPGA.v` slices it from.
    """
    bound = bindings(text)
    frame_re = re.compile(r"^Row_Y(\d+)_FrameData_(\d+)$|^Column_X(\d+)_FrameStrobe_(\d+)$")

    def net_of(name: str) -> str:
        if name in bound:
            return bound[name]
        frame = frame_re.match(name)
        if frame is None:
            return name
        row, bit, column, strobe = frame.groups()
        if row is not None:
            return f"frame_data[{int(row) * frame_bits + int(bit)}]"
        return f"frame_strobe[{int(column) * frames + int(strobe)}]"

    unbound = sorted(set(netlist.inputs) | set(netlist.outputs))
    unbound = [name for name in unbound if net_of(name) == name]
    if unbound:
        raise ValueError(
            f"{len(unbound)} fabric boundary scalars bind to no top-level signal: {unbound[:4]}"
        )
    lines = [f"    wire {name};" for name in netlist.wires]
    for instance in netlist.instances:
        pins = ",\n".join(f"        .{pin}({net_of(net)})" for pin, net in instance.pins)
        # Kept, since a tile whose outputs the top never reads, such as NE_term,
        # is otherwise swept away and its placement then names nothing.
        lines.append(f"    (* keep *) {instance.tile_type} {instance.name} (\n{pins}\n    );")
    return "\n".join(lines) + "\n"


def render(fabric: Fabric, text: str, source: str, netlist: Netlist | None = None) -> str:
    """Return the top for one variant's `eFPGA.v`.

    Without `netlist` the fabric is one `eFPGA` instance, for simulation. With
    it, the fabric is the macro netlist `flow.topdesign` flattens `eFPGA.v` to,
    which is what the top-level ECC run synthesises around.
    """
    frames, frame_bits = _frame_parameters(text, source)
    if fabric.columns > 1 << FRAME_SELECT_WIDTH:
        raise ValueError(
            f"{fabric.columns} columns do not fit the {FRAME_SELECT_WIDTH}-bit column "
            "field of a frame header"
        )
    buses = read_externals(text)
    ports = [
        line
        for _, line in sorted(
            _port_declaration(port, bits)
            for port, bits in buses.items()
            if port != CONFIGURED_PORT
        )
    ]
    body = _rtl_body(text) if netlist is None else _hard_body(text, netlist, frame_bits, frames)
    return f"""// Written by flow/topwrap.py from {source}; regenerate with `flow gen-top`.
`default_nettype none

module eFPGA_top (
{chr(10).join(ports)}
    // Configuration clock and reset. The fabric's own clock arrives on a pad
    // through the global buffers, since the grid sets DisableUserCLK.
    input wire CLK,
    input wire resetn,
    input wire Rx,
    output wire ComActive,
    output wire ReceiveLED,
    input wire spi_sck,
    input wire spi_cs_n,
    input wire spi_mosi,
    output wire ConfigBusy,
    output wire Configured
);
    localparam integer FRAME_BITS_PER_ROW = {frame_bits};
    localparam integer MAX_FRAMES_PER_COL = {frames};
    localparam integer NUM_ROWS = {fabric.rows};
    localparam integer NUM_COLUMNS = {fabric.columns};

    wire [31:0] bitstream_data;
    wire bitstream_valid;
    wire configured;
    wire [FRAME_BITS_PER_ROW*NUM_ROWS-1:0] frame_data;
    wire [MAX_FRAMES_PER_COL*NUM_COLUMNS-1:0] frame_strobe;

    assign Configured = configured;

    config_frontend frontend (
        .CLK(CLK),
        .resetn(resetn),
        .Rx(Rx),
        .ComActive(ComActive),
        .ReceiveLED(ReceiveLED),
        .s_clk(1'b0),
        .s_data(1'b0),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .SelfWriteData(32'b0),
        .SelfWriteStrobe(1'b0),
        .bitstream_data(bitstream_data),
        .bitstream_valid(bitstream_valid)
    );

    fabric_config #(
        .FRAME_BITS_PER_ROW(FRAME_BITS_PER_ROW),
        .MAX_FRAMES_PER_COL(MAX_FRAMES_PER_COL),
        .FRAME_SELECT_WIDTH({FRAME_SELECT_WIDTH}),
        .FABRIC_NUM_COLUMNS(NUM_COLUMNS),
        .FABRIC_NUM_ROWS(NUM_ROWS)
    ) loader (
        .clk_i(CLK),
        .rst_ni(resetn),
        .bitstream_data_i(bitstream_data),
        .bitstream_valid_i(bitstream_valid),
        .busy_o(ConfigBusy),
        .configured_o(configured),
        .frame_data_o(frame_data),
        .frame_strobe_o(frame_strobe)
    );

{body}endmodule

`default_nettype wire
"""


def write_top(paths: Paths, fabric: Fabric) -> tuple[int, dict[str, int]]:
    """Write `fabrics/<variant>/Fabric/eFPGA_top.v`, returning its size and bus widths."""
    text = paths.fabric_verilog.read_text()
    source = str(paths.fabric_verilog.relative_to(paths.root))
    top = paths.fabric / "Fabric" / "eFPGA_top.v"
    top.write_text(render(fabric, text, source))
    widths = {port: len(bits) for port, bits in read_externals(text).items()}
    return top.stat().st_size, widths
