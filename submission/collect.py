"""Assemble the submission appendix from the working tree and build/nobram.

The appendix is a snapshot, so it is rebuilt from its sources rather than
edited by hand: every file under rtl/, sim/, physical/, signoff/, sta/ and gl/
and chip/ is copied (and large text views gzipped) by this script, and a rerun replaces
those directories. The report, images/ and the README are hand-written and are
left alone.

The RTL set is the module closure of `eFPGA_top` as Yosys `hierarchy` resolves
it, so primitives the variant does not instantiate (the ICS55 SRAM with its
vendor model among them) never enter the appendix.

    python3 submission/collect.py
"""

import csv
import gzip
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission"
VARIANT = ROOT / "fabrics" / "nobram"
BUILD = ROOT / "build" / "nobram"
TOP = BUILD / "top" / "default"
FULLSTA = BUILD / "fullsta"
CHIP = BUILD / "chip"
STA_RECIPE = ROOT / "flow" / "sta"
SIM_BUILD = ROOT / "Test" / "build"
GENERATED = ("rtl", "sim", "physical", "signoff", "sta", "gl", "chip")
RC_CORNERS = (
    "Cbest_125C", "Cbest_m40C", "Cworst_125C", "Cworst_m40C", "RCbest_125C",
    "RCbest_m40C", "RCworst_125C", "RCworst_m40C", "TYPICAL_25C",
)


def need(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; rebuild it before collecting")
    return path


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(need(src), dst)


def copy_gz(src: Path, dst_dir: Path) -> None:
    """Copy src into dst_dir gzipped, unless it already is."""
    need(src)
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".gz":
        shutil.copy2(src, dst_dir / src.name)
        return
    # mtime=0 keeps the archive byte-identical across reruns, so git sees no change.
    with src.open("rb") as f, gzip.GzipFile(dst_dir / f"{src.name}.gz", "wb", mtime=0) as g:
        shutil.copyfileobj(f, g)


def grid_tiles() -> list[str]:
    """Tile types named in fabric.csv between FabricBegin and FabricEnd."""
    names: set[str] = set()
    inside = False
    with need(VARIANT / "fabric.csv").open() as f:
        for row in csv.reader(f):
            head = row[0].strip() if row else ""
            if head == "FabricBegin":
                inside = True
            elif head == "FabricEnd":
                inside = False
            elif inside:
                names.update(c.strip() for c in row if c.strip() and c.strip() != "NULL")
    return sorted(names)


def tile_dir(name: str) -> Path:
    """Tile/<name>, or the supertile directory holding Tile/*/<name>."""
    direct = ROOT / "Tile" / name
    if direct.is_dir():
        return direct
    parents = [p.parent for p in (ROOT / "Tile").glob(f"*/{name}") if p.is_dir()]
    if len(parents) != 1:
        raise LookupError(f"tile {name}: expected one supertile directory, found {parents}")
    return parents[0]


def rtl_closure(tile_dirs: list[Path]) -> list[Path]:
    """Source files of every module eFPGA_top reaches, from Yosys hierarchy."""
    candidates = sorted(
        {*(ROOT / "Fabric").glob("*.v"), *(ROOT / "Fabric").glob("*.sv"),
         *(VARIANT / "Fabric").glob("*.v"), *(ROOT / "primitives").glob("*/fabulous/*.v"),
         *(f for d in tile_dirs for f in d.rglob("*.v"))}
    )
    with tempfile.TemporaryDirectory() as tmp:
        hier = Path(tmp) / "hier.json"
        script = Path(tmp) / "hier.ys"
        script.write_text(
            "read_verilog -sv -defer " + " ".join(str(c) for c in candidates) + "\n"
            f"hierarchy -top eFPGA_top\nproc\nwrite_json {hier}\n"
        )
        subprocess.run(["yosys", "-q", "-s", str(script)], check=True)
        modules = json.loads(hier.read_text())["modules"]
    # hierarchy keeps every (* blackbox *) module, instantiated or not, so walk
    # the instances from the top instead.
    reached: set[str] = set()
    todo = ["eFPGA_top"]
    while todo:
        name = todo.pop()
        if name in reached:
            continue
        reached.add(name)
        todo.extend(c["type"] for c in modules[name]["cells"].values() if c["type"] in modules)
    files: set[Path] = set()
    for name in sorted(reached):
        mod = modules[name]
        src = mod["attributes"].get("src")
        if src is None:
            raise ValueError(f"module {name} carries no src attribute")
        files.add(Path(src.split(":")[0]).resolve())
    return sorted(files)


def collect_rtl(tiles: list[str]) -> None:
    dirs = sorted({tile_dir(t) for t in tiles})
    files = rtl_closure(dirs)
    out = OUT / "rtl"
    listed: list[str] = []
    for f in files:
        rel = f.relative_to(VARIANT / "Fabric") if f.is_relative_to(VARIANT / "Fabric") else f.relative_to(ROOT)
        dst = out / ("eFPGA" / rel if f.is_relative_to(VARIANT / "Fabric") else rel)
        copy(f, dst)
        listed.append(str(dst.relative_to(OUT)))
    (out / "filelist.f").write_text("\n".join(listed) + "\n")
    for d in dirs:
        for name in ("io_pin_order.yaml", "ecc_config.toml"):
            copy(d / name, out / "config" / d.name / name)
    for f in ("fabric.csv", "dies.toml"):
        copy(VARIANT / f, out / "config" / f)
    copy(ROOT / "Fabric" / "ecc_config.toml", out / "config" / "Fabric_ecc_config.toml")
    copy(ROOT / "Tile" / "include" / "ecc_config.toml", out / "config" / "Tile_include_ecc_config.toml")


def collect_sim() -> None:
    out = OUT / "sim"
    for f in (VARIANT / "user_design").iterdir():
        # Hidden entries are editor or sandbox state, not design sources.
        if not f.name.startswith("."):
            copy(f, out / "user_design" / f.name)
    for ext in ("bin", "hex", "fasm"):
        copy(SIM_BUILD / f"sequential_16bit_en.{ext}", out / "bitstream" / f"sequential_16bit_en.{ext}")
    copy(SIM_BUILD / "bitstream_sim.log", out / "results" / "bitstream_sim.log")
    model = VARIANT / ".FABulous"
    for name in ("pips.txt", "bel.txt", "bel.v2.txt", "bel.v3.txt", "bitStreamSpec.bin"):
        copy_gz(model / name, out / "fabulous_model")


def collect_physical(tiles: list[str]) -> None:
    out = OUT / "physical"
    copy(BUILD / "fabric_plan.json", out / "fabric_plan.json")
    top = out / "eFPGA_top"
    filler = TOP / "filler_ecc" / "output"
    for name in ("eFPGA_top_filler.def.gz", "eFPGA_top_filler.v.gz", "eFPGA_top_filler.gds"):
        copy_gz(filler / name, top)
    for corner in RC_CORNERS:
        copy_gz(TOP / "RCX_ecc" / "output" / f"eFPGA_top_{corner}.spef", top / "spef")
    for name in ("eFPGA_top_Harden.lef", "eFPGA_top_Harden.lib", "eFPGA_top_Harden.gds"):
        copy(TOP / "Harden_ecc" / "output" / name, top / "abstract" / name)
    types = sorted({tile_dir(t).name for t in tiles})
    for t in types:
        run = BUILD / "tiles" / t / "default"
        dst = out / "tiles" / t
        for name in (f"{t}_filler.def.gz", f"{t}_filler.v.gz", f"{t}_filler.gds"):
            copy_gz(run / "filler_ecc" / "output" / name, dst)
        for corner in RC_CORNERS:
            copy_gz(run / "RCX_ecc" / "output" / f"{t}_{corner}.spef", dst / "spef")
        macro = BUILD / "top" / "macros" / t
        for name in (f"{t}_Harden.lef", f"{t}_Harden.lib"):
            copy(macro / name, dst / "abstract" / name)


def collect_signoff(tiles: list[str]) -> None:
    out = OUT / "signoff"
    runs = {"eFPGA_top": TOP} | {
        t: BUILD / "tiles" / t / "default" for t in sorted({tile_dir(n).name for n in tiles})
    }
    for name, run in runs.items():
        # ECC's drc.db.rpt and sta.db.rpt are database summaries with no result in
        # them. The DRC count is in the step feature and its per-layer table.
        copy(run / "drc_ecc" / "feature" / "drc.step.json", out / name / "drc.json")
        copy(run / "drc_ecc" / "analysis" / "drc_statis.csv", out / name / "drc.csv")
        copy(run / "lvs_ecc" / "report" / "lvs.rpt", out / name / "lvs.rpt")
        # The timing sits in one directory per library corner and RC corner.
        corners = sorted(p.parent for p in (run / "sta_ecc" / "report").glob("*/*/qor_summary.rpt"))
        if not corners:
            raise FileNotFoundError(f"{run / 'sta_ecc' / 'report'} holds no per-corner iSTA report")
        for corner in corners:
            dst = out / name / "sta" / f"{corner.parent.name}_{corner.name}"
            copy(corner / "qor_summary.rpt", dst / "qor_summary.rpt")
            # Path listings reach 15 MB a corner.
            for f in sorted(corner.glob("timing_*.rpt")):
                copy_gz(f, dst)


def collect_sta() -> None:
    out = OUT / "sta"
    # The tracked recipe ran the logs; copies left in FULLSTA by earlier runs may be stale.
    for name in ("full.tcl", "prepare.sh", "run.sh", "summarise.py", "write_v.tcl", "etm.tcl", "chip.tcl"):
        copy(STA_RECIPE / name, out / "scripts" / name)
    for pattern in ("ff*.log", "ss*.log", "write_v.log", "drv_*.txt", "hold_violators_*.txt", "mpw_*.txt"):
        for f in sorted(FULLSTA.glob(pattern)):
            copy_gz(f, out / "reports")
    summary = subprocess.run(
        [sys.executable, str(STA_RECIPE / "summarise.py"), str(FULLSTA)],
        check=True, capture_output=True, text=True,
    ).stdout
    (out / "summary.txt").write_text(summary)


def collect_gl() -> None:
    out = OUT / "gl"
    copy_gz(FULLSTA / "top_full.v", out)
    for f in sorted(FULLSTA.glob("tile_*.v")):
        copy_gz(f, out)
    copy(ROOT / "Test" / "gen_gl_xinit.py", out / "gen_gl_xinit.py")


def collect_chip() -> None:
    out = OUT / "chip"
    for name in ("top.v", "top.sdc"):
        copy(CHIP / name, out / name)
    models = sorted((CHIP / "etm").glob("eFPGA_top_*.lib"))
    if not models:
        raise FileNotFoundError(f"no extracted model in {CHIP / 'etm'}; run flow/sta/etm.tcl")
    for f in models:
        copy(f, out / "etm" / f.name)
    for f in sorted(CHIP.glob("sta_*.log")):
        copy(f, out / "sta" / f.name)


def main() -> None:
    for d in GENERATED:
        shutil.rmtree(OUT / d, ignore_errors=True)
    tiles = grid_tiles()
    collect_rtl(tiles)
    collect_sim()
    collect_physical(tiles)
    collect_signoff(tiles)
    collect_sta()
    collect_gl()
    collect_chip()
    total = sum(f.stat().st_size for d in GENERATED for f in (OUT / d).rglob("*") if f.is_file())
    largest = max((f for d in GENERATED for f in (OUT / d).rglob("*") if f.is_file()),
                  key=lambda f: f.stat().st_size)
    print(f"collected {total / 1e6:.1f} MB; largest {largest.relative_to(OUT)} "
          f"{largest.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
