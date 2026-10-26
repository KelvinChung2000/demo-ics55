"""Write the chip-level netlist and SDC that put `eFPGA_top` inside a signal pad ring.

Every signal pin of the hardened macro reaches the die edge through one
`P65_1233_PBMUX`, except a user IO bit, whose three macro pins share one
bidirectional pad. The pin list comes from `eFPGA_top_Harden.lib` through Yosys,
so the ring follows the macro ECC hardened, which bit-blasts the RTL's buses into
scalars such as `A_IN_top_0`.

Corner, power and ground pads carry no signal and stay out of the netlist: the
physical flow places them and the ring metal joins their USE POWER pins.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PAD_CELL = "P65_1233_PBMUX"
MACRO = "eFPGA_top"
TOP = "top"
SUPPLIES = ("VDD", "VSS", "vdd_stripe_generate", "vss_stripe_generate")
USER_IO_PIN = re.compile(r"A_(IN|OUT|EN)_top_(\d+)")

# `uclk` in flow/sta/full.tcl; the user clock's Fmax is unmeasured.
USER_PERIOD_NS = 10.0
# The IO datasheet's 100 MHz output AC condition. With the PAD pin's own 1.56 pF
# it lands 0.1 pF past the ss Liberty tables' 11.46 pF edge.
BOARD_LOAD_PF = 10.0
# A PBMUX driving that load, 0.99 ns typical rise in the same datasheet table.
BOARD_TRANSITION_NS = 1.0
# flow/sta/full.tcl's hold margin.
HOLD_UNCERTAINTY_NS = 0.05


class Timing(Enum):
    """How the SDC constrains a pad."""

    CONFIG_CLOCK = "config_clock"
    USER_CLOCK = "user_clock"
    # Configuration logic ports, which the macro's timing model carries arcs for.
    CONFIG_IN = "config_in"
    CONFIG_OUT = "config_out"
    # Through the fabric's configurable routing; the timing model has no arcs.
    USER = "user"


@dataclass(frozen=True)
class Signal:
    """A single-pin pad: what the chip calls it, how it is timed and whether it pulls up."""

    port: str
    timing: Timing
    pull_up: bool = False


SIGNALS: dict[str, Signal] = {
    "CLK": Signal("PAD_CLK", Timing.CONFIG_CLOCK),
    "USER_CLK": Signal("PAD_USER_CLK", Timing.USER_CLOCK),
    "USER_RESET": Signal("PAD_USER_RESET", Timing.USER),
    # Pulled so a floating pin holds the loader out of reset and the SPI slave deselected.
    "resetn": Signal("PAD_RSTN", Timing.CONFIG_IN, pull_up=True),
    "spi_cs_n": Signal("PAD_SPI_CSN", Timing.CONFIG_IN, pull_up=True),
    "spi_sck": Signal("PAD_SPI_SCK", Timing.CONFIG_IN),
    "spi_mosi": Signal("PAD_SPI_MOSI", Timing.CONFIG_IN),
    "Rx": Signal("PAD_UART_RX", Timing.CONFIG_IN),
    "ComActive": Signal("PAD_UART_ACTIVE", Timing.CONFIG_OUT),
    "ReceiveLED": Signal("PAD_CFG_LED", Timing.CONFIG_OUT),
    "ConfigBusy": Signal("PAD_CFG_BUSY", Timing.CONFIG_OUT),
    "Configured": Signal("PAD_CFG_DONE", Timing.CONFIG_OUT),
}
USER_IO_PORT = "PAD_IO"


@dataclass(frozen=True)
class Pad:
    """One PBMUX: its chip port and the macro pin or constant on each control pin."""

    port: str
    label: str
    c: str | None
    i: str
    oe: str
    ie: str
    pull_up: bool
    timing: Timing


@dataclass(frozen=True)
class Ring:
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    user_bits: int
    pads: tuple[Pad, ...]


def macro_pins(liberty: Path) -> dict[str, str]:
    """Return each signal pin of the hardened macro and its direction, read by Yosys.

    Fails if Yosys cannot read the Liberty or the library holds no `eFPGA_top`.
    """
    with tempfile.TemporaryDirectory() as scratch:
        dump = Path(scratch) / "macro.json"
        subprocess.run(
            ["yosys", "-q", "-p", f"read_liberty -lib {liberty}; write_json {dump}"],
            check=True,
        )
        modules = json.loads(dump.read_text())["modules"]
    if MACRO not in modules:
        raise ValueError(f"{liberty} defines no {MACRO}, only {sorted(modules)}")
    ports: dict[str, dict[str, object]] = modules[MACRO]["ports"]
    return {
        name: str(port["direction"])
        for name, port in ports.items()
        if name not in SUPPLIES
    }


def build_ring(pins: dict[str, str]) -> Ring:
    """Assign every macro pin to a pad, failing on a pin no pad accounts for."""
    user: dict[int, dict[str, str]] = {}
    singles: list[Pad] = []
    inputs: list[str] = []
    outputs: list[str] = []
    for name, direction in sorted(pins.items()):
        match = USER_IO_PIN.fullmatch(name)
        if match:
            user.setdefault(int(match[2]), {})[match[1]] = name
            continue
        if name not in SIGNALS:
            raise ValueError(f"macro pin {name} has no pad; add it to chiptop.SIGNALS")
        signal = SIGNALS[name]
        if direction == "input":
            pad = Pad(
                signal.port,
                name,
                c=name,
                i="1'b0",
                oe="1'b0",
                ie="1'b1",
                pull_up=signal.pull_up,
                timing=signal.timing,
            )
            inputs.append(signal.port)
        elif direction == "output":
            pad = Pad(
                signal.port,
                name,
                c=None,
                i=name,
                oe="1'b1",
                ie="1'b0",
                pull_up=signal.pull_up,
                timing=signal.timing,
            )
            outputs.append(signal.port)
        else:
            raise ValueError(f"macro pin {name} has direction {direction}")
        singles.append(pad)
    missing = set(SIGNALS) - set(pins)
    if missing:
        raise ValueError(
            f"chiptop.SIGNALS names {sorted(missing)}, which the macro lacks"
        )
    if sorted(user) != list(range(len(user))):
        raise ValueError(f"user IO bits are not contiguous: {sorted(user)}")
    bidirectional = []
    for bit, parts in sorted(user.items()):
        if set(parts) != {"IN", "OUT", "EN"}:
            raise ValueError(f"user IO bit {bit} has only {sorted(parts)}")
        bidirectional.append(
            Pad(
                f"{USER_IO_PORT}[{bit}]",
                f"user IO bit {bit}",
                c=parts["OUT"],
                i=parts["IN"],
                oe=parts["EN"],
                ie="1'b1",
                pull_up=False,
                timing=Timing.USER,
            )
        )
    return Ring(
        tuple(inputs), tuple(outputs), len(user), tuple(singles + bidirectional)
    )


def _instance(index: int, pad: Pad) -> str:
    pins = [
        ("PAD", pad.port),
        ("C", pad.c or ""),
        ("I", pad.i),
        ("OE", pad.oe),
        ("IE", pad.ie),
        ("OD", "1'b0"),
        ("CS", "1'b0"),
        ("PU", "1'b1" if pad.pull_up else "1'b0"),
        ("PD", "1'b0"),
        ("DS0", "1'b0"),
        ("DS1", "1'b0"),
        ("A", ""),
    ]
    body = "".join(f"    .{pin:<3} ({net}),\n" for pin, net in pins)
    return (
        f"// {pad.label}\n{PAD_CELL} u_pad_{index} (\n{body}"
        "    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)\n);\n"
    )


def netlist(ring: Ring, pins: dict[str, str], liberty: Path) -> str:
    """Render the chip top: chip ports, the macro, then one PBMUX per pad."""
    ports = [*ring.inputs, *ring.outputs, USER_IO_PORT]
    declarations = [f"input  {port};" for port in ring.inputs]
    declarations += [f"output {port};" for port in ring.outputs]
    declarations.append(f"inout  [{ring.user_bits - 1}:0] {USER_IO_PORT};")
    width = max(len(name) for name in pins)
    connections = ",\n".join(f"    .{name:<{width}} ({name})" for name in sorted(pins))
    pads = "\n".join(_instance(index, pad) for index, pad in enumerate(ring.pads))
    return f"""\
// Chip-level netlist for the FABulous eFPGA on ICS55, written by `flow cli chip-top`.
// Do not edit; regenerate. The macro's pins are read from {liberty.name}.
//
// {len(ring.pads)} {PAD_CELL} signal pads: {ring.user_bits} bidirectional user IO, each
// joining A_OUT_top_i (pad to fabric), A_IN_top_i (fabric to pad) and A_EN_top_i
// (output enable), and {len(ring.pads) - ring.user_bits} single-pin pads.
// Every pad: OD = 0 push-pull, CS = 0 Schmitt input, DS0 = DS1 = 0 for 16 mA (both
// active low), IE = 1 except on outputs. PU = 1 only on PAD_RSTN and PAD_SPI_CSN.
// Corner and supply pads carry no signal and are placed by the physical flow.

`timescale 1ns / 1ps

module {TOP} (
    {(",\n    ").join(ports)}
);

{chr(10).join(declarations)}

// The ring's supplies; the IO LEF makes them USE POWER / USE GROUND pins.
supply1 VDD;
supply1 VDDIO;
supply0 VSS;
supply0 VSSIO;

wire {(", ").join(sorted(pins))};

{MACRO} u_efpga (
{connections}
);

{pads}
endmodule
"""


def sdc(ring: Ring, config_period_ns: float) -> str:
    """Render the chip-level constraints on the ring's ports."""

    def ports(*timings: Timing, direction: tuple[str, ...]) -> str:
        names = [
            p.port for p in ring.pads if p.timing in timings and p.port in direction
        ]
        if not names:
            raise ValueError(f"no {direction} pad is timed as {timings}")
        return f"[get_ports {{{' '.join(names)}}}]"

    clock = {
        p.timing: p.port
        for p in ring.pads
        if p.timing in (Timing.CONFIG_CLOCK, Timing.USER_CLOCK)
    }
    user_io = f"[get_ports {{{USER_IO_PORT}[*]}}]"
    config_in = ports(Timing.CONFIG_IN, direction=ring.inputs)
    config_out = ports(Timing.CONFIG_OUT, direction=ring.outputs)
    user_in = ports(Timing.USER, direction=ring.inputs)
    return f"""\
# Chip-level constraints for `{TOP}`, written by `flow cli chip-top`.
# Load eFPGA_top from the timing model flow/sta/etm.tcl extracts, not from ECC's
# eFPGA_top_Harden.lib, which has no arcs.
create_clock -name CLK -period {config_period_ns:.1f} [get_ports {clock[Timing.CONFIG_CLOCK]}]
# USER_CLK reaches the fabric only through the SW_term global-buffer muxes and has
# no phase relationship with CLK.
create_clock -name USER_CLK -period {USER_PERIOD_NS:.1f} [get_ports {clock[Timing.USER_CLOCK]}]
set_clock_groups -asynchronous -group CLK -group USER_CLK
# Each clock tree is one pad and a wire, so the pad delay counts from the start.
set_propagated_clock [all_clocks]
set_clock_uncertainty -hold {HOLD_UNCERTAINTY_NS} [all_clocks]

# Board: a {BOARD_LOAD_PF:.0f} pF load on every driven pad and a {BOARD_TRANSITION_NS} ns edge into every pad.
set_load {BOARD_LOAD_PF} [all_outputs]
set_input_transition {BOARD_TRANSITION_NS} [all_inputs]

# Configuration logic: zero board delay, so each path is the pad plus the macro's
# own arc and must fit one CLK period. The host's own delay comes out of the slack.
set_input_delay 0 -clock CLK {config_in}
set_output_delay 0 -clock CLK {config_out}
# The inputs come from a host on its own clock into synchronisers (SPI a 4-flop
# sampler, Rx one flop, resetn an asynchronous clear), so a hold check against CLK
# describes no real transfer; setup still bounds the pad-to-sampler delay.
set_false_path -hold -from {config_in}

# User IO and the user reset pass through configurable routing, whose timing
# depends on the bitstream, so nothing at chip level times them.
set_input_delay 0 -clock USER_CLK {user_in}
set_input_delay 0 -clock USER_CLK {user_io}
set_output_delay 0 -clock USER_CLK {user_io}
set_false_path -from {user_in}
set_false_path -from {user_io}
set_false_path -to {user_io}
"""


def write(liberty: Path, directory: Path, config_period_ns: float) -> Ring:
    """Write `top.v` and `top.sdc` into `directory` for the macro `liberty` describes."""
    pins = macro_pins(liberty)
    ring = build_ring(pins)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "top.v").write_text(netlist(ring, pins, liberty))
    (directory / "top.sdc").write_text(sdc(ring, config_period_ns))
    return ring
