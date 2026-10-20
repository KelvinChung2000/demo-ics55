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
from collections.abc import Sequence
from dataclasses import replace
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated

import typer

from flow import defedit, ioplace, names, project, repair, tilelib
from flow.config import Config, FabricSettings, load_config
from flow.fabric import Fabric, load_fabric
from flow.plan import CORE_MARGIN, DBU, build_plan, Plan, stale_dies, uncovered
from flow.variant import ENVIRONMENT, ROOT, Paths, Variant

app = typer.Typer(
    add_completion=False, help="Build a FABulous fabric on ICS55 with ECC."
)


class Stitcher(str, Enum):
    """Which tool assembles the hardened tiles into one fabric layout."""

    KLAYOUT = "klayout"
    ECC = "ecc"
    BOTH = "both"


SHARED_SOURCES = [
    ROOT / "Fabric",
    ROOT / "Tile" / "include",
    # The tile library keeps a BEL in one place and names it from every tile
    # that instantiates it, rather than copying it into each tile directory.
    ROOT / "primitives",
    ROOT / "user_design",
]
TOP_MODULE = "eFPGA"
# Two FABulous checkouts built this fabric and they are not interchangeable.
# `user-clk-attr` at c0ca47639 wrote every generated `.v` under `Tile/`, and
# regenerating with it reproduces all eleven frozen tiles byte for byte; the
# revision `fix-direction` names reorders a tile's ports, moving `CO` ahead of
# `S1END` on `LUT4x8_ha`, and rewrites the `//TilePort` comments. Pin order went
# the other way: every committed `io_pin_order.yaml` regenerates unchanged under
# `fix-direction` and not under `user-clk-attr`, which orders `CO` and the
# global-buffer ports differently. Hardened tiles were built to that order, so
# this is the one `gen-io-order` runs and neither checkout can do both jobs.
FABULOUS_PYTHON = Path(
    "/home/kelvin/FABulous/.worktrees-tmp/fix-direction/.venv/bin/python"
)
# Every tile is scaled from this one, and `plan` takes the anchor from its
# compiled die. The fabric's proportions come from `eFPGA_geometry.csv`, so the
# anchor type only has to be a tile that is always built.
ANCHOR_TYPE = "LUT4x8_ha"
TAIL_STEP = "postFloorplan"
# The STA corner a hardened tile's extracted `.lib` belongs to. Every tile is
# built against the standard cells' ss_rcworst_1p08_125 liberty, which is what
# `sta_ecc.json` calls MAX.
MACRO_CORNER = "MAX"
# What a post-synthesis build and the netlists it writes are named with.
NETLIST_SUFFIX = "_nl"
_selected: Paths | None = None


@app.callback()
def select(
    variant: Annotated[
        Variant,
        typer.Option(envvar=ENVIRONMENT, help="Which fabrics/<variant> to build."),
    ],
) -> None:
    """Build a FABulous fabric on ICS55 with ECC."""
    global _selected
    _selected = Paths(variant)


def paths() -> Paths:
    """The variant `select` chose, which Typer runs before every command."""
    if _selected is None:
        raise RuntimeError("no variant selected; pass --variant or set FLOW_VARIANT")
    return _selected


def _fabric_geometry() -> Path:
    """ECC's own assembly of the abutted fabric, which only `assemble --stitcher ecc`
    writes; `stitch` abuts in klayout and produces no ECC workspace."""
    return (
        paths().build
        / "fabric"
        / project.WORKSPACE
        / "filler_ecc/output/geometry/geometry.manifest"
    )


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
        return paths().build / "tiles" / tile_type
    return paths().build / "tiles" / f"{tile_type}@{','.join(parts)}"


def _netlist_directory(tile_type: str) -> Path:
    """Name the synthesis-only build of a tile type, which the strategy sweep reads.

    `synth` and `harden` write an ECC workspace for the same top module, so one
    directory between them would let a sweep discard a hardened run forty minutes
    deep. The netlist build keeps the `_nl` suffix a post-synthesis netlist is
    named with, and the two builds never meet.
    """
    return paths().build / "tiles" / f"{tile_type}{NETLIST_SUFFIX}"


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
def gen_io_order(fabulous_python: Path = FABULOUS_PYTHON) -> None:
    """Regenerate each tile's io_pin_order.yaml with FABulous's own generator.

    Through a separate interpreter because the flow's own environment does not
    carry FABulous, and through this one in particular because a tile's pin
    order has to match the RTL it was hardened from.
    """
    if not fabulous_python.exists():
        raise typer.BadParameter(
            f"{fabulous_python} does not exist; pass --fabulous-python for the "
            "FABulous checkout that generated Tile/"
        )
    checkout = fabulous_python.parent.parent.parent
    completed = subprocess.run(
        [str(fabulous_python), "-m", "flow.genioyaml", str(paths().fabric)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(checkout)},
    )
    if completed.returncode:
        raise typer.Exit(code=completed.returncode)


@app.command()
def sync_tiles(cache: Path = ROOT / "build" / "fabulous-tiles") -> None:
    """Re-vendor Tile/ and primitives/ from the pinned FABulous tile library."""
    result = tilelib.sync(ROOT, cache)
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
    fabric = load_fabric(paths())
    config = load_config(paths(), tuple(fabric.tile_types))
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
        typer.echo("no anchor needed, every column and row is sized by a [die] table")
    result = build_plan(
        fabric,
        paths().geometry,
        anchor_micron,
        anchor_type,
        stripe_pitch_micron=config.fabric.stripe_pitch_micron,
        tile_die=config.tile_die,
        tile_macro=config.tile_macro,
    )
    paths().build.mkdir(parents=True, exist_ok=True)
    result.write(paths().plan)
    typer.echo(
        f"{paths().plan}: {result.width / DBU} x {result.height / DBU} um, "
        f"{len(result.placements)} tiles of {len(result.tile_size)} types, "
        f"{len(result.seams)} seams carrying {sum(s.crossings for s in result.seams)} wires"
    )
    for name, (width, height) in sorted(result.tile_size.items()):
        typer.echo(f"  {name:16s} {width / DBU:6.1f} x {height / DBU:6.1f} um")


@app.command()
def gen_top() -> None:
    """Write fabrics/<variant>/Fabric/eFPGA_top.v from the variant's eFPGA.v."""
    from flow import topwrap

    fabric = load_fabric(paths())
    size, widths = topwrap.write_top(paths(), fabric)
    buses = ", ".join(f"{port}[{width}]" for port, width in sorted(widths.items()))
    typer.echo(
        f"{paths().fabric / 'Fabric' / 'eFPGA_top.v'}: {size} bytes, "
        f"{fabric.columns} x {fabric.rows} frames grid, {buses}"
    )


@app.command()
def check() -> None:
    """Test the plan's four wiring properties without running anything."""
    from flow import verify

    fabric = load_fabric(paths())
    layout = Plan.read(paths().plan)
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
    fabric = load_fabric(paths())
    config = load_config(paths(), tuple(fabric.tile_types))
    layout = Plan.read(paths().plan)
    # Checked over every type rather than only the ones asked for, since one
    # stale plan makes every edited [die] table wrong and hardening the tile
    # named here would still leave the fabric built to two different geometries.
    stale = stale_dies(config.tile_die, layout.tile_size)
    if stale:
        raise typer.BadParameter(
            f"{paths().plan} was written before these [die] tables were edited, and "
            f"harden builds to the plan: {'; '.join(stale)}. Run `task plan` to "
            "carry them in, which `task harden-one` now does for you."
        )
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
        log = paths().build / "logs" / f"{directory.name}.log"
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
                dont_use=(
                    project.WEAK_DRIVES if config.avoids_weak_drives(tile_type) else ()
                ),
            )
        except ValueError:
            # An override ECC refuses leaves a project that can never run. Its
            # directory is removed rather than left under build/tiles, where the
            # stages that read every tile directory would fail on it later.
            shutil.rmtree(directory, ignore_errors=True)
            raise
        macro = config.tile_macro.get(tile_type)
        if macro is None:
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
        else:
            # A hard macro splits the run in a third place. Its LEF and liberty
            # can only be appended to `config/db_ecc.json`, which the workspace
            # creates on its first step, so synthesis has to finish before the
            # floorplanner can be told the cell exists; Yosys reads the blackbox
            # beside the BEL instead. The coordinate is fixed here rather than
            # left to DreamPlace because an abutted tile has nowhere to move it
            # and `flow.plan` drew the pin plan around where it sits.
            step = project.create_workspace(
                directory, log, to="Synthesis", progress=jobs == 1, strategy=strategy
            )
            if not step.ok:
                return tile_type, f"synthesis failed, see {log}"
            project.widen_flow(directory)
            project.add_macro_views(directory, lefs=[macro.lef], libs=[macro.lib])
            # `ecc param set --workspace` refreshes the step configs and fails on
            # a step whose config does not exist yet, so the floorplan has to run
            # once before either of the two settings below can be made. Its own
            # automatic macro placement is discarded by the rerun that follows.
            step = project.run_range(
                directory, "preFloorplan", "preFloorplan", log, progress=jobs == 1
            )
            if not step.ok:
                return tile_type, f"preFloorplan failed, see {log}"
            # The 3 um halos ECC ships would take area a core this tight cannot
            # spare, and they guard against crowding this macro is not at risk
            # of: its placement is fixed and its east face is the fabric edge.
            project.zero_macro_halos(directory, log)
            instance = project.macro_instance(directory, tile_type, macro.cell)
            project.set_params(
                directory,
                {
                    "macro.placements": json.dumps(
                        [
                            {
                                "instance": instance,
                                "x": macro.x_micron,
                                "y": macro.y_micron,
                                "orientation": macro.orientation,
                            }
                        ]
                    )
                },
                log,
            )
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
        elif tile_type in config.tile_repair:
            step = project.run_range(
                directory, "place", "legalization", log, progress=jobs == 1
            )
            if not step.ok:
                return tile_type, f"{note}; placement failed, see {log}"
            folder = ("legalization", "legalization_dreamplace")
            note += "; OpenROAD " + repair.tile(
                project.step_def(directory, tile_type, *folder),
                pdk_root=config.fabric.pdk_root,
                margin_percent=config.tile_repair[tile_type],
                reports=directory / "repair",
            )
            project.drop_step_database(directory, tile_type, *folder)
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
        typer.echo(f"{failures} failed; see {paths().build}/logs")
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
    """Synthesise tile types and stop, which is all a strategy sweep needs from them.

    `sweep/tile_strategies.py` at 93bf29a read the `_nl` workspaces this writes
    to compare a tile's cell area across ABC strategies, and none of the hardening that
    follows synthesis changes that number. Each build goes to its own
    `<type>_nl` directory rather than the hardened tile's, so a sweep cannot
    discard a hardened run.
    """
    fabric = load_fabric(paths())
    config = load_config(paths(), tuple(fabric.tile_types))
    layout = Plan.read(paths().plan)
    wanted = tile or sorted(layout.tile_size)
    unknown = set(wanted) - layout.tile_size.keys()
    if unknown:
        raise typer.BadParameter(f"no such tile type: {sorted(unknown)}")

    def build(tile_type: str) -> tuple[str, str]:
        directory = _netlist_directory(tile_type)
        log = paths().build / "logs" / f"{directory.name}.log"
        project.create_project(
            directory=directory,
            top=tile_type,
            sources=_sources(tile_type, fabric.tile_types[tile_type].source),
            settings=_tile_settings(config, fabric, tile_type),
            params=config.params_for(tile_type),
            # Synthesis only, so no floorplan reads this.
            stripe_pitch_micron=config.fabric.stripe_pitch_micron,
            dont_use=project.WEAK_DRIVES if config.avoids_weak_drives(tile_type) else (),
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
def stitch(out: Path | None = None, columns: str = "", rows: str = "") -> None:
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

    out = out or paths().build / "eFPGA.gds"
    layout = Plan.read(paths().plan)
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
    painted = paths().build / "painted"
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
    stitcher.stitch(
        plan=layout, fabric=load_fabric(paths()), tile_gds=sources, out_gds=out
    )


@app.command()
def top(
    directory: Path | None = None, run: bool = True, assemble: bool = False
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

    directory = directory or paths().build / "fabric"
    layout = Plan.read(paths().plan)
    fabric = load_fabric(paths())
    config = load_config(paths(), tuple(fabric.tile_types))
    netlist = topdesign.write_project(
        plan=layout,
        fabric=fabric,
        directory=directory,
        settings=config.fabric,
        params=config.fabric_params,
    )
    typer.echo(f"{directory}: fabric-level project written")
    if not run:
        return

    # Copied into the project rather than referenced, so `build/fabric` is a
    # complete ECC project: hand it to a tool that has never heard of
    # `build/tiles` and every macro it instantiates is there beside it.
    views = project.stage_macro_views(
        directory,
        {
            name: project.tile_views(_tile_directory(name), name)
            for name in layout.tile_size
        },
    )
    unbound = topdesign.unbound_pins(
        directory / "rtl", {name: kinds["lef"] for name, kinds in views.items()}
    )
    if unbound:
        raise typer.BadParameter(
            "the parent's blackbox stubs and the hardened macros they bind to by "
            "name disagree, so the floorplan would carry pins with nothing on "
            "them: " + "; ".join(unbound)
        )
    log = paths().build / "logs" / "fabric.log"
    # `Synthesis` as the ledger spells it, not the lowercase `--from` selector:
    # `project.step_state` reads the state back by that name and a mismatch is a
    # KeyError after the step has already run.
    step = project.create_workspace(directory, log, to="Synthesis", progress=True)
    if not step.ok:
        raise typer.Exit(code=1)
    project.add_macro_views(
        directory,
        lefs=[kinds["lef"] for kinds in views.values()],
        libs=[kinds["lib"] for kinds in views.values()],
    )
    timed = project.add_macro_timing(
        directory, [kinds["lib"] for kinds in views.values()], MACRO_CORNER
    )
    project.widen_flow(directory)
    # `ecc param set --workspace` refreshes the step configs and fails on a step
    # whose config does not exist, so the floorplan runs once before the halos
    # can be zeroed and again afterwards. Its first pass places nothing that
    # survives: every macro is fixed by `macro.placements` at project scope.
    step = project.run_range(
        directory, "preFloorplan", "preFloorplan", log, progress=True
    )
    if not step.ok:
        typer.echo(f"the first floorplan pass failed, see {log}")
        raise typer.Exit(code=1)
    project.zero_macro_halos(directory, log)
    cleared = project.clear_pdn_stripes(directory)
    # Every parent pin is one edge tile's pin and has no freedom, so it is placed
    # rather than left to ECC's automatic placer, which scatters 688 of them
    # around a die whose every net already sits on its boundary.
    die = topdesign.plan_die(layout)
    boundary = topdesign.boundary_pins(layout, fabric, netlist)
    placed = ioplace.install(
        project.workspace_of(directory), boundary, (die.width, die.height)
    )
    typer.echo(
        f"{len(layout.placements)} macros fixed at their planned coordinates; "
        f"{cleared} template stripes cleared, the tiles carry the PDN; "
        f"{len(views)} tile view sets staged under macros/; "
        f"{timed} macro timing models added to the {MACRO_CORNER} corner; {placed}"
    )
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
def integrate(
    channel_micron: float = typer.Option(
        48.0, help="Width of the standard-cell channel west of the fabric."
    ),
    strip_micron: float = typer.Option(
        22.4, help="Height of the standard-cell strip south of the fabric."
    ),
    directory: Path | None = None,
    run: bool = True,
) -> None:
    """Harden eFPGA_top: the tile macros, the loader and the front-ends in one run.

    The fabric sits in the north-east corner of the die and the configuration
    logic is placed in the strip and the channel, whose PDN `flow.integrate`
    draws into the floorplan DEF because ECC's would cover the tiles too.
    """
    from flow import integrate as toprun
    from flow import topdesign

    directory = directory or paths().build / "top"
    layout = Plan.read(paths().plan)
    fabric = load_fabric(paths())
    config = load_config(paths(), tuple(fabric.tile_types))
    shape = toprun.geometry(layout, channel_micron, strip_micron)
    netlist = toprun.write_project(
        paths=paths(),
        plan=layout,
        fabric=fabric,
        directory=directory,
        settings=config.fabric,
        params=config.fabric_params,
        shape=shape,
    )
    typer.echo(
        f"{directory}: die {shape.width / DBU} x {shape.height / DBU} um, fabric at "
        f"({shape.origin[0] / DBU}, {shape.origin[1] / DBU}) um"
    )
    if not run:
        return
    views = project.stage_macro_views(
        directory,
        {
            name: project.tile_views(_tile_directory(name), name)
            for name in layout.tile_size
        },
    )
    unbound = topdesign.unbound_pins(
        directory / "rtl", {name: kinds["lef"] for name, kinds in views.items()}
    )
    if unbound:
        raise typer.BadParameter("stubs and macros disagree: " + "; ".join(unbound))
    log = paths().build / "logs" / "top.log"
    step = project.create_workspace(directory, log, to="Synthesis", progress=True)
    if not step.ok:
        raise typer.Exit(code=1)
    project.add_macro_views(
        directory,
        lefs=[kinds["lef"] for kinds in views.values()],
        libs=[kinds["lib"] for kinds in views.values()],
    )
    project.widen_flow(directory)
    step = project.run_range(
        directory, "preFloorplan", "preFloorplan", log, progress=True
    )
    if not step.ok:
        typer.echo(f"the first floorplan pass failed, see {log}")
        raise typer.Exit(code=1)
    project.zero_macro_halos(directory, log)
    project.clear_pdn_stripes(directory)
    # Global placement puts each row's FrameData flops beside the row and each
    # column's strobe gates under the column; legalising alone left all 3105
    # cells at one corner and the router at 56% overflow. Overflow bottoms out
    # at 0.147 around iteration 300, the cells still over the fabric then, and
    # DreamPlace's divergence guard restarts it towards 0.70, so it stops at
    # 0.15 and the legaliser moves the rest into the free rows.
    x0, y0 = shape.origin
    project.set_params(
        directory,
        {
            "place.target_overflow": "0.15",
            "place.init_loc_perc_x": f"{x0 / shape.width:.4f}",
            "place.init_loc_perc_y": f"{y0 / shape.height:.4f}",
        },
        log,
    )
    # After the last `param set`: each one rewrites every STA liberty path
    # outside the PDK as if it were inside it, `/home/...` becoming
    # `<pdk>/home/...`, and STA then refuses the missing files.
    project.add_macro_timing(
        directory, [kinds["lib"] for kinds in views.values()], MACRO_CORNER
    )
    text = paths().fabric_verilog.read_text()
    ports = set(
        toprun.top_ports(project.synthesis_netlist(directory, toprun.TOP_MODULE))
    )
    fabric_pins = toprun.fabric_pins(layout, fabric, netlist, text, shape, ports)
    config_names = sorted(ports - {pin.name for pin in fabric_pins})
    pins = fabric_pins + toprun.config_pins(config_names, shape)
    if {pin.name for pin in pins} != ports or len(pins) != len(ports):
        raise typer.BadParameter("the pin plan and the synthesised ports disagree")
    placed = ioplace.install(
        project.workspace_of(directory), pins, (shape.width, shape.height)
    )
    typer.echo(f"{placed}; {len(config_names)} of them configuration ports")
    step = project.run_range(
        directory, "preFloorplan", "postFloorplan", log, progress=True
    )
    if not step.ok:
        typer.echo(f"floorplan failed, see {log}")
        raise typer.Exit(code=1)
    floorplan = project.floorplan_def(directory, toprun.TOP_MODULE)
    typer.echo(
        toprun.write_pdn(
            floorplan,
            layout,
            shape,
            {name: kinds["def"] for name, kinds in views.items()},
        )
    )
    project.drop_floorplan_database(directory, toprun.TOP_MODULE)
    step = project.run_range(directory, "place", "legalization", log, progress=True)
    if not step.ok:
        typer.echo(f"placement recorded as {step.state}, see {log}")
        raise typer.Exit(code=1)
    legalised = project.step_def(
        directory, toprun.TOP_MODULE, "legalization", "legalization_dreamplace"
    )
    withheld = toprun.withhold_seam_nets(legalised, set(netlist.wires))
    project.drop_step_database(
        directory, toprun.TOP_MODULE, "legalization", "legalization_dreamplace"
    )
    typer.echo(f"{len(withheld)} seam nets withheld from routing")
    typer.echo(
        toprun.repair_placement(
            legalised,
            pdk_root=config.fabric.pdk_root,
            macros=directory / "macros",
            sdc=directory / "top.sdc",
            reports=paths().build / "logs" / "top_repair",
        )
    )
    step = project.run_range(directory, "route", "filler", log, progress=True)
    typer.echo(
        f"top run recorded as {step.state} after {step.seconds:.0f} s, see {log}"
    )
    if not step.ok:
        raise typer.Exit(code=1)
    # Signed off on the database the router wrote, which lacks the seam nets;
    # `flow.stitch` is what proves those conduct. Harden writes the eFPGA_top
    # LEF, .lib and pin/OBS GDS abstract; the routed layout is drc_ecc's GDS.
    step = project.run_range(directory, "RCX", "Harden", log, progress=True)
    typer.echo(
        f"signoff and harden recorded as {step.state} after {step.seconds:.0f} s"
    )
    if not step.ok:
        raise typer.Exit(code=1)
    toprun.restore_seam_nets(project.final_def(directory, toprun.TOP_MODULE), withheld)
    typer.echo(f"{len(withheld)} seam nets restored to the final DEF, unrouted")


@app.command()
def assemble(
    stitcher: Stitcher = Stitcher.KLAYOUT,
    out: Path | None = None,
    directory: Path | None = None,
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
    manifest: Path | None = None,
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
    manifest = manifest or _fabric_geometry()
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
    source: Path | None = None,
    by: str = "cell",
    out: Path | None = None,
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

    source = source or paths().build / "eFPGA.gds"
    out = out or paths().build / "overlay"
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
