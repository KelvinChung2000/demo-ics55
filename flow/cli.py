"""Drive the whole fabric build, one command per stage.

The stages are separate commands rather than one because the expensive part is
hardening thirteen tile types and the cheap part is the plan they are built to,
so the plan is worth regenerating and inspecting on its own. `pilot` exists for
the same reason: FINDINGS.md records a pin placement silently reverting to
iEDA's own coordinates at routing, and a single tile proves the DEF rewrite in
about two minutes against the hours a full batch costs.
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import typer

from flow import defedit, project
from flow.fabric import load_fabric
from flow.plan import CORE_MARGIN, DBU, build_plan, Plan

app = typer.Typer(add_completion=False, help="Build a FABulous fabric on ICS55 with ECC.")

PROJECT = Path(__file__).resolve().parent.parent
BUILD = PROJECT / "build"
PLAN_PATH = BUILD / "fabric_plan.json"
SHARED_SOURCES = [PROJECT / "Fabric", PROJECT / "Tile" / "include", PROJECT / "user_design"]
CLOCK_PORT = "UserCLK"
TOP_MODULE = "eFPGA"
FREQUENCY_MHZ = 100.0
CORE_UTIL = 0.8
TAIL_STEP = "fixFanout"


def _tile_directory(tile_type: str) -> Path:
    return BUILD / "tiles" / tile_type


def _sources(tile_type: str, source: Path) -> list[Path]:
    index = project.source_index([source.parent, *SHARED_SOURCES])
    return project.dependencies(tile_type, index)


@app.command()
def plan(anchor_micron: float = 110.0, anchor_type: str = "LUT4AB") -> None:
    """Size every tile and place every pin, then write build/fabric_plan.json."""
    fabric = load_fabric(PROJECT)
    result = build_plan(fabric, PROJECT / "eFPGA_geometry.csv", anchor_micron, anchor_type)
    BUILD.mkdir(exist_ok=True)
    result.write(PLAN_PATH)
    typer.echo(
        f"{PLAN_PATH}: {result.width / DBU} x {result.height / DBU} um, "
        f"{len(result.placements)} tiles of {len(result.tile_size)} types, "
        f"{len(result.seams)} seams carrying {sum(s.crossings for s in result.seams)} wires"
    )
    for name, (width, height) in sorted(result.tile_size.items()):
        typer.echo(f"  {name:16s} {width / DBU:6.1f} x {height / DBU:6.1f} um")


@app.command()
def check() -> None:
    """Test the plan's four wiring properties without running anything."""
    from flow import verify

    fabric = load_fabric(PROJECT)
    layout = Plan.read(PLAN_PATH)
    failures = verify.check_plan(fabric, layout)
    for line in failures:
        typer.echo(line)
    if failures:
        raise typer.Exit(code=1)
    typer.echo(
        f"plan holds: {len(fabric.links)} links meet at one coordinate, no edge has two pins "
        f"at one offset, no pin sits under a power stripe or past its edge"
    )


@app.command()
def harden(
    tile: list[str] = typer.Option(None),
    jobs: int = 3,
    force: bool = False,
    extend_power: bool = True,
    status: str = "FIXED",
) -> None:
    """Run one tile type from synthesis to filler, with the planned die and pins."""
    fabric = load_fabric(PROJECT)
    layout = Plan.read(PLAN_PATH)
    wanted = tile or sorted(layout.tile_size)
    unknown = set(wanted) - layout.tile_size.keys()
    if unknown:
        raise typer.BadParameter(f"no such tile type: {sorted(unknown)}")

    def build(tile_type: str) -> tuple[str, str]:
        directory = _tile_directory(tile_type)
        if force and directory.exists():
            shutil.rmtree(directory)
        log = BUILD / "logs" / f"{tile_type}.log"
        width, height = layout.tile_size[tile_type]
        project.create_project(
            directory=directory,
            top=tile_type,
            sources=_sources(tile_type, fabric.tile_types[tile_type].source),
            core_util=CORE_UTIL,
            clock_port=CLOCK_PORT,
            frequency_mhz=FREQUENCY_MHZ,
        )
        step = project.create_workspace(directory, log)
        if not step.ok:
            return tile_type, f"Synthesis failed, see {log}"
        project.install_harden_flow(directory)
        project.patch_floorplan(
            directory,
            width_micron=width / DBU,
            height_micron=height / DBU,
            stripe_pitch_micron=layout.stripe_pitch / DBU,
        )
        step = project.run_step(directory, "Floorplan", log)
        if not step.ok:
            return tile_type, f"Floorplan failed, see {log}"
        floorplan = project.floorplan_def(directory, tile_type)
        note = defedit.prepare(
            floorplan,
            floorplan,
            layout.pins[tile_type],
            (width, height),
            extend_power=extend_power,
            status=status,
        )
        project.drop_floorplan_database(directory, tile_type)
        step = project.run_step(directory, TAIL_STEP, log)
        if not step.ok:
            return tile_type, f"{note}; {TAIL_STEP} failed, see {log}"
        opt = project.workspace_of(directory) / "fixFanout_ecc" / "output"
        if not project.needs_placement(directory, opt / f"{tile_type}_{TAIL_STEP}.def.gz"):
            note += "; no logic to place, so placement, CTS and legalisation are skipped"
            project.bypass_placement(directory, tile_type, TAIL_STEP, "fixFanout_ecc")
            step = project.run_from(directory, "route", log)
        else:
            step = project.run_from(directory, "place", log)
        if not step.ok:
            return tile_type, f"{note}; the flow failed, see {log}"
        return tile_type, f"{note}; {check_pins(directory, tile_type)}"

    def attempt(tile_type: str) -> tuple[str, str, bool]:
        # One tile's failure must not stop the other twelve, so it is reported
        # with its log rather than thrown; the exit code still records it.
        try:
            name, message = build(tile_type)
        except (ValueError, FileNotFoundError, KeyError) as failure:
            return tile_type, f"{type(failure).__name__}: {failure}", False
        return name, message, "failed" not in message and "moved" not in message

    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for tile_type, message, ok in pool.map(attempt, wanted):
            failures += not ok
            typer.echo(f"{tile_type:16s} {message}")
    if failures:
        raise typer.Exit(code=1)


def check_pins(directory: Path, tile_type: str) -> str:
    """Compare the routed DEF's pin coordinates with the floorplan's.

    A workspace resumed piecemeal once carried paired pins in its floorplan DEF,
    iEDA's own in its routed DEF and paired pins again in its abstract LEF, so
    the macro view described a layout that did not exist. This is the check that
    catches that, and it is the reason not to trust the run without it.
    """
    def coordinates(path: Path) -> dict[str, str]:
        text = defedit.read_def(path)
        block = defedit.PINS_RE.search(text).group(1)
        import re

        return {
            match.group(1): match.group(2)
            for match in re.finditer(
                r"^\s*- (\S+).*?\+ (?:PLACED|FIXED|COVER) \(\s*(-?\d+\s+-?\d+)\s*\)",
                block,
                re.S | re.M,
            )
        }

    floorplan = coordinates(project.floorplan_def(directory, tile_type))
    routed = coordinates(project.final_def(directory, tile_type))
    moved = {name for name, place in floorplan.items() if routed.get(name) != place}
    if moved:
        return f"{len(moved)} of {len(floorplan)} pins moved between floorplan and filler"
    return f"all {len(floorplan)} pins held their planned position"


@app.command()
def pilot(tile: str = "LUT4AB", extend_power: bool = True, status: str = "FIXED") -> None:
    """Harden one tile type and report whether its pins and PDN survived."""
    harden(tile=[tile], jobs=1, force=True, extend_power=extend_power, status=status)


@app.command()
def paint(tile: list[str] = typer.Option(None)) -> None:
    """Draw each hardened tile's pins and boundary power into its GDS."""
    from flow import paint as painter

    layout = Plan.read(PLAN_PATH)
    painted = BUILD / "painted"
    painted.mkdir(parents=True, exist_ok=True)
    for tile_type in tile or sorted(layout.tile_size):
        directory = _tile_directory(tile_type)
        out = painted / f"{tile_type}.gds"
        typer.echo(
            f"{tile_type:16s} "
            + painter.paint(
                def_path=project.final_def(directory, tile_type),
                gds_path=project.final_gds(directory, tile_type),
                out_path=out,
            )
        )


@app.command()
def stitch(out: Path = BUILD / "eFPGA.gds") -> None:
    """Abut every painted tile at its planned position and prove the seams."""
    from flow import stitch as stitcher

    layout = Plan.read(PLAN_PATH)
    sources = {name: BUILD / "painted" / f"{name}.gds" for name in layout.tile_size}
    missing = {name for name, path in sources.items() if not path.exists()}
    if missing:
        raise typer.BadParameter(f"these tile types are not painted yet: {sorted(missing)}")
    stitcher.stitch(plan=layout, tile_gds=sources, out_gds=out)


@app.command()
def flat(
    directory: Path = BUILD / "flat", core_util: float = 0.8, bottom_up: bool = True
) -> None:
    """Harden the whole eFPGA as one flat design, with no tile macros at all.

    This is the control the abutted fabric is measured against, so it takes none
    of the abutment machinery: iEDA sizes the die from utilisation, places its
    own boundary pins and keeps the PDN inside the core. A flat eFPGA is roughly
    a quarter of a million standard cells, so synthesis alone runs far longer
    than a tile and neither placement nor routing is expected to be quick.
    """
    rtl = directory / "rtl"
    if bottom_up:
        # Flattening the behavioural fabric in one pass wrote a 93 GB Yosys log,
        # because every one of a quarter of a million flattened objects is logged
        # with its full hierarchical path. Composing the tiles' own gate netlists
        # under the bit-blasted parent gives Yosys mapped cells to flatten
        # instead, and reuses thirteen syntheses that have already run.
        from flow import topdesign

        rtl.mkdir(parents=True, exist_ok=True)
        sources = []
        for tile_type in sorted(Plan.read(PLAN_PATH).tile_size):
            netlist = (
                project.workspace_of(_tile_directory(tile_type))
                / "Synthesis_yosys"
                / "output"
                / f"{tile_type}_Synthesis.v.gz"
            )
            if not netlist.exists():
                raise typer.BadParameter(f"{tile_type} has not been synthesised: {netlist}")
            target = rtl / f"{tile_type}_gate.v"
            target.write_text(defedit.read_def(netlist))
            sources.append(target)
        parent = rtl / "eFPGA_flat.v"
        parent.write_text(topdesign.netlist_text(load_fabric(PROJECT)))
        sources.append(parent)
    else:
        roots = (
            [PROJECT / "Fabric"]
            + sorted(path for path in (PROJECT / "Tile").rglob("*") if path.is_dir())
            + [PROJECT / "user_design"]
        )
        sources = project.dependencies(TOP_MODULE, project.source_index(roots))

    log = BUILD / "logs" / "flat.log"
    project.create_project(
        directory=directory,
        top=TOP_MODULE,
        sources=sources,
        core_util=core_util,
        clock_port=CLOCK_PORT,
        frequency_mhz=FREQUENCY_MHZ,
    )
    step = project.create_workspace(directory, log)
    typer.echo(f"synthesis {step.state or 'run'} in {step.seconds:.0f} s")
    if not step.ok:
        raise typer.Exit(code=1)
    project.install_harden_flow(directory)
    step = project.run_from(directory, "Floorplan", log)
    typer.echo(f"flat flow recorded as {step.state} after {step.seconds:.0f} s, see {log}")
    if not step.ok:
        raise typer.Exit(code=1)


@app.command()
def top(directory: Path = BUILD / "fabric", run: bool = True) -> None:
    """Write the fabric-level ECC project and floorplan it with the tiles as macros.

    Only the floorplan is run. The parent is 151 blackboxes and no standard cell,
    which is the input DreamPlace aborts on, so placement and everything after it
    has nothing to do and FINDINGS.md records both failing.
    """
    from flow import topdesign

    layout = Plan.read(PLAN_PATH)
    topdesign.write_project(plan=layout, fabric=load_fabric(PROJECT), directory=directory)
    typer.echo(f"{directory}: fabric-level project written")
    if not run:
        return

    views = {name: project.harden_views(_tile_directory(name), name) for name in layout.tile_size}
    log = BUILD / "logs" / "fabric.log"
    step = project.create_workspace(directory, log)
    if not step.ok:
        raise typer.Exit(code=1)
    project.add_macro_views(
        directory,
        lefs=[lef for lef, _, _ in views.values()],
        libs=[lib for _, lib, _ in views.values()],
    )
    project.install_harden_flow(directory)
    project.patch_floorplan(
        directory,
        width_micron=(layout.width + 2 * CORE_MARGIN) / DBU,
        height_micron=(layout.height + 2 * CORE_MARGIN) / DBU,
        stripe_pitch_micron=layout.stripe_pitch / DBU,
    )
    project.zero_macro_halos(directory)
    placed = project.install_macro_locations(directory, directory / "macro_locations.txt")
    typer.echo(f"{placed} macros fixed at their planned coordinates")
    step = project.run_step(directory, "Floorplan", log)
    typer.echo(
        f"fabric floorplan {'succeeded' if step.ok else 'failed'} in {step.seconds:.0f} s, "
        f"recorded as {step.state}, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
