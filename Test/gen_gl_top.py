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

Both designs are read by yosys; nothing here parses Verilog.

    python3 Test/gen_gl_top.py --rtl fabrics/nobram/Fabric/eFPGA_top.v \
        --netlist build/gl/top_full.v build/gl/tile_*.v \
        --liberty <pdk>/<lib>.lib ... --out build/eFPGA_top_gl.v
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


def census(seq: list[Sequential]) -> list[str]:
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
        outs = ", ".join(ref(INSTANCE, *s.path, o) for o in s.outputs)
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


def wrapper(
    rtl: list[Port],
    pairs: list[tuple[str, str]],
    seq: list[Sequential],
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
            f"// Written by Test/gen_gl_top.py from {sources}; do not edit by hand.",
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
            *census(seq),
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
    seq = sequentials(modules, cells, sequential_kinds(modules))
    stubs = physical_only(modules, cells)
    sources = f"{args.netlist[0].name} and {args.rtl.name}"
    args.out.write_text(wrapper(rtl, pairs, seq, stubs, sources))
    n_latch = sum(1 for s in seq if s.kind is Kind.LATCH)
    print(
        f"wrote {args.out}: {len(pairs)} port bits, census of {n_latch} latches and "
        f"{len(seq) - n_latch} flops, {len(stubs)} physical-only cells declared empty"
    )


if __name__ == "__main__":
    main()
