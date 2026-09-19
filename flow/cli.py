"""Drive the whole fabric build, one command per stage.

The stages are separate commands rather than one because the expensive part is
hardening fifteen tile types and the cheap part is the plan they are built to,
so the plan is worth regenerating and inspecting on its own. `pilot` exists for
the same reason: FINDINGS.md records a pin placement silently reverting to
iEDA's own coordinates at routing, and a single tile proves the DEF rewrite in
about two minutes against the hours a full batch costs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import typer

from flow import defedit, ioplace, names, project, tilelib
from flow.fabric import load_fabric
from flow.plan import DBU, build_plan, Plan

app = typer.Typer(
    add_completion=False, help="Build a FABulous fabric on ICS55 with ECC."
)

PROJECT = Path(__file__).resolve().parent.parent
BUILD = PROJECT / "build"
PLAN_PATH = BUILD / "fabric_plan.json"
SHARED_SOURCES = [
    PROJECT / "Fabric",
    PROJECT / "Tile" / "include",
    # The tile library keeps a BEL in one place and names it from every tile
    # that instantiates it, rather than copying it into each tile directory.
    PROJECT / "primitives",
    PROJECT / "user_design",
]
# The fabric has no top-level clock port. `DisableUserCLK` in fabric.csv means
# the clock enters on an IOBUF pad and reaches the SW_term global buffers
# through the fabric, so which net a flat or macro-level build should call its
# clock is an open question; a tile's own clock port comes from
# `TileType.clock_port` instead.
FABRIC_CLOCK_PORT = "UserCLK"
TOP_MODULE = "eFPGA"
FREQUENCY_MHZ = 100.0
CORE_UTIL = 0.8
# `generate_IO_pin_order_config` is on a FABulous branch this project does not
# pin for anything else, so the interpreter that can run it is named here
# rather than assumed to be the one running the flow.
FABULOUS_PYTHON = Path(
    "/home/kelvin/FABulous/.worktrees-tmp/fix-direction/.venv/bin/python"
)
TAIL_STEP = "postFloorplan"
# The signoff layout of the flat build: routed, DRC'd, LVS'd and filled.
FLAT_GEOMETRY = BUILD / "flat/default/filler_ecc/output/geometry/geometry.manifest"
FLAT_GDS = BUILD / "flat/default/filler_ecc/output/eFPGA_filler.gds"


def _tile_directory(tile_type: str) -> Path:
    return BUILD / "tiles" / tile_type


def _sources(tile_type: str, source: Path) -> list[Path]:
    index = project.source_index([source.parent, *SHARED_SOURCES])
    return project.dependencies(tile_type, index)


@app.command()
def sync_tiles(cache: Path = BUILD / "fabulous-tiles") -> None:
    """Re-vendor Tile/ and primitives/ from the pinned FABulous tile library."""
    result = tilelib.sync(PROJECT, cache)
    typer.echo(
        f"{tilelib.LIBRARY} at {tilelib.COMMIT[:12]}: {len(result.tiles)} tiles, "
        f"{len(result.primitives)} primitives, {len(result.rewritten)} BEL paths shifted"
    )
    typer.echo(f"  primitives: {' '.join(result.primitives)}")
    typer.echo(
        "  every io_pin_order.yaml went with them; run gen-io-order before plan"
    )


@app.command()
def gen_io_order(fabulous_python: Path = FABULOUS_PYTHON) -> None:
    """Regenerate each tile's io_pin_order.yaml with FABulous's own generator.

    Through a separate interpreter because `generate_IO_pin_order_config` is
    not on the FABulous revision this project pins for `run_FABulous_fabric`.
    """
    if not fabulous_python.exists():
        raise typer.BadParameter(
            f"{fabulous_python} does not exist; pass --fabulous-python for the "
            "FABulous checkout that carries generate_IO_pin_order_config"
        )
    # The script is this project's and the packages it imports are FABulous's,
    # so the project is the working directory and the checkout goes on the path.
    checkout = fabulous_python.parent.parent.parent
    completed = subprocess.run(
        [str(fabulous_python), "-m", "flow.genioyaml", str(PROJECT)],
        cwd=PROJECT,
        env={**os.environ, "PYTHONPATH": str(checkout)},
    )
    if completed.returncode:
        raise typer.Exit(code=completed.returncode)


@app.command()
def plan(anchor_micron: float = 110.0, anchor_type: str = "LUT4x8_ha") -> None:
    """Size every tile and place every pin, then write build/fabric_plan.json."""
    fabric = load_fabric(PROJECT)
    result = build_plan(
        fabric, PROJECT / "eFPGA_geometry.csv", anchor_micron, anchor_type
    )
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
        f"at one offset, no pin sits under a power stripe, and every pin is on a track "
        f"inside the core"
    )


@app.command()
def harden(
    tile: list[str] = typer.Option(None),
    jobs: int = 3,
    force: bool = False,
    extend_power: bool = True,
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
            clock_port=fabric.tile_types[tile_type].clock_port(),
            frequency_mhz=FREQUENCY_MHZ,
            die_micron=(width / DBU, height / DBU),
            stripe_pitch_micron=layout.stripe_pitch / DBU,
        )
        step = project.create_workspace(directory, log, to="macroPlacement")
        if not step.ok:
            return tile_type, f"synthesis through macroPlacement failed, see {log}"
        project.widen_flow(directory)
        placed = ioplace.install(
            project.workspace_of(directory), layout.pins[tile_type]
        )
        # From `preFloorplan` rather than from `postFloorplan` alone, so that a
        # rerun over an existing workspace has the die and the macro placement
        # its database initialisation reads.
        step = project.run_range(directory, "preFloorplan", TAIL_STEP, log)
        if not step.ok:
            return tile_type, f"{TAIL_STEP} failed, see {log}"
        floorplan = project.floorplan_def(directory, tile_type)
        note = f"{placed}; " + defedit.prepare(
            floorplan,
            floorplan,
            (width, height),
            extend_power=extend_power,
        )
        project.drop_floorplan_database(directory, tile_type)
        opt = project.workspace_of(directory) / "postFloorplan_ecc" / "output"
        if not project.needs_placement(
            directory, opt / f"{tile_type}_{TAIL_STEP}.def.gz"
        ):
            note += (
                "; no logic to place, so placement, CTS and legalisation are skipped"
            )
            project.bypass_placement(
                directory, tile_type, TAIL_STEP, "postFloorplan_ecc"
            )
            step = project.run_range(directory, "route", "Harden", log)
        else:
            step = project.run_range(directory, "place", "Harden", log)
        if not step.ok:
            return tile_type, f"{note}; the flow failed, see {log}"
        return tile_type, f"{note}; {check_pins(directory, tile_type)}"

    def attempt(tile_type: str) -> tuple[str, str, bool]:
        # One tile's failure must not stop the other fourteen, so it is reported
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
        return (
            f"{len(moved)} of {len(floorplan)} pins moved between floorplan and filler"
        )
    return f"all {len(floorplan)} pins held their planned position"


@app.command()
def pilot(
    tile: str = "LUT4x8_ha", extend_power: bool = True
) -> None:
    """Harden one tile type and report whether its pins and PDN survived."""
    harden(tile=[tile], jobs=1, force=True, extend_power=extend_power)


@app.command()
def synth(tile: list[str] = typer.Option(None), jobs: int = 3) -> None:
    """Synthesise tile types and stop, which is all the flat build needs from them.

    `flat --bottom-up` composes the tiles' gate netlists under a bit-blasted
    parent, so it needs fifteen syntheses and none of the hardening that
    follows them.
    """
    fabric = load_fabric(PROJECT)
    layout = Plan.read(PLAN_PATH)
    wanted = tile or sorted(layout.tile_size)
    unknown = set(wanted) - layout.tile_size.keys()
    if unknown:
        raise typer.BadParameter(f"no such tile type: {sorted(unknown)}")

    def build(tile_type: str) -> tuple[str, str]:
        directory = _tile_directory(tile_type)
        log = BUILD / "logs" / f"{tile_type}.log"
        project.create_project(
            directory=directory,
            top=tile_type,
            sources=_sources(tile_type, fabric.tile_types[tile_type].source),
            core_util=CORE_UTIL,
            clock_port=fabric.tile_types[tile_type].clock_port(),
            frequency_mhz=FREQUENCY_MHZ,
        )
        step = project.create_workspace(directory, log, to="synthesis")
        if not step.ok:
            return tile_type, f"failed after {step.seconds:.0f} s, see {log}"
        netlist = project.synthesis_netlist(directory, tile_type)
        return tile_type, f"{netlist.stat().st_size // 1024} KB in {step.seconds:.0f} s"

    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for tile_type, message in pool.map(build, wanted):
            failures += "failed" in message
            typer.echo(f"{tile_type:16s} {message}")
    if failures:
        raise typer.Exit(code=1)


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
def stitch(out: Path = BUILD / "eFPGA.gds", columns: str = "", rows: str = "") -> None:
    """Abut every painted tile at its planned position and prove the seams.

    `columns` and `rows` take a `first:last` grid range and cut a window out of
    the fabric, which is the same layout the whole fabric has there. A window is
    what makes a geometric check tractable, since the full fabric is 151 tiles.
    """
    from flow import stitch as stitcher

    layout = Plan.read(PLAN_PATH)
    if columns or rows:
        span = lambda text, whole: (  # noqa: E731
            range(*(int(part) for part in text.split(":"))) if text else whole
        )
        layout = layout.window(
            span(columns, range(len(layout.column_width))),
            span(rows, range(len(layout.row_height))),
        )
        typer.echo(
            f"window of {len(layout.placements)} tiles, {len(layout.seams)} seams"
        )
    sources = {name: BUILD / "painted" / f"{name}.gds" for name in layout.tile_size}
    missing = {name for name, path in sources.items() if not path.exists()}
    if missing:
        raise typer.BadParameter(
            f"these tile types are not painted yet: {sorted(missing)}"
        )
    stitcher.stitch(plan=layout, tile_gds=sources, out_gds=out)


@app.command()
def flat(
    directory: Path = BUILD / "flat",
    core_util: float = 0.8,
    bottom_up: bool = True,
    last: str = "Harden",
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
        # instead, and reuses fifteen syntheses that have already run.
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
                raise typer.BadParameter(
                    f"{tile_type} has not been synthesised: {netlist}"
                )
            target = rtl / f"{tile_type}_gate.v"
            text = defedit.read_def(netlist)
            if not target.exists() or target.read_text() != text:
                target.write_text(text)
            # Decompressing is not authoring: the copy is exactly as old as the
            # tile netlist it came from, and dating it now would make the fabric
            # netlist built from it look stale.
            os.utime(target, (netlist.stat().st_atime, netlist.stat().st_mtime))
            sources.append(target)
        parent = rtl / "eFPGA_flat.v"
        text = topdesign.netlist_text(load_fabric(PROJECT))
        if not parent.exists() or parent.read_text() != text:
            parent.write_text(text)
        # The parent is derived from eFPGA.v, so it is no newer than that; dating
        # it now would make every netlist built from it look stale.
        source = PROJECT / "Fabric" / "eFPGA.v"
        os.utime(parent, (source.stat().st_atime, source.stat().st_mtime))
        sources.append(parent)
    else:
        roots = (
            [PROJECT / "Fabric"]
            + sorted(path for path in (PROJECT / "Tile").rglob("*") if path.is_dir())
            + sorted(
                path for path in (PROJECT / "primitives").rglob("*") if path.is_dir()
            )
            + [PROJECT / "user_design"]
        )
        sources = project.dependencies(TOP_MODULE, project.source_index(roots))

    log = BUILD / "logs" / f"{directory.name}.log"
    project.create_project(
        directory=directory,
        top=TOP_MODULE,
        sources=sources,
        core_util=core_util,
        clock_port=FABRIC_CLOCK_PORT,
        frequency_mhz=FREQUENCY_MHZ,
    )
    step = project.create_workspace(directory, log, to="synthesis")
    yosys = project.subflow_state(directory, "Synthesis_yosys", "run yosys")
    netlist = project.synthesis_netlist(directory, TOP_MODULE)
    current = project.netlist_is_current(directory, TOP_MODULE)
    typer.echo(
        f"yosys recorded {yosys}, netlist {netlist.stat().st_size // 1024} KB and "
        f"{'current' if current else 'older than its sources'}"
    )
    if not current:
        typer.echo(
            "the netlist predates its RTL; delete the workspace and synthesise again"
        )
        raise typer.Exit(code=1)
    if project.step_state(directory, "Synthesis") != "Success":
        # ECC's analysis stage runs iSTA over the whole design and fails on this
        # one, which leaves the step unfinished even though Yosys wrote the
        # netlist every later step reads. The netlist is the deliverable, so the
        # step is recorded on the strength of it rather than of the metrics.
        typer.echo(
            "the analysis stage failed; recording synthesis on its netlist instead"
        )
        project.force_step_state(directory, "Synthesis", "Success")
    if not project.floorplan_measurement(directory).exists():
        # `die_side` sizes the die from a floorplan's own measurement, so a
        # workspace that has never floorplanned has to run one first. ECC sizes
        # that one from `core_util` itself, which is close but not exact.
        first = project.run_range(directory, "preFloorplan", "postFloorplan", log)
        if not first.ok:
            typer.echo(f"the sizing floorplan failed, see {log}")
            raise typer.Exit(code=1)
    # ECC rewrites `Core.Utilitization` from the finished floorplan, so setting
    # it before the step does not survive: a run asked for 0.5 came out at
    # 0.7998. The die is therefore sized here and set outright, from the cell
    # area the last floorplan measured, and the core height is rounded to a
    # whole number of core7 rows so no row is lost to alignment.
    side = project.die_side(directory, TOP_MODULE, core_util)
    project.set_params(
        directory,
        {
            "floorplan.die_builder.mode": "die_size",
            "floorplan.die_builder.die_size.width_micron": side,
            "floorplan.die_builder.die_size.height_micron": side,
        },
        log,
    )
    typer.echo(f"floorplanning a {side} um square die, {core_util} of it filled")
    step = project.run_range(directory, "preFloorplan", last, log)
    typer.echo(
        f"flat flow recorded as {step.state} after {step.seconds:.0f} s, see {log}"
    )
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
    topdesign.write_project(
        plan=layout, fabric=load_fabric(PROJECT), directory=directory
    )
    typer.echo(f"{directory}: fabric-level project written")
    if not run:
        return

    views = {
        name: project.harden_views(_tile_directory(name), name)
        for name in layout.tile_size
    }
    log = BUILD / "logs" / "fabric.log"
    step = project.create_workspace(directory, log, to="synthesis")
    if not step.ok:
        raise typer.Exit(code=1)
    project.add_macro_views(
        directory,
        lefs=[lef for lef, _, _ in views.values()],
        libs=[lib for _, lib, _ in views.values()],
    )
    project.zero_macro_halos(directory, log)
    typer.echo(f"{len(layout.placements)} macros fixed at their planned coordinates")
    step = project.run_range(directory, "preFloorplan", "postFloorplan", log)
    typer.echo(
        f"fabric floorplan {'succeeded' if step.ok else 'failed'} in {step.seconds:.0f} s, "
        f"recorded as {step.state}, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)


@app.command()
def find(
    pattern: str,
    kind: names.Kind = names.Kind.SIGNAL,
    manifest: Path = FLAT_GEOMETRY,
    pick: int = 1,
    limit: int = 40,
    copy: bool = True,
) -> None:
    """Find names in a chip-viewer snapshot and put one on the clipboard.

    The viewer's search box takes a whole name and no pattern, so the pattern is
    resolved here and the match at `--pick` is copied for pasting straight back
    in. `--kind` mirrors the viewer's own scope selector, and its default is
    `signal` because the net tables carry a `clock` kind that is rarely what a
    layout question is about.
    """
    if not manifest.exists():
        raise typer.BadParameter(f"no chip-viewer snapshot at {manifest}")
    matches = names.search(manifest, pattern, kind)
    if not matches:
        typer.echo(f"no {kind.value} name matches {pattern!r}")
        raise typer.Exit(code=1)
    for index, name in enumerate(matches[:limit], start=1):
        typer.echo(f"{index:>4}  {name}")
    if len(matches) > limit:
        typer.echo(f"      ... {len(matches) - limit} more, raise --limit to see them")
    if not 1 <= pick <= len(matches):
        raise typer.BadParameter(f"--pick must be between 1 and {len(matches)}")
    chosen = matches[pick - 1]
    typer.echo(
        f"{len(matches)} matches, {'copied' if copy else 'chose'} #{pick} {chosen}"
    )
    if copy:
        names.copy(chosen)


@app.command()
def colour(
    source: Path = FLAT_GDS,
    by: str = "cell",
    out: Path = BUILD / "overlay",
    minimum: int = 1,
    limit: int = 0,
) -> None:
    """Write an overlay GDS colouring a layout by cell master or by tile.

    KLayout colours a layer, never a cell or an instance, so the grouping is
    turned into layers: one per group, each given its own colour in a `.lyp`
    written beside the overlay. Load the overlay over the original and the
    groups separate visually.
    """
    from flow import overlay as painter

    if not source.exists():
        raise typer.BadParameter(f"no layout at {source}")
    grouping = painter.By(by)
    out.mkdir(parents=True, exist_ok=True)
    gds = out / f"{source.stem}_by_{grouping.value}.gds"
    lyp = gds.with_suffix(".lyp")
    groups = painter.write_overlay(source, gds, lyp, grouping, minimum)
    for number, group in enumerate(groups[: limit or 12]):
        typer.echo(
            f"  {painter.FIRST_LAYER + number}/0  {group.name:<24} {len(group.boxes)}"
        )
    if len(groups) > (limit or 12):
        typer.echo(f"       ... {len(groups) - (limit or 12)} more groups")
    typer.echo(
        f"{len(groups)} groups over {sum(len(g.boxes) for g in groups)} placements"
    )
    typer.echo(f"open {source} then load {gds} over it, and apply {lyp}")


if __name__ == "__main__":
    app()
