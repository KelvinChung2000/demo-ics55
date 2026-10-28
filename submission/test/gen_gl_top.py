"""Write the gate-level testbench top for the hardened eFPGA_top netlist.

The ECC netlist of eFPGA_top (``top_full.v``) names its ports per bit
(``A_EN_top_3``), while the testbench connects the RTL's vectors
(``A_EN_top[3]``). This writes ``eFPGA_top_gl``, which carries the RTL port list
and instantiates the netlist as ``gl``, mapping each RTL port bit ``p[i]`` to the
netlist port ``p_i`` (``p`` for a one-bit port). Every netlist port must be
claimed exactly once, so a renamed or missing port fails here.

The wrapper also takes an X census of every sequential cell when ``Configured``
rises: a configuration latch still X then was never written, which no later
stimulus can fix. Sequential cells are told apart by the latch or flip-flop
yosys builds from their Liberty ``latch``/``ff`` group. The census reads values
only; it forces and deposits nothing.

With ``--chip``, the wrapper is ``eFPGA_chip_gl`` instead: the same RTL port
list, but driving and reading only the ``PAD_*`` ports of the chip-level
``top`` (submission/chip/top.v), so every signal crosses a P65_1233_PBMUX model.
The pad each RTL bit uses is read from ``top``'s connections, and every netlist
port must reach exactly one pad. A bidirectional pad is the tester's pin: the
tester drives it with the RTL input bit where ``<input>_drive`` is 1 and leaves
it at Z elsewhere. The output enable is then what the pad shows, Z or not, but
only on undriven pins; on a driven pin an enabled output shows only as the X of
contention, so one driving the same value as the tester goes unseen.

The wrapper also forces the output of every logic cell (``FABULOUS_LC``) whose
loaded configuration makes it a constant (``FF`` = 0 and ``INIT`` all 0 or all 1)
to that constant once ``Configured`` rises. In silicon such a cell drives the
constant for any input. The gate-level LUT turns an X on an unused input into
an X on its output, and that X circulates through unused LUTs and default
routing that no reset reaches, so without the force it leaks into used logic.
The cells and values come from the configuration latches at run time, so a
wrong bitstream still fails. A gate-level fault inside an unused cell's own
logic is masked; that needs an equivalence check, not this simulation. The
INIT and FF positions come from the cell's ``BelMap``, and the latch behind
each bit from the tile RTL and its ConfigMem.

Both designs are read by yosys; nothing here parses Verilog.

    python3 gen_gl_top.py --rtl ../rtl/eFPGA/eFPGA_top.v \
        --netlist build/gl_chip/top_full.v build/gl_chip/tile_*.v \
        --liberty <pdk>/<lib>.lib ... [--chip ../chip/top.v] \
        --lc-cell ../rtl/primitives/FABULOUS_LC/fabulous/FABULOUS_LC.v \
        --lc-tile ../rtl/Tile/LUT4x8_ha --out build/gl_chip/eFPGA_top_gl.v
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

TOP = "eFPGA_top"
WRAPPER = "eFPGA_top_gl"
INSTANCE = "gl"
CHIP_TOP = "top"
CHIP_WRAPPER = "eFPGA_chip_gl"
CHIP_INSTANCE = "chip"
PAD_CELL = "P65_1233_PBMUX"
LC_CELL = "FABULOUS_LC"
CONFIG_LATCH = "config_latch"
LATCH_Q = "Q"
SIMPLE_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
# How many X cells of one scope the census names before it only counts.
CENSUS_NAMED = 10


class Kind(Enum):
    LATCH = "latch"
    FLOP = "flop"

    @property
    def plural(self) -> str:
        return {Kind.LATCH: "latches", Kind.FLOP: "flops"}[self]


@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    width: int
    offset: int


@dataclass(frozen=True)
class Sequential:
    scope: str  # tile type, or the top module for the configuration logic
    path: tuple[str, ...]  # instance names below the netlist top
    outputs: tuple[str, ...]
    kind: Kind


@dataclass(frozen=True)
class Pad:
    pad: str  # chip port bit
    to_core: str | None  # RTL bit driven by the pad's C
    from_core: str | None  # RTL bit on the pad's I
    enable: str | None  # RTL bit on the pad's OE, None when OE is tied


@dataclass(frozen=True)
class LogicCell:
    path: tuple[str, ...]  # tile instance path below the netlist top
    init: tuple[str, ...]  # tile net of the latch behind each INIT bit, INIT[0] first
    ff: str  # tile net of the latch behind FF
    out: str  # tile net of the cell output O


def yosys_json(script: str, yosys: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "design.json"
        ys = Path(tmp) / "design.ys"
        ys.write_text(f"{script}\nwrite_json {out}\n")
        subprocess.run([yosys, "-q", "-s", str(ys)], check=True)
        return json.loads(out.read_text())["modules"]


def ports(module: dict) -> list[Port]:
    found: list[Port] = []
    for name, p in module["ports"].items():
        if p.get("upto", 0) and len(p["bits"]) > 1:
            raise ValueError(
                f"{name} is declared [lo:hi]; the bit mapping assumes [hi:lo]"
            )
        found.append(
            Port(
                name=name,
                direction=p["direction"],
                width=len(p["bits"]),
                offset=p.get("offset", 0),
            )
        )
    return found


def bit_map(rtl: list[Port], netlist: list[Port]) -> list[tuple[str, str]]:
    """Pair each netlist port with the RTL port bit it carries."""
    gl = {p.name: p for p in netlist}
    for p in netlist:
        if p.width != 1:
            raise ValueError(
                f"netlist port {p.name} is {p.width} bits wide; expected scalar ports"
            )
    pairs: list[tuple[str, str]] = []
    for p in rtl:
        for i in range(p.offset, p.offset + p.width):
            name = p.name if p.width == 1 else f"{p.name}_{i}"
            q = gl.pop(name, None)
            if q is None:
                raise ValueError(f"RTL bit {p.name}[{i}] has no netlist port {name}")
            if q.direction != p.direction:
                raise ValueError(
                    f"{name} is {q.direction} in the netlist, {p.direction} in RTL"
                )
            pairs.append((name, p.name if p.width == 1 else f"{p.name}[{i}]"))
    if gl:
        raise ValueError(f"netlist ports with no RTL bit: {sorted(gl)}")
    return pairs


def sequential_kinds(modules: dict) -> dict[str, Kind]:
    """Classify Liberty cells by the storage element yosys built for them."""
    kinds: dict[str, Kind] = {}
    for name, m in modules.items():
        types = {c["type"] for c in m.get("cells", {}).values()}
        if any(t.startswith("$_DLATCH") for t in types):
            kinds[name] = Kind.LATCH
        elif any(t.startswith("$_DFF") for t in types):
            kinds[name] = Kind.FLOP
    return kinds


def sequentials(
    modules: dict, cells: set[str], kinds: dict[str, Kind]
) -> list[Sequential]:
    def outputs(cell_type: str) -> tuple[str, ...]:
        return tuple(
            n
            for n, p in modules[cell_type]["ports"].items()
            if p["direction"] == "output"
        )

    def walk(module: str, prefix: tuple[str, ...]) -> list[Sequential]:
        found: list[Sequential] = []
        for inst, cell in modules[module]["cells"].items():
            t = cell["type"]
            if t in kinds:
                found.append(
                    Sequential(
                        scope=module,
                        path=(*prefix, inst),
                        outputs=outputs(t),
                        kind=kinds[t],
                    )
                )
            elif t in modules and t not in cells:
                found.extend(walk(t, (*prefix, inst)))
        return found

    return walk(TOP, ())


def physical_only(modules: dict, cells: set[str]) -> list[str]:
    """Cells the netlist places that connect no pin (fill, decap, tap).

    Some are in the Liberty without pins, some (FILLER*, FILLTAP*) are in no
    Liberty at all. The PDK ships no Verilog model for either, and with nothing
    connected they carry no logic, so the wrapper file declares them empty. A
    cell type known to no library fails here unless no instance connects a pin.
    """
    netlist = [m for name, m in modules.items() if name not in cells]
    insts = [c for m in netlist for c in m["cells"].values()]
    unknown = {c["type"] for c in insts if c["type"] not in modules}
    wired = sorted(
        {c["type"] for c in insts if c["type"] in unknown and c["connections"]}
    )
    if wired:
        raise ValueError(f"cell types in no library with pins connected: {wired}")
    pinless = {
        c["type"]
        for c in insts
        if c["type"] in cells and not modules[c["type"]]["ports"]
    }
    return sorted(unknown | pinless)


def ident(name: str) -> str:
    return name if SIMPLE_ID.fullmatch(name) else f"\\{name} "


def ref(*parts: str) -> str:
    return ".".join(ident(p) for p in parts)


def census(seq: list[Sequential], prefix: tuple[str, ...]) -> list[str]:
    scopes = sorted({(s.kind, s.scope) for s in seq}, key=lambda k: (k[0].value, k[1]))
    var = {k: f"n_{k[0].value}_{k[1]}" for k in scopes}
    total = {k: sum(1 for s in seq if (s.kind, s.scope) == k) for k in scopes}
    lines = [
        "    // X census of every sequential cell when Configured rises. Read-only.",
        "    initial begin : census",
        *(f"        integer {v};" for v in var.values()),
        "        @(posedge Configured);",
        "        #1;",
        *(f"        {v} = 0;" for v in var.values()),
    ]
    for s in seq:
        v = var[(s.kind, s.scope)]
        outs = ", ".join(ref(*prefix, *s.path, o) for o in s.outputs)
        name = ".".join(s.path)
        lines.append(
            f"        if ((^{{{outs}}}) === 1'bx) begin "
            f'if ({v} < {CENSUS_NAMED}) $display("[gl_census] X {s.kind.value} {name}"); '
            f"{v} = {v} + 1; end"
        )
    for k in scopes:
        lines.append(
            f'        $display("[gl_census] Configured @ %0t: %0d of {total[k]} {k[0].plural} in {k[1]} X", '
            f"$time, {var[k]});"
        )
    lines.append("    end")
    return lines


def lc_layout(cell_v: Path, yosys: str) -> tuple[list[int], int]:
    """INIT and FF positions in the logic cell's ConfigBits, from its BelMap."""
    attrs = yosys_json(f"read_verilog -lib {cell_v}", yosys)[LC_CELL]["attributes"]
    if "BelMap" not in attrs:
        raise ValueError(f"{LC_CELL} in {cell_v} carries no BelMap")
    init: list[int] = []
    while (key := "INIT" if not init else f"INIT_{len(init)}") in attrs:
        init.append(int(attrs[key], 2))
    if "FF" not in attrs or not init:
        raise ValueError(f"the BelMap of {LC_CELL} names no INIT or no FF bit")
    return init, int(attrs["FF"], 2)


def lc_latches(tile_dir: Path, yosys: str) -> dict[str, list[str]]:
    """Each logic cell of a tile, with the latch net behind each of its ConfigBits."""
    name = tile_dir.name
    mem_type = f"{name}_ConfigMem"
    rtl = yosys_json(f"read_verilog {tile_dir / name}.v {tile_dir / mem_type}.v", yosys)
    tile = rtl[name]
    mems = [(n, c) for n, c in tile["cells"].items() if c["type"] == mem_type]
    if len(mems) != 1:
        raise ValueError(f"{name} instantiates {mem_type} {len(mems)} times")
    mem_inst, mem = mems[0]
    index = {b: j for j, b in enumerate(mem["connections"]["ConfigBits"])}
    port = rtl[mem_type]["ports"]["ConfigBits"]["bits"]
    latch_of = {
        c["connections"][LATCH_Q][0]: n
        for n, c in rtl[mem_type]["cells"].items()
        if c["type"] == CONFIG_LATCH
    }
    found: dict[str, list[str]] = {}
    for inst, cell in tile["cells"].items():
        if cell["type"] != LC_CELL:
            continue
        nets: list[str] = []
        for b in cell["connections"]["ConfigBits"]:
            if b not in index or port[index[b]] not in latch_of:
                raise ValueError(f"{name}.{inst} has a ConfigBits bit no latch drives")
            nets.append(f"{mem_inst}.{latch_of[port[index[b]]]}.{LATCH_Q}")
        found[inst] = nets
    if not found:
        raise ValueError(f"{name} holds no {LC_CELL}")
    return found


def logic_cells(
    modules: dict,
    kinds: dict[str, Kind],
    layout: tuple[list[int], int],
    tiles: dict[str, dict[str, list[str]]],
) -> list[LogicCell]:
    """Every logic cell of the netlist, its nets checked against the gate-level tile."""
    init_at, ff_at = layout
    found: list[LogicCell] = []
    for tile, cells in tiles.items():
        if tile not in modules:
            raise ValueError(f"tile {tile} is not in the netlist")
        m = modules[tile]
        latch_q = {
            b
            for c in m["cells"].values()
            if kinds.get(c["type"]) is Kind.LATCH
            for pin, bits in c["connections"].items()
            if modules[c["type"]]["ports"][pin]["direction"] == "output"
            for b in bits
        }
        for inst, nets in cells.items():
            out = f"{inst}.O"
            if out not in m["netnames"]:
                raise ValueError(f"{tile} netlist has no net {out}")
            for net in nets:
                if (
                    net not in m["netnames"]
                    or not set(m["netnames"][net]["bits"]) & latch_q
                ):
                    raise ValueError(f"{tile} netlist net {net} is not a latch output")
            for path in instances(modules, TOP, tile, ()):
                found.append(
                    LogicCell(
                        path=path,
                        init=tuple(nets[i] for i in init_at),
                        ff=nets[ff_at],
                        out=out,
                    )
                )
    return found


def instances(
    modules: dict, module: str, cell_type: str, prefix: tuple[str, ...]
) -> list[tuple[str, ...]]:
    found: list[tuple[str, ...]] = []
    for inst, cell in modules[module]["cells"].items():
        if cell["type"] == cell_type:
            found.append((*prefix, inst))
        elif cell["type"] in modules and modules[cell["type"]]["cells"]:
            found.extend(instances(modules, cell["type"], cell_type, (*prefix, inst)))
    return found


def constant_cells(lcs: list[LogicCell], prefix: tuple[str, ...]) -> list[str]:
    lines = [
        "    // Force each logic cell its loaded config makes constant to that constant.",
        "    initial begin : constant_cells",
        "        integer n;",
        "        @(posedge Configured);",
        "        n = 0;",
    ]
    for lc in lcs:
        cfg = ", ".join(ref(*prefix, *lc.path, n) for n in (lc.ff, *reversed(lc.init)))
        o = ref(*prefix, *lc.path, lc.out)
        w = 1 + len(lc.init)
        ones = (1 << len(lc.init)) - 1
        lines += [
            f"        if ({{{cfg}}} === {w}'h0) begin force {o} = 1'b0; n = n + 1; end",
            f"        if ({{{cfg}}} === {w}'h{ones:x}) begin force {o} = 1'b1; n = n + 1; end",
        ]
    lines.append(
        f'        $display("[gl_const] Configured @ %0t: %0d of {len(lcs)} logic cells forced constant", '
        "$time, n);"
    )
    lines.append("    end")
    return lines


def bit_names(port: dict, name: str) -> list[tuple[int | str, str]]:
    """(yosys bit, Verilog name) for each bit of a yosys JSON port."""
    bits = port["bits"]
    if len(bits) == 1 and port.get("offset", 0) == 0:
        return [(bits[0], name)]
    off = port.get("offset", 0)
    return [(b, f"{name}[{off + i}]") for i, b in enumerate(bits)]


def chip_pads(modules: dict, pairs: list[tuple[str, str]]) -> tuple[str, list[Pad]]:
    """The macro instance name in ``top`` and the RTL bits each pad carries."""
    top = modules[CHIP_TOP]
    macro = [n for n, c in top["cells"].items() if c["type"] == TOP]
    if len(macro) != 1:
        raise ValueError(
            f"{CHIP_TOP} instantiates {TOP} {len(macro)} times; expected once"
        )
    others = {c["type"] for c in top["cells"].values()} - {TOP, PAD_CELL}
    if others:
        raise ValueError(
            f"{CHIP_TOP} holds cells other than {TOP} and {PAD_CELL}: {sorted(others)}"
        )
    conn = top["cells"][macro[0]]["connections"]
    rtl_of: dict[int | str, str] = {}
    for gl, rtl in pairs:
        bits = conn.get(gl, [])
        if len(bits) != 1 or not isinstance(bits[0], int):
            raise ValueError(f"{TOP} port {gl} is not wired to a net in {CHIP_TOP}")
        rtl_of[bits[0]] = rtl
    pad_of = {b: n for name, p in top["ports"].items() for b, n in bit_names(p, name)}

    def pin(cell: dict, name: str) -> int | str | None:
        bits = cell["connections"].get(name, [])
        return bits[0] if bits else None

    pads: list[Pad] = []
    for inst, cell in sorted(top["cells"].items()):
        if cell["type"] != PAD_CELL:
            continue
        pad = pad_of.get(pin(cell, "PAD"))
        if pad is None:
            raise ValueError(f"pad {inst} reaches no port of {CHIP_TOP}")
        c, i, oe = (pin(cell, n) for n in ("C", "I", "OE"))
        p = Pad(
            pad=pad,
            to_core=rtl_of.get(c),
            from_core=rtl_of.get(i),
            enable=rtl_of.get(oe),
        )
        is_input = p.to_core and not p.from_core and oe == "0"
        is_output = p.from_core and not p.to_core and oe == "1"
        is_bidir = p.to_core and p.from_core and p.enable
        if not (is_input or is_output or is_bidir):
            raise ValueError(
                f"pad {inst} on {pad} is neither input, output nor bidirectional"
            )
        pads.append(p)
    used = [b for p in pads for b in (p.to_core, p.from_core, p.enable) if b]
    missing = sorted(set(rtl_of.values()) - set(used))
    twice = sorted({b for b in used if used.count(b) > 1})
    if missing or twice:
        raise ValueError(f"RTL bits on no pad: {missing}; on more than one: {twice}")
    return macro[0], pads


def drive_bit(rtl_bit: str) -> str:
    name, _, idx = rtl_bit.partition("[")
    return f"{name}_drive[{idx}" if idx else f"{name}_drive"


def chip_wrapper(
    rtl: list[Port],
    chip: dict,
    macro: str,
    pads: list[Pad],
    seq: list[Sequential],
    lcs: list[LogicCell],
    stubs: list[str],
    sources: str,
) -> str:
    def rng(width: int, offset: int) -> str:
        return "" if width == 1 and offset == 0 else f"[{offset + width - 1}:{offset}] "

    driven = {p.to_core.partition("[")[0] for p in pads if p.enable and p.to_core}
    decls = [f"    {p.direction} wire {rng(p.width, p.offset)}{p.name}" for p in rtl]
    decls += [
        f"    input wire {rng(p.width, p.offset)}{p.name}_drive"
        for p in rtl
        if p.name in driven
    ]
    top_ports = chip[CHIP_TOP]["ports"]
    nets = [
        f"    wire {rng(len(p['bits']), p.get('offset', 0))}{n};"
        for n, p in top_ports.items()
    ]
    body: list[str] = []
    for p in pads:
        if p.enable and p.to_core and p.from_core:
            d = drive_bit(p.to_core)
            body += [
                f"    assign {p.pad} = {d} ? {p.to_core} : 1'bz;",
                f"    assign {p.from_core} = {p.pad};",
                f"    assign {p.enable} = {d} ? (({p.pad} === 1'bx) ? 1'bx : 1'b0) : ({p.pad} !== 1'bz);",
            ]
        elif p.to_core:
            body.append(f"    assign {p.pad} = {p.to_core};")
        else:
            body.append(f"    assign {p.from_core} = {p.pad};")
    conns = ",\n".join(f"        .{n}({n})" for n in top_ports)
    return "\n".join(
        [
            f"// Written by test/gen_gl_top.py from {sources}; do not edit by hand.",
            "`timescale 1ns / 1ps",
            "`default_nettype none",
            "",
            f"module {CHIP_WRAPPER} (",
            ",\n".join(decls),
            ");",
            *nets,
            f"    {CHIP_TOP} {CHIP_INSTANCE} (",
            conns,
            "    );",
            "",
            "    // The tester drives a bidirectional pin only where <input>_drive is 1.",
            *body,
            "",
            *census(seq, (CHIP_INSTANCE, macro)),
            "",
            *constant_cells(lcs, (CHIP_INSTANCE, macro)),
            "",
            "endmodule",
            "",
            "// Physical-only cells: no pins, no logic, no PDK model.",
            *(f"module {t} ();\nendmodule" for t in stubs),
            "`default_nettype wire",
            "",
        ]
    )


def wrapper(
    rtl: list[Port],
    pairs: list[tuple[str, str]],
    seq: list[Sequential],
    lcs: list[LogicCell],
    stubs: list[str],
    sources: str,
) -> str:
    def decl(p: Port) -> str:
        rng = (
            ""
            if p.width == 1 and p.offset == 0
            else f"[{p.offset + p.width - 1}:{p.offset}] "
        )
        return f"    {p.direction} wire {rng}{p.name}"

    conns = ",\n".join(f"        .{ident(g)}({r})" for g, r in pairs)
    return "\n".join(
        [
            f"// Written by test/gen_gl_top.py from {sources}; do not edit by hand.",
            "`timescale 1ns / 1ps",
            "`default_nettype none",
            "",
            f"module {WRAPPER} (",
            ",\n".join(decl(p) for p in rtl),
            ");",
            f"    {TOP} {INSTANCE} (",
            conns,
            "    );",
            "",
            *census(seq, (INSTANCE,)),
            "",
            *constant_cells(lcs, (INSTANCE,)),
            "",
            "endmodule",
            "",
            "// Physical-only cells: no pins, no logic, no PDK model.",
            *(f"module {t} ();\nendmodule" for t in stubs),
            "`default_nettype wire",
            "",
        ]
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--rtl",
        required=True,
        type=Path,
        help="RTL eFPGA_top.v, the port list to restore",
    )
    ap.add_argument(
        "--netlist",
        required=True,
        nargs="+",
        type=Path,
        help="top_full.v and the tile netlists",
    )
    ap.add_argument(
        "--liberty",
        required=True,
        nargs="+",
        type=Path,
        help="Liberty of every cell library used",
    )
    ap.add_argument(
        "--chip",
        type=Path,
        help="chip-level top.v; wrap it instead of the bare netlist",
    )
    ap.add_argument(
        "--lc-cell",
        required=True,
        type=Path,
        help=f"{LC_CELL} source, whose BelMap places INIT and FF",
    )
    ap.add_argument(
        "--lc-tile",
        required=True,
        nargs="+",
        type=Path,
        help=f"RTL directory of every tile type holding {LC_CELL}",
    )
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--yosys", default="yosys")
    args = ap.parse_args()

    rtl = ports(yosys_json(f"read_verilog -lib {args.rtl}", args.yosys)[TOP])
    libs = "\n".join(f"read_liberty -ignore_miss_func {lib}" for lib in args.liberty)
    sources_v = " ".join(str(n) for n in args.netlist)
    cells = set(yosys_json(libs, args.yosys))
    modules = yosys_json(
        f"{libs}\nread_verilog {sources_v}\nhierarchy -top {TOP}", args.yosys
    )
    pairs = bit_map(rtl, ports(modules[TOP]))
    kinds = sequential_kinds(modules)
    seq = sequentials(modules, cells, kinds)
    stubs = physical_only(modules, cells)
    tiles = {d.name: lc_latches(d, args.yosys) for d in args.lc_tile}
    lcs = logic_cells(modules, kinds, lc_layout(args.lc_cell, args.yosys), tiles)
    n_latch = sum(1 for s in seq if s.kind is Kind.LATCH)
    summary = (
        f"{len(pairs)} port bits, census of {n_latch} latches and "
        f"{len(seq) - n_latch} flops, {len(lcs)} logic cells, "
        f"{len(stubs)} physical-only cells declared empty"
    )
    if args.chip is None:
        sources = f"{args.netlist[0].name} and {args.rtl.name}"
        args.out.write_text(wrapper(rtl, pairs, seq, lcs, stubs, sources))
        print(f"wrote {args.out}: {summary}")
        return
    chip = yosys_json(f"read_verilog {args.chip}", args.yosys)
    macro, pads = chip_pads(chip, pairs)
    sources = f"{args.chip.name}, {args.netlist[0].name} and {args.rtl.name}"
    args.out.write_text(chip_wrapper(rtl, chip, macro, pads, seq, lcs, stubs, sources))
    print(f"wrote {args.out}: {len(pads)} pads, {summary}")


if __name__ == "__main__":
    main()
