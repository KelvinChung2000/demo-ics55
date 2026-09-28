"""Write a variant's `eFPGA_top`: its fabric, the frame loader and the serial front-ends.

FABulous writes its top wrapper once, for the grid it was generated with, around
a `ConfigFSM` that reads a fixed number of row words per frame. Change the grid
and that count goes stale while `bit_gen` keeps emitting one word per row, so
every frame after the first loads misaligned. This top is written from the
variant's own `eFPGA.v` instead. The loader is `fabric_config` from
fabulous-fabrics, sized by the row and column counts the grid has, and the words
it takes come from `config_frontend`, which serves UART, bitbang, SPI and the
parallel port.

A tile port `eFPGA.v` marks `//EXTERNAL` becomes one bit of a top-level bus
named after the port, numbered the way FABulous numbers them: bottom row first,
west to east within a row. A user design's pin constraints index those buses, so
keeping FABulous's order is what lets a wrapper written against the old top load
unchanged. `CONFIGURED_top` is the exception. It tells a BEL the fabric has
finished loading, which only the loader knows, so `configured_o` drives it
rather than a pin.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from flow.fabric import Fabric
from flow.variant import Paths

# The header word carries the column in its top five bits, as `bit_gen` writes it.
FRAME_SELECT_WIDTH = 5
CONFIGURED_PORT = "CONFIGURED_top"

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


def render(fabric: Fabric, text: str, source: str) -> str:
    """Return the top-level Verilog for one variant's generated `eFPGA.v`."""
    parameters = dict(PARAMETER_RE.findall(text))
    if parameters.keys() != {"MaxFramesPerCol", "FrameBitsPerRow"}:
        raise ValueError(f"{source} does not declare MaxFramesPerCol and FrameBitsPerRow")
    frames, frame_bits = int(parameters["MaxFramesPerCol"]), int(parameters["FrameBitsPerRow"])
    if fabric.columns > 1 << FRAME_SELECT_WIDTH:
        raise ValueError(
            f"{fabric.columns} columns do not fit the {FRAME_SELECT_WIDTH}-bit column "
            "field of a frame header"
        )
    buses = read_externals(text)
    pins = {port: scalars for port, scalars in buses.items() if port != CONFIGURED_PORT}

    ports = [
        f"    {scalars[0].direction} wire [{len(scalars) - 1}:0] {port},"
        for port, scalars in sorted(pins.items())
    ]
    connections = [
        f"        .{bit.scalar}({port}[{index}]),"
        for port, scalars in sorted(pins.items())
        for index, bit in enumerate(scalars)
    ] + [
        f"        .{bit.scalar}(configured),"
        for bit in buses.get(CONFIGURED_PORT, [])
    ]
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
    input wire s_clk,
    input wire s_data,
    input wire spi_sck,
    input wire spi_cs_n,
    input wire spi_mosi,
    input wire [31:0] SelfWriteData,
    input wire SelfWriteStrobe,
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
        .s_clk(s_clk),
        .s_data(s_data),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .SelfWriteData(SelfWriteData),
        .SelfWriteStrobe(SelfWriteStrobe),
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

    eFPGA #(
        .MaxFramesPerCol(MAX_FRAMES_PER_COL),
        .FrameBitsPerRow(FRAME_BITS_PER_ROW)
    ) fabric (
{chr(10).join(connections)}
        .FrameData(frame_data),
        .FrameStrobe(frame_strobe)
    );
endmodule

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
