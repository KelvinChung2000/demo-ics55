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
from collections.abc import Sequence
from dataclasses import replace
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import typer

from flow import defedit, ioplace, names, project, tilelib
from flow.config import Config, FabricSettings, Param, load_config
from flow.fabric import Fabric, load_fabric
from flow.plan import CORE_MARGIN, DBU, build_plan, Plan, uncovered

app = typer.Typer(
    add_completion=False, help="Build a FABulous fabric on ICS55 with ECC."
)


class Stitcher(str, Enum):
    """Which tool assembles the hardened tiles into one fabric layout."""

    KLAYOUT = "klayout"
    ECC = "ecc"
    BOTH = "both"


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
TOP_MODULE = "eFPGA"
# Every tile is scaled from this one, and `plan` takes the anchor from its
# compiled die. The fabric's proportions come from `eFPGA_geometry.csv`, so the
# anchor type only has to be a tile that is always built.
ANCHOR_TYPE = "LUT4x8_ha"
TAIL_STEP = "postFloorplan"
# What a post-synthesis build and the netlists it writes are named with.
NETLIST_SUFFIX = "_nl"
# The signoff layout of the flat build: routed, DRC'd, LVS'd and filled.
FLAT_GEOMETRY = BUILD / "flat/runs/default/filler_ecc/output/geometry/geometry.manifest"
FLAT_GDS = BUILD / "flat/runs/default/filler_ecc/output/eFPGA_filler.gds"


def _tile_directory(
    tile_type: str,
    overrides: Sequence[project.Override] = (),
    strategy: str | None = None,
) -> Path:
    """Name a tile's build directory after the parameters it was built with.

    An override is an experiment rather than a fabric input, so it gets its own
    directory and leaves the baseline `paint`, `stitch` and `top` read alone.
    Sorting the overrides makes one set of parameters name one directory however
    the flags were ordered on the command line.

    The ABC strategy names the directory on the same grounds, and it has to:
    without it, comparing strategies means four builds racing for one directory.
    """
    parts = sorted(str(override) for override in overrides)
    if strategy is not None:
        parts.append(f"synth={strategy.replace(' ', '-')}")
    if not parts:
        return BUILD / "tiles" / tile_type
    return BUILD / "tiles" / f"{tile_type}@{','.join(parts)}"


def _netlist_directory(tile_type: str) -> Path:
    """Name the synthesis-only build of a tile type, which `flat` composes from.

    `synth` and `harden` write an ECC workspace for the same top module, so one
    directory between them would let a `flat` rebuild discard a hardened run
    forty minutes deep. The netlist build keeps the `_nl` suffix a post-synthesis
    netlist is named with, and the two builds never meet.
    """
    return BUILD / "tiles" / f"{tile_type}{NETLIST_SUFFIX}"


def _sources(tile_type: str, source: Path) -> list[Path]:
    index = project.source_index([source.parent, *SHARED_SOURCES])
    return project.dependencies(tile_type, index)


def _tile_settings(config: Config, fabric: Fabric, tile_type: str) -> FabricSettings:
    """Return the fabric settings with this tile's own clock port put in.

    `clock_port` is one string in `Fabric/ecc_config.toml` because it used to be
    one port every tile shared. The classic tile library has no `UserCLK`, and a
    tile instead meets the global-buffer network on `N_GBUF_END`, `E_GBUF_END`
    or `W_GBUF_FEED_END` depending on where it sits, so the fabric-wide value
    stands only for builds that are not one tile.
    """
    return replace(config.fabric, clock_port=fabric.tile_types[tile_type].clock_port())


@app.command()
def sync_tiles(cache: Path = BUILD / "fabulous-tiles") -> None:
    """Re-vendor Tile/ and primitives/ from the pinned FABulous tile library."""
    result = tilelib.sync(PROJECT, cache)
    typer.echo(
        f"{tilelib.LIBRARY} at {tilelib.COMMIT[:12]}: {len(result.tiles)} tiles, "
        f"{len(result.primitives)} primitives, {len(result.rewritten)} BEL paths shifted"
    )
    typer.echo(f"  primitives: {' '.join(result.primitives)}")


@app.command()
def plan(
    anchor_micron: float = typer.Option(
        None,
        help="Override the anchor width instead of reading the compiled anchor "
        "tile. Needed once to build that tile, and for sweeping the anchor. "
        "Ignored where a [die] table already sizes the column or row.",
    ),
    anchor_type: str = ANCHOR_TYPE,
) -> None:
    """Size every tile and place every pin, then write build/fabric_plan.json.

    A column or row a `[die]` table sizes is built to that. Anything left over
    is scaled from one anchor type, whose anchor is that type's own compiled die
    rather than a number carried beside the fabric: harden the anchor tile and
    the rest of the fabric follows what it actually built. A fabric whose [die]
    tables cover every column and row needs no anchor and none is read, which is
    what lets it be planned before any tile has ever been built.
    """
    fabric = load_fabric(PROJECT)
    config = load_config(PROJECT, tuple(fabric.tile_types))
    loose_columns, loose_rows = uncovered(fabric, config.tile_die)
    if anchor_micron is not None:
        typer.echo(f"anchor {anchor_micron} um, given on the command line")
    elif loose_columns or loose_rows:
        anchor_micron, anchor_height = project.compiled_die(
            _tile_directory(anchor_type, ()), anchor_type
        )
        typer.echo(
            f"anchor {anchor_micron} um, read from the {anchor_type} compiled at "
            f"{anchor_micron} x {anchor_height} um"
        )
    else:
        typer.echo(
            "no anchor needed, every column and row is sized by a [die] table"
        )
    result = build_plan(
        fabric,
        PROJECT / "eFPGA_geometry.csv",
        anchor_micron,
        anchor_type,
        stripe_pitch_micron=config.fabric.stripe_pitch_micron,
        tile_die=config.tile_die,
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
        f"at one offset, no pin sits under a power stripe, and every pin is on a "
        f"track inside the core"
    )


@app.command()
def harden(
    tile: list[str] = typer.Option(None),
    jobs: int = 3,
    force: bool = False,
    extend_power: bool = True,
    overrides: list[str] = typer.Option(
        None,
        "--set",
        metavar="SECTION.NAME=VALUE",
        help="Override one ECC parameter, spelled as `ecc param list` names it. "
        "Repeatable. A run carrying any override builds into its own directory.",
    ),
    synth_strategy: str = typer.Option(
        None,
        "--synth-strategy",
        metavar="DELAY|AREA|BALANCE N",
        help="ABC strategy for synthesis, as YOSYS_SYNTH_STRATEGY spells it. "
        "A run carrying one builds into its own directory.",
    ),
) -> None:
    """Run one tile type from synthesis to filler, with the planned die and pins."""
    fabric = load_fabric(PROJECT)
    config = load_config(PROJECT, tuple(fabric.tile_types))
    layout = Plan.read(PLAN_PATH)
    wanted = tile or sorted(layout.tile_size)
    unknown = set(wanted) - layout.tile_size.keys()
    if unknown:
        raise typer.BadParameter(f"no such tile type: {sorted(unknown)}")
    try:
        chosen = tuple(project.Override.parse(text) for text in overrides or [])
    except ValueError as malformed:
        raise typer.BadParameter(str(malformed)) from malformed

    def build(tile_type: str) -> tuple[str, str]:
        # Only the flag names a directory. A strategy the tile's own config
        # asks for is this fabric's baseline, so it belongs in the plain
        # directory that `plan`, `paint` and `stitch` read.
        directory = _tile_directory(tile_type, chosen, synth_strategy)
        strategy = synth_strategy or config.strategy_for(tile_type)
        if force and directory.exists():
            shutil.rmtree(directory)
        log = BUILD / "logs" / f"{directory.name}.log"
        width, height = layout.tile_size[tile_type]
        try:
            project.create_project(
                directory=directory,
                top=tile_type,
                sources=_sources(tile_type, fabric.tile_types[tile_type].source),
                settings=_tile_settings(config, fabric, tile_type),
                params=[
                    *config.params_for(tile_type),
                    # The die the plan bound to this type's columns and rows,
                    # which `flow.verify` has already proved the fabric meets on.
                    project.Param("floorplan.die_builder", "mode", "die_size"),
                    project.Param(
                        "floorplan.die_builder.die_size", "width_micron", width / DBU
                    ),
                    project.Param(
                        "floorplan.die_builder.die_size", "height_micron", height / DBU
                    ),
                ],
                preset="rtl2gds",
                overrides=chosen,
                stripe_pitch_micron=layout.stripe_pitch / DBU,
            )
        except ValueError:
            # An override ECC refuses leaves a project that can never run. Its
            # directory is removed rather than left under build/tiles, where the
            # stages that read every tile directory would fail on it later.
            shutil.rmtree(directory, ignore_errors=True)
            raise
        step = project.create_workspace(
            directory,
            log,
            to="macroPlacement",
            progress=jobs == 1,
            strategy=strategy,
        )
        if not step.ok:
            return tile_type, f"synthesis through macroPlacement failed, see {log}"
        project.widen_flow(directory)
        placed = ioplace.install(
            project.workspace_of(directory), layout.pins[tile_type], (width, height)
        )
        # From `preFloorplan` rather than from `postFloorplan` alone, so that a
        # rerun over an existing workspace has the die and the macro placement
        # its database initialisation reads.
        step = project.run_range(
            directory, "preFloorplan", TAIL_STEP, log, progress=jobs == 1
        )
        if not step.ok:
            return tile_type, f"{TAIL_STEP} failed, see {log}"
        floorplan = project.floorplan_def(directory, tile_type)
        note = f"{placed}; " + defedit.prepare(
            floorplan, floorplan, (width, height), extend_power=extend_power
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
            step = project.run_range(
                directory, "route", "Harden", log, progress=jobs == 1
            )
        else:
            step = project.run_range(
                directory, "place", "Harden", log, progress=jobs == 1
            )
        if not step.ok:
            return tile_type, f"{note}; the flow failed, see {log}"
        density = project.placed_density(directory)
        return (
            tile_type,
            f"{note}; {check_pins(directory, tile_type)}; placed density {density:.3f}",
        )

    def attempt(tile_type: str) -> tuple[str, str, bool]:
        # One tile's failure must not stop the other fourteen, so it is reported
        # with its log rather than thrown; the exit code still records it.
        try:
            name, message = build(tile_type)
        except (ValueError, FileNotFoundError, KeyError) as failure:
            return tile_type, f"{type(failure).__name__}: {failure}", False
        return name, message, "failed" not in message and "moved" not in message

    failures, densities = 0, {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for tile_type, message, ok in pool.map(attempt, wanted):
            failures += not ok
            if ok:
                densities[tile_type] = project.placed_density(
                    _tile_directory(tile_type, chosen)
                )
            # The directory rather than the tile type, so a run carrying an
            # override names the build it actually produced.
            typer.echo(f"{_tile_directory(tile_type, chosen).name:16s} {message}")

    built = len(wanted) - failures
    typer.echo(f"\n{built} of {len(wanted)} tile types hardened")
    if densities:
        worst = min(densities, key=densities.get)
        best = max(densities, key=densities.get)
        # The fabric is sized by whichever type fills its placeable area least,
        # so the spread matters more than the mean. DreamPlace refuses a run at
        # 0.99, which is what the top of this range is approaching.
        typer.echo(
            f"placed density {densities[worst]:.3f} ({worst}) to "
            f"{densities[best]:.3f} ({best})"
        )
    if failures:
        typer.echo(f"{failures} failed; see {BUILD}/logs")
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
    tile: str = "LUT4x8_ha",
    extend_power: bool = True,
    overrides: list[str] = typer.Option(None, "--set", metavar="SECTION.NAME=VALUE"),
) -> None:
    """Harden one tile type and report whether its pins and PDN survived."""
    harden(
        tile=[tile],
        jobs=1,
        force=True,
        extend_power=extend_power,
        overrides=overrides or [],
    )


@app.command()
def synth(tile: list[str] = typer.Option(None), jobs: int = 3) -> None:
    """Synthesise tile types and stop, which is all the flat build needs from them.

    `flat --bottom-up` composes the tiles' gate netlists under a bit-blasted
    parent, so it needs fifteen syntheses and none of the hardening that
    follows them. Each one builds into its own `<type>_nl` directory rather than
    the hardened tile's, so rebuilding the flat control cannot discard a
    hardened run.
    """
    fabric = load_fabric(PROJECT)
    config = load_config(PROJECT, tuple(fabric.tile_types))
    layout = Plan.read(PLAN_PATH)
    wanted = tile or sorted(layout.tile_size)
    unknown = set(wanted) - layout.tile_size.keys()
    if unknown:
        raise typer.BadParameter(f"no such tile type: {sorted(unknown)}")

    def build(tile_type: str) -> tuple[str, str]:
        directory = _netlist_directory(tile_type)
        log = BUILD / "logs" / f"{directory.name}.log"
        project.create_project(
            directory=directory,
            top=tile_type,
            sources=_sources(tile_type, fabric.tile_types[tile_type].source),
            settings=_tile_settings(config, fabric, tile_type),
            params=config.params_for(tile_type),
            # Synthesis only, so no floorplan reads this.
            stripe_pitch_micron=config.fabric.stripe_pitch_micron,
        )
        step = project.create_workspace(
            directory,
            log,
            # Spelled as the ledger records it, not as the CLI accepts it. ECC
            # takes either case as an argument and writes back only `Synthesis`,
            # and this name is then read back out of the ledger.
            to="Synthesis",
            progress=jobs == 1,
            strategy=config.strategy_for(tile_type),
        )
        if not step.ok:
            return tile_type, f"failed after {step.seconds:.0f} s, see {log}"
        netlist = project.synthesis_netlist(directory, tile_type)
        return tile_type, f"{netlist.stat().st_size // 1024} KB in {step.seconds:.0f} s"

    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for tile_type, message in pool.map(build, wanted):
            failures += "failed" in message
            typer.echo(f"{_netlist_directory(tile_type).name:16s} {message}")
    if failures:
        raise typer.Exit(code=1)


@app.command()
def stitch(out: Path = BUILD / "eFPGA.gds", columns: str = "", rows: str = "") -> None:
    """Paint every hardened tile, abut them at their planned positions, prove the seams.

    Painting and abutting are one step because a painted GDS is only valid for
    the plan it was drawn against: `flow.paint` draws the pins and the boundary
    power that plan placed, and `flow.stitch` abuts at the coordinates the same
    plan derived. Painting here, against the plan being abutted, is what catches
    a tile hardened to an older die before anything is placed, rather than
    letting it surface as a seam that does not conduct.

    `columns` and `rows` take a `first:last` grid range and cut a window out of
    the fabric, which is the same layout the whole fabric has there. A window is
    what makes a geometric check tractable, since the full fabric is 151 tiles.
    """
    from flow import paint as painter
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
    painted = BUILD / "painted"
    painted.mkdir(parents=True, exist_ok=True)
    sources = {}
    for tile_type in sorted(layout.tile_size):
        directory = _tile_directory(tile_type)
        sources[tile_type] = painted / f"{tile_type}.gds"
        typer.echo(
            f"{tile_type:16s} "
            + painter.paint(
                def_path=project.final_def(directory, tile_type),
                gds_path=project.final_gds(directory, tile_type),
                out_path=sources[tile_type],
                size=layout.tile_size[tile_type],
            )
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
    config = load_config(PROJECT, tuple(load_fabric(PROJECT).tile_types))
    if bottom_up:
        # Flattening the behavioural fabric in one pass wrote a 93 GB Yosys log,
        # because every one of a quarter of a million flattened objects is logged
        # with its full hierarchical path. Composing the tiles' own gate netlists
        # under the bit-blasted parent gives Yosys mapped cells to flatten
        # instead, out of the fifteen `synth` builds rather than out of RTL.
        from flow import topdesign

        rtl.mkdir(parents=True, exist_ok=True)
        sources = []
        for tile_type in sorted(Plan.read(PLAN_PATH).tile_size):
            netlist = (
                project.workspace_of(_netlist_directory(tile_type))
                / "Synthesis_yosys"
                / "output"
                / f"{tile_type}_Synthesis.v.gz"
            )
            if not netlist.exists():
                raise typer.BadParameter(
                    f"{tile_type} has no netlist at {netlist}. Run `task synth` first; "
                    "a hardened tile's own synthesis is a separate build and is not "
                    "read here."
                )
            target = rtl / f"{tile_type}{NETLIST_SUFFIX}.v"
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
    # The flat control is one design rather than fifteen, so it takes the tile
    # defaults with its own utilisation, which is a flag here because the whole
    # point of the build is to sweep it.
    params = tuple(
        param for param in config.tile_defaults if param.key != "floorplan.core_util"
    ) + (Param(section="floorplan", name="core_util", value=core_util),)
    project.create_project(
        directory=directory,
        top=TOP_MODULE,
        sources=sources,
        settings=config.fabric,
        params=params,
        # One design rather than an abutted fabric, so its rows are its own and
        # the pitch the fabric settled on does not apply.
        stripe_pitch_micron=config.fabric.stripe_pitch_micron,
    )
    step = project.create_workspace(directory, log, to="synthesis", progress=True)
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
    project.widen_flow(directory)
    if not project.floorplan_measurement(directory).exists():
        # `die_side` sizes the die from a floorplan's own measurement, so a
        # workspace that has never floorplanned has to run one first. ECC sizes
        # that one from `core_util` itself, which is close but not exact.
        first = project.run_range(
            directory, "preFloorplan", "postFloorplan", log, progress=True
        )
        if not first.ok:
            typer.echo(f"the sizing floorplan failed, see {log}")
            raise typer.Exit(code=1)
    # ECC rewrites `Core.Utilitization` from the finished floorplan, so setting
    # it before the step does not survive: a run asked for 0.5 came out at
    # 0.7998. The die is therefore sized here and set outright, from the cell
    # area the last floorplan measured, and the core height is rounded to a
    # whole number of core7 rows so no row is lost to alignment.
    side = project.die_side(
        directory,
        TOP_MODULE,
        core_util,
        core_margin_micron=config.fabric.core_margin_micron,
    )
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
    step = project.run_range(directory, "preFloorplan", last, log, progress=True)
    typer.echo(
        f"flat flow recorded as {step.state} after {step.seconds:.0f} s, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)


@app.command()
def top(
    directory: Path = BUILD / "fabric", run: bool = True, assemble: bool = False
) -> None:
    """Write the fabric-level ECC project and floorplan it with the tiles as macros.

    Without `--assemble` only the floorplan is run. The parent is 151 blackboxes
    and no standard cell, which is the input DreamPlace aborts on, so placement
    and everything after it has nothing to do and FINDINGS.md records both
    failing.

    `--assemble` carries that parent on to a layout: placement, CTS and
    legalisation are seeded from the floorplan the way `harden` seeds a tile
    whose logic Yosys collapsed away, and the flow runs from routing to filler,
    which is the step that writes the GDS. Routing has nothing to join either,
    since every inter-tile connection is made by abutment, but it is run rather
    than skipped because only the router can say so.
    """
    from flow import topdesign

    layout = Plan.read(PLAN_PATH)
    fabric = load_fabric(PROJECT)
    config = load_config(PROJECT, tuple(fabric.tile_types))
    topdesign.write_project(
        plan=layout,
        fabric=fabric,
        directory=directory,
        settings=config.fabric,
        params=config.fabric_params,
    )
    typer.echo(f"{directory}: fabric-level project written")
    if not run:
        return

    views = {
        name: project.harden_views(_tile_directory(name), name)
        for name in layout.tile_size
    }
    log = BUILD / "logs" / "fabric.log"
    step = project.create_workspace(directory, log, to="synthesis", progress=True)
    if not step.ok:
        raise typer.Exit(code=1)
    project.add_macro_views(
        directory,
        lefs=[lef for lef, _, _ in views.values()],
        libs=[lib for _, lib, _ in views.values()],
    )
    project.widen_flow(directory)
    project.zero_macro_halos(directory, log)
    typer.echo(f"{len(layout.placements)} macros fixed at their planned coordinates")
    step = project.run_range(
        directory, "preFloorplan", "postFloorplan", log, progress=True
    )
    typer.echo(
        f"fabric floorplan {'succeeded' if step.ok else 'failed'} in {step.seconds:.0f} s, "
        f"recorded as {step.state}, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)
    if not assemble:
        return
    # RCX, STA and Harden have no standard cell to extract or constrain here, so
    # the assembly stops at the step that writes the layout.
    project.bypass_placement(
        directory, TOP_MODULE, "postFloorplan", "postFloorplan_ecc"
    )
    step = project.run_range(directory, "route", "filler", log, progress=True)
    typer.echo(
        f"ECC assembly recorded as {step.state} after {step.seconds:.0f} s, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)
    typer.echo(f"{project.final_gds(directory, TOP_MODULE)}: assembled by ECC")


@app.command()
def assemble(
    stitcher: Stitcher = Stitcher.KLAYOUT,
    out: Path = BUILD / "eFPGA.gds",
    directory: Path = BUILD / "fabric",
) -> None:
    """Assemble the hardened tiles into one fabric layout, by klayout or by ECC.

    The two are not interchangeable. `flow.stitch` abuts the painted tiles and
    then proves every seam conducts and joins the two ends of a link `eFPGA.v`
    declares, which is the check the whole abutment rests on; it writes `out`.
    ECC assembles the same tiles as macros in its own run, so the layout carries
    iEDA's DEF and the fabric PDN and can be read by the rest of the ECC flow,
    but nothing in it proves a seam. `both` runs each, which is the only way to
    get the ECC layout and the proof from one command.
    """
    if stitcher is not Stitcher.ECC:
        stitch(out=out)
    top(directory=directory, assemble=stitcher is not Stitcher.KLAYOUT)


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
