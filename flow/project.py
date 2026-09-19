"""Create and drive one ECC project per tile type.

Every `ecc.toml` this flow writes goes through `write_ecc_toml`, reading the
project configuration `flow.config` loads, so the clock, the PDK and the core
margin cannot drift between a tile run, the fabric run and the flat control.
The die and the PDN stripe pitch reach a run the same way: both are ordinary
registry parameters on ECC main, so nothing is patched into a workspace step
config after the fact.

The flow is broken in two places and both are forced. It stops after
`macroPlacement` so `flow.ioplace` can hand `postFloorplan` the pin plan, and
again after `postFloorplan` so `flow.defedit` can stretch the PDN to the die
edge. FINDINGS.md records a tile whose pins reverted to iEDA's own coordinates
at routing in a workspace resumed piecemeal, so everything after the second
break is one invocation and `flow.cli`'s `check_pins` tests that they held.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from flow.config import FabricSettings, Param

ECC = Path("/home/kelvin/side-project/ecc-spike/eccw-main")
WORKSPACE = "default"
# `build_harden_flow`'s step list, which the workspace only receives if the
# project was created with that preset. It is written in after synthesis
# instead, because a plain `ecc run` is the only call that creates a workspace
# and it takes no step selector, so a `harden` project would run the whole flow
# at the wrong die before the die could be set.
# `lec` is ECC's own default skip. `TimingOpt` needs Sizer, which is not
# installed here, and `postRouteLec` re-elaborates the routed netlist for a
# design this flow already checks by abutment.
SKIP_STEPS: tuple[str, ...] = ("lec", "TimingOpt", "postRouteLec")
# `build_rtl2gds_flow`'s chain, which a bounded workspace only holds as far as
# the step it was created with; `widen_flow` writes the rest back in.
CHAIN: tuple[tuple[str, str], ...] = (
    ("Synthesis", "yosys"),
    ("lec", "yosys_lec"),
    ("preFloorplan", "ecc"),
    ("macroPlacement", "dreamplace"),
    ("postFloorplan", "ecc"),
    ("place", "dreamplace"),
    ("CTS", "ecc"),
    ("legalization", "dreamplace"),
    ("TimingOpt", "sizer"),
    ("route", "ecc"),
    ("filler", "ecc"),
    ("RCX", "ecc"),
    ("sta", "ecc"),
    ("lvs", "ecc"),
    ("postRouteLec", "yosys_lec"),
    ("drc", "ecc"),
    ("Harden", "ecc"),
)
STRIPE_LAYERS: tuple[str, ...] = ("MET4", "MET5")
STRIPE_WIDTH_MICRON = 1.0
STRIPE_OFFSET_MICRON = 0.5
SITE_HEIGHT_MICRON = 1.4  # core7
# FABulous writes an instantiation with the module name alone on its line and a
# `ifdef EMULATION` parameter block between it and the instance name, so the two
# cannot be matched together. The leading token of a line is enough, since a
# known module name never opens a line for any other reason.
LEADING_TOKEN_RE = re.compile(r"^[ \t]*(?:\(\*[^*]*\*\)[ \t]*)?([A-Za-z_]\w*)", re.M)


@dataclass(frozen=True)
class StepResult:
    step: str
    returncode: int
    seconds: float
    state: str = ""

    @property
    def ok(self) -> bool:
        """Whether the step finished, by the workspace's record rather than the exit code.

        ECC exits 0 on a step that errored: a floorplan whose macros all failed
        `checkMacroPlacement` returns 0 in three seconds and leaves the step
        `Ongoing`, so the exit code alone reports a success that did not happen.
        """
        return self.returncode == 0 and self.state in ("", "Success")


@dataclass(frozen=True)
class Override:
    """One entry of ECC's parameter registry, set for a single project.

    `ecc param list` in a project directory names every parameter that can be
    overridden this way; anything outside that list has to be edited in the
    workspace's own step config, as the die size and the PDN pitch are.
    """

    section: str
    name: str
    value: str

    @classmethod
    def parse(cls, text: str) -> Override:
        key, separator, value = text.partition("=")
        if not separator or not value:
            raise ValueError(f"an override reads section.name=value, not {text!r}")
        section, dot, name = key.partition(".")
        if not dot or not name:
            raise ValueError(f"an override key reads section.name, not {key!r}")
        return cls(section=section, name=name, value=value)

    @property
    def key(self) -> str:
        return f"{self.section}.{self.name}"

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


def apply_overrides(directory: Path, overrides: Sequence[Override]) -> None:
    """Set each override in the project's `ecc.toml` through `ecc param set`.

    ECC coerces the value to the parameter's own type and rewrites a key the
    project already carries in place, neither of which hand-written TOML would
    do. It reports an unknown parameter or a mistyped value and then exits 0
    without writing the key, so the write is confirmed by reading the file back.
    """
    if not overrides:
        return
    reports: dict[Override, str] = {}
    for override in overrides:
        completed = subprocess.run(
            [str(ECC), "param", "set", override.key, override.value],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        # ECC writes its `[error]` block to stdout and only Fontconfig noise to
        # stderr, so stdout alone carries the reason a key was refused.
        reports[override] = completed.stdout.strip()
    params = tomllib.loads((directory / "ecc.toml").read_text()).get("params", {})
    refused = [
        override
        for override in overrides
        if override.name not in params.get(override.section, {})
    ]
    if refused:
        detail = "; ".join(f"{override}: {reports[override]}" for override in refused)
        raise ValueError(f"ECC refused an override: {detail}")


def _mask_comments(text: str) -> str:
    without_block = re.sub(
        r"/\*.*?\*/", lambda m: " " * len(m.group(0)), text, flags=re.S
    )
    return re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), without_block)


def source_index(roots: list[Path]) -> dict[str, Path]:
    """Map every module name under `roots` to the file declaring it, first root wins.

    FABulous copies a shared BEL such as `Config_access` into every tile that
    uses it, and the copies differ in whitespace and comments, so precedence is
    the caller's ordering: the tile's own directory first, then the shared ones.
    Two declarations inside one root are a real conflict and stop the run.
    """
    index: dict[str, Path] = {}
    for root in roots:
        local: dict[str, Path] = {}
        for path in sorted(root.rglob("*.v")):
            for module in re.findall(
                r"^module\s+(\w+)", _mask_comments(path.read_text()), re.M
            ):
                if module in local:
                    raise ValueError(
                        f"{root} declares {module} in {local[module]} and {path}"
                    )
                local[module] = path
        for module, path in local.items():
            index.setdefault(module, path)
    return index


def dependencies(top: str, index: dict[str, Path]) -> list[Path]:
    """Return the files a tile needs, leaves first, following instantiations.

    Yosys is given the closure rather than the whole project because an
    unrelated tile's switch matrix would otherwise be elaborated into every run.
    """
    if top not in index:
        raise ValueError(f"no Verilog declares module {top}")
    ordered: list[Path] = []
    seen: set[str] = set()

    def walk(module: str) -> None:
        if module in seen:
            return
        seen.add(module)
        path = index[module]
        text = _mask_comments(path.read_text())
        for candidate in LEADING_TOKEN_RE.findall(text):
            if candidate in index and candidate != module:
                walk(candidate)
        if path not in ordered:
            ordered.append(path)

    walk(top)
    return ordered


def stripe_tables(pitch_micron: float) -> str:
    """Render the PDN stripes, whole, at the pitch the fabric rows dictate."""
    return "".join(
        f"\n[[params.floorplan.pdn_generator.stripe]]\n"
        f'routing_layer_name = "{layer}"\n'
        f"width_micron = {STRIPE_WIDTH_MICRON}\n"
        f"pitch_micron = {pitch_micron}\n"
        f"offset_micron = {STRIPE_OFFSET_MICRON}\n"
        for layer in STRIPE_LAYERS
    )


def write_ecc_toml(
    directory: Path,
    *,
    top: str,
    settings: FabricSettings,
    params: Sequence[Param] = (),
    preset: str,
    sdc: str | None = None,
    note: str = "",
    stripe_pitch_micron: float | None = None,
) -> None:
    """Render one project's `ecc.toml` from the project configuration.

    Every project this flow writes goes through here, so that the clock, the PDK
    and the core margin cannot drift between a tile run, the fabric run and the
    flat control. `params` is already validated against ECC's registry by
    `flow.config`; anything outside that registry has no `ecc.toml` spelling and
    reaches a run through the workspace step configs instead.

    `stripe_pitch_micron` is rendered here rather than passed as a `Param`
    because `floorplan.pdn_generator.stripe` is a list of tables: ECC replaces
    the list wholesale rather than merging it, so every field of every stripe
    has to be restated and `Param` renders one scalar.
    """
    # A whole-micron margin is written as an integer, because that is what ECC
    # prints it back as and a diff against `ecc param list` should be empty.
    micron = settings.core_margin_micron
    margin: float | int = int(micron) if micron.is_integer() else micron
    sections = [
        f'[design]\nname = "{top}"\ntop = "{top}"\nrtl = ["filelist.f"]\n'
        f'clock_port = "{settings.clock_port}"\n'
        f"frequency_mhz = {settings.frequency_mhz}\n",
        f'[pdk]\nname = "{settings.pdk_name}"\nroot = "{settings.pdk_root}"\n',
    ]
    if sdc is not None:
        sections.append(
            f"# Without this ECC writes its own SDC from clock_port and ignores {sdc}.\n"
            f'[pdk.overrides]\nsdc = "{sdc}"\n'
        )
    # ECC main rejects `[flow].run`, and records the skip policy when the
    # workspace is first created, so both belong here rather than in a later
    # edit that the ledger would not see.
    sections.append(
        f'[flow]\npreset = "{preset}"\n'
        f"skip_steps = {json.dumps(list(SKIP_STEPS))}\n"
    )
    if stripe_pitch_micron is not None:
        sections.append(stripe_tables(stripe_pitch_micron).lstrip("\n"))
    # The margin is the one registry entry the config files cannot carry, so it
    # is rendered here and the floorplan section always exists to hold it. A note
    # leads the section, since what it explains is the margin.
    grouped: dict[str, list[str]] = {"floorplan": [f"core_margin = [{margin}, {margin}]"]}
    for param in params:
        grouped.setdefault(param.section, []).append(param.render())
    for section, entries in grouped.items():
        lead = note.rstrip("\n") + "\n" if note and section == "floorplan" else ""
        sections.append(lead + f"[params.{section}]\n" + "\n".join(entries) + "\n")
    (directory / "ecc.toml").write_text("\n".join(sections))


def create_project(
    *,
    directory: Path,
    top: str,
    sources: list[Path],
    settings: FabricSettings,
    params: Sequence[Param] = (),
    preset: str = "syn_sta",
    overrides: Sequence[Override] = (),
    stripe_pitch_micron: float,
) -> None:
    """Lay out an ECC project for one tile, copying its Verilog into `rtl/`.

    `stripe_pitch_micron` is the pitch the plan settled on, not the one the
    fabric configuration asked for. `flow.plan` pulls the asked-for pitch onto
    a whole division of the row height, and its pin offsets dodge stripes at
    the pitch it settled on, so giving ECC the other one puts every N/S pin a
    few hundred nanometres from a stripe it was placed to avoid.
    """
    rtl = directory / "rtl"
    rtl.mkdir(parents=True, exist_ok=True)
    names = []
    for source in sources:
        target = rtl / source.name
        content = source.read_bytes()
        # Only write on a real change, and carry the source's timestamp over, so
        # that a copy's mtime still says whether a netlist built from it is
        # stale. Rewriting an identical file with a fresh timestamp made a valid
        # netlist look older than the sources it came from.
        if not target.exists() or target.read_bytes() != content:
            shutil.copy2(source, target)
        names.append(f"rtl/{source.name}")
    (directory / "filelist.f").write_text("\n".join(names) + "\n")
    write_ecc_toml(
        directory,
        top=top,
        settings=settings,
        params=params,
        preset=preset,
        stripe_pitch_micron=stripe_pitch_micron,
    )
    apply_overrides(directory, overrides)


def workspace_of(directory: Path) -> Path:
    """Return a run's workspace as an absolute path.

    `run` invokes ECC with `cwd=directory`, so a relative `--workspace` is
    resolved against the project directory rather than against the caller's:
    `build/flat_0.5` came back as `build/flat_0.5/build/flat_0.5/runs/default`
    and ECC rejected it as invalid.
    """
    return directory.resolve() / WORKSPACE


def run(directory: Path, arguments: list[str], log: Path) -> StepResult:  # noqa: D401
    """Invoke ECC, appending its output to `log`, and return without raising.

    A failing step is reported rather than thrown so that a batch over fifteen
    tile types finishes and names every tile that failed instead of the first.
    """
    import time

    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with log.open("a") as handle:
        handle.write(f"\n=== ecc {' '.join(arguments)} ===\n")
        handle.flush()
        completed = subprocess.run(
            [str(ECC), *arguments],
            cwd=directory,
            stdout=handle,
            stderr=subprocess.STDOUT,
        )
    return StepResult(
        step=arguments[-1] if arguments else "",
        returncode=completed.returncode,
        seconds=time.monotonic() - start,
    )


def step_state(directory: Path, step: str) -> str:
    """Return what the workspace records for `step`, which is the real outcome."""
    path = workspace_of(directory) / "home" / "flow.json"
    for entry in json.loads(path.read_text())["steps"]:
        if entry["name"] == step:
            return entry["state"]
    raise KeyError(f"{path} records no step named {step}")


def run_step(directory: Path, step: str, log: Path) -> StepResult:
    workspace = workspace_of(directory)
    result = run(
        directory,
        ["run", "--workspace", str(workspace), "--only", step, "--force"],
        log,
    )
    return StepResult(
        step, result.returncode, result.seconds, step_state(directory, step)
    )


def run_from(directory: Path, step: str, log: Path) -> StepResult:
    """Run `step` and every step after it in one invocation.

    `--force` is rejected alongside `--from`, so the steps have to be Unstart,
    which `install_harden_flow` arranges.
    """
    workspace = workspace_of(directory)
    result = run(directory, ["run", "--workspace", str(workspace), "--from", step], log)
    return StepResult(
        step, result.returncode, result.seconds, step_state(directory, step)
    )


def floorplan_def(directory: Path, top: str) -> Path:
    return (
        workspace_of(directory) / "postFloorplan_ecc" / "output" / f"{top}_postFloorplan.def.gz"
    )


def drop_floorplan_database(directory: Path, top: str) -> None:
    """Delete the binary floorplan database so the next step reads the DEF.

    `create_db_engine` prefers `<step>/output/<design>_<step>_db` and only falls
    back to `read_def` when it is absent, so an externally written PINS section
    is ignored while the database is there.
    """
    import shutil

    database = (
        workspace_of(directory) / "postFloorplan_ecc" / "output" / f"{top}_postFloorplan_db"
    )
    if database.exists():
        shutil.rmtree(database)


def final_def(directory: Path, top: str) -> Path:
    return workspace_of(directory) / "filler_ecc" / "output" / f"{top}_filler.def.gz"


def final_gds(directory: Path, top: str) -> Path:
    candidates = sorted(
        (workspace_of(directory) / "filler_ecc" / "output").glob("*.gds")
    )
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"expected one GDS in {workspace_of(directory)}/filler_ecc/output, found {candidates}"
        )
    return candidates[0]


def create_workspace(directory: Path, log: Path, *, to: str) -> StepResult:
    """Run the project up to `to`, materialising the workspace on the way.

    The bound is what leaves a clean point to intervene before the next step:
    ECC records its step ledger when the workspace is first created, and a
    workspace already holding a ledger is resumed rather than recreated.
    """
    if (workspace_of(directory) / "home" / "flow.json").exists():
        # `ecc run --project` refuses a workspace that already exists, and a
        # rerun of one tile in a batch must not be that error.
        return StepResult(step="workspace", returncode=0, seconds=0.0)
    result = run(
        directory,
        [
            "run",
            "--project",
            str(directory.resolve()),
            "--workspace",
            WORKSPACE,
            "--from",
            "synthesis",
            "--to",
            to,
            "--plain",
        ],
        log,
    )
    return StepResult(to, result.returncode, result.seconds, step_state(directory, to))


def run_range(directory: Path, first: str, last: str, log: Path) -> StepResult:
    """Run `first` through `last` inclusive in one invocation."""
    result = run(
        directory,
        ["run", "--workspace", WORKSPACE, "--from", first, "--to", last, "--plain"],
        log,
    )
    return StepResult(
        first, result.returncode, result.seconds, step_state(directory, last)
    )


def set_params(directory: Path, assignments: dict[str, object], log: Path) -> None:
    """Set workspace-scope parameters, which the next step refreshes its config from.

    A project-scope `ecc.toml` value is read when the workspace is created and
    not afterwards, so a die sized from a measurement the first floorplan made
    has to be set here instead.
    """
    for key, value in assignments.items():
        rendered = value if isinstance(value, str) else json.dumps(value)
        result = run(
            directory, ["param", "set", key, rendered, "--workspace", WORKSPACE], log
        )
        if result.returncode:
            raise ValueError(f"ecc param set {key} {rendered} failed, see {log}")


def widen_flow(directory: Path) -> None:
    """Extend a bounded workspace's step ledger to the whole preset.

    A workspace remembers the range it was created with, in `home/flow.json`
    and again in the project manifest, and `ecc run` validates a step selector
    against that ledger rather than against the preset. `ecc workspace refresh`
    would widen it but resets every step to Unstart and deletes the outputs
    with them, so the ledger is widened here instead and what has already run
    stays run.
    """
    path = workspace_of(directory) / "home" / "flow.json"
    data = json.loads(path.read_text())
    done = {step["name"]: step for step in data["steps"]}
    if "Synthesis" not in done:
        raise ValueError(f"{path} records no Synthesis, so there is nothing to extend")
    data["steps"] = [
        done.get(
            name,
            {
                "name": name,
                "tool": tool,
                "state": "Unstart",
                "runtime": "",
                "peak memory (mb)": 0,
                "info": {},
            },
        )
        for name, tool in CHAIN
        if name not in SKIP_STEPS
    ]
    path.write_text(json.dumps(data, indent=4))

    manifest = directory / "project.json"
    record = json.loads(manifest.read_text())
    for workspace in record["workspaces"]:
        if workspace["workspace_id"] == WORKSPACE:
            workspace["end_step"] = CHAIN[-1][0]
    manifest.write_text(json.dumps(record, indent=1))


def harden_views(directory: Path, top: str) -> tuple[Path, Path, Path]:
    """Return the abstract LEF, the extracted timing model and the GDS of a macro."""
    output = workspace_of(directory) / "Harden_ecc" / "output"
    views = tuple(output / f"{top}_Harden.{suffix}" for suffix in ("lef", "lib", "gds"))
    missing = [view for view in views if not view.exists()]
    if missing:
        raise FileNotFoundError(f"{top} has not been hardened: {missing} are absent")
    return views


def add_macro_views(directory: Path, *, lefs: list[Path], libs: list[Path]) -> None:
    """Bring the hardened tiles into a parent run as library cells.

    `chipcompiler.data.workspace` reads `db_ecc.json` back into
    `pdk.lefs` and `pdk.libs` on load and writes it out again, so appending here
    is the supported route. `[pdk.overrides]` is whole-field replacement and
    would drop the standard-cell library.
    """
    config = workspace_of(directory) / "config" / "db_ecc.json"
    if not config.exists():
        raise FileNotFoundError(f"{config} does not exist. Run one step first.")
    data = json.loads(config.read_text())
    for key, additions in (("lef_paths", lefs), ("lib_path", libs)):
        existing = data["INPUT"][key]
        data["INPUT"][key] = existing + [
            str(p) for p in additions if str(p) not in existing
        ]
    config.write_text(json.dumps(data, indent=4))


def zero_macro_halos(directory: Path, log: Path) -> None:
    """Remove the 3 um placement and routing halos, which abutted macros cannot have.

    Through the parameters rather than the config file, because both halos are
    registry entries and the refresh rewrites them before every step.
    """
    set_params(
        directory,
        {
            "floorplan.macro_placer.macro_placement_halo": 0.0,
            "floorplan.macro_placer.macro_routing_halo": 0.0,
        },
        log,
    )


def _floorplan_cells(directory: Path) -> set[str]:
    """Return the cell names the floorplan itself inserts, from its own config.

    Taken from `phy_placer` rather than written out here, so a PDK with
    different tap and endcap cells needs no change.
    """
    data = json.loads(
        (workspace_of(directory) / "config" / "floorplan_ecc.json").read_text()
    )
    placer = data["phy_placer"]
    names = {placer["well_tap"]["cell_name"]}
    names.update(placer["side_endcap"].values())
    for group in ("edge_endcap", "boundary_tap"):
        for key, value in placer[group].items():
            if key.endswith("cell_name_list"):
                names.update(value)
    return names


def needs_placement(directory: Path, step_def: Path) -> bool:
    """Say whether a tile has enough logic for DreamPlace to place.

    A FABulous terminator is pure feedthrough, so Yosys collapses it to wires and
    the tile reaches placement with nothing but the floorplan's own taps and
    endcaps, or with a single tie cell beside them. DreamPlace does not report
    either as unplaceable: with no movable cell it takes the minimum of an empty
    array, and with one it converts a NaN to an integer. The bound is empirical
    and is stated as fewer movable cells than there are standard-cell rows, which
    separates the two observed failures, at zero and at one cell, from the
    smallest real tile by three orders of magnitude.
    """
    from flow.defedit import read_def

    text = read_def(step_def)
    fixed = _floorplan_cells(directory)
    block = re.search(r"^COMPONENTS.*?^END COMPONENTS", text, re.S | re.M)
    if block is None:
        raise ValueError(f"{step_def} has no COMPONENTS section")
    masters = re.findall(r"^\s*- \S+ (\S+)", block.group(0), re.M)
    movable = sum(1 for master in masters if master not in fixed)
    return movable >= len(re.findall(r"^ROW ", text, re.M))


def bypass_placement(
    directory: Path, top: str, source_step: str, source_dir: str
) -> None:
    """Hand a tile with no logic straight from `source_step` to routing.

    Placement, CTS and legalisation have nothing to do on a tile whose only
    cells are the floorplan's own taps, and DreamPlace aborts rather than saying
    so. `create_db_engine` reads a step's DEF when no binary database sits beside
    it, so seeding the outputs it would have written is enough.
    """
    import shutil

    workspace = workspace_of(directory)
    origin = workspace / source_dir / "output"
    skipped = (
        ("place", "place_dreamplace"),
        ("CTS", "CTS_ecc"),
        ("legalization", "legalization_dreamplace"),
    )
    for name, folder in skipped:
        target = workspace / folder / "output"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for suffix in ("def.gz", "v.gz"):
            source = origin / f"{top}_{source_step}.{suffix}"
            if not source.exists():
                raise FileNotFoundError(
                    f"{source} does not exist, so {name} cannot be seeded"
                )
            shutil.copy(source, target / f"{top}_{name}.{suffix}")

    path = workspace / "home" / "flow.json"
    data = json.loads(path.read_text())
    done = {name for name, _ in skipped}
    for step in data["steps"]:
        if step["name"] in done:
            step["state"] = "Success"
    path.write_text(json.dumps(data, indent=4))


def synthesis_netlist(directory: Path, top: str) -> Path:
    """Return a run's gate netlist, and refuse when Yosys did not write one."""
    path = (
        workspace_of(directory) / "Synthesis_yosys" / "output" / f"{top}_Synthesis.v.gz"
    )
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist, so synthesis produced no netlist"
        )
    return path


def subflow_state(directory: Path, step: str, name: str) -> str:
    """Return what a step's subflow records for one of its own stages."""
    path = workspace_of(directory) / step / "subflow.json"
    for entry in json.loads(path.read_text()).get("steps", []):
        if entry["name"] == name:
            return entry["state"]
    raise KeyError(f"{path} records no stage named {name}")


def force_step_state(directory: Path, step: str, state: str) -> None:
    """Record `state` for `step`, for a step whose artefact is known good."""
    path = workspace_of(directory) / "home" / "flow.json"
    data = json.loads(path.read_text())
    for entry in data["steps"]:
        if entry["name"] == step:
            entry["state"] = state
            path.write_text(json.dumps(data, indent=4))
            return
    raise KeyError(f"{path} records no step named {step}")


def netlist_is_current(directory: Path, top: str) -> bool:
    """Say whether the gate netlist is at least as new as every source it came from.

    The workspace's own subflow record is not enough on its own: a run that is
    stopped and returns later rewrites it, so a netlist that is present and
    current can be filed under a step marked unstarted.
    """
    netlist = synthesis_netlist(directory, top)
    newest = max(path.stat().st_mtime for path in (directory / "rtl").glob("*.v"))
    return netlist.stat().st_mtime >= newest


def set_core_util(directory: Path, utilisation: float) -> None:
    """Change a workspace's target core utilisation without re-running synthesis.

    `_refresh_floorplan_config` reads `Core.Utilitization` out of the run's own
    parameters on every floorplan, so a die can be resized from an existing
    netlist. `ecc.toml` is read only when the workspace is created, so editing it
    alone changes nothing, and recreating the workspace repeats a synthesis whose
    analysis stage fails on a design this size.
    """
    path = workspace_of(directory) / "home" / "parameters.json"
    data = json.loads(path.read_text())
    data["Core"]["Utilitization"] = utilisation
    path.write_text(json.dumps(data, indent=4))


def floorplan_measurement(directory: Path) -> Path:
    """Return the feature file recording what the last floorplan actually built."""
    return workspace_of(directory) / "postFloorplan_ecc" / "feature" / "postFloorplan.db.json"


def compiled_die(directory: Path, top: str) -> tuple[float, float]:
    """Return the die, in microns, that the last floorplan of `top` actually built.

    Read from the floorplan's own measurement rather than from the plan that
    asked for it, so that a tile hardened with an override or its own `[die]`
    table reports what it really is.
    """
    measurement = floorplan_measurement(directory)
    if not measurement.exists():
        raise FileNotFoundError(
            f"{top} has never been floorplanned, so there is no compiled die to "
            f"read: {measurement} does not exist. Run "
            f"`task harden-one TILE={top} ANCHOR=<microns>` once to build it."
        )
    layout = json.loads(measurement.read_text())["Design Layout"]
    return layout["die_bounding_width"], layout["die_bounding_height"]


def compiled_usage(directory: Path) -> float:
    """Return how much of the core the last floorplan of this tile filled."""
    measurement = json.loads(floorplan_measurement(directory).read_text())
    return measurement["Design Layout"]["core_usage"]


def die_side(
    directory: Path, top: str, utilisation: float, *, core_margin_micron: float
) -> float:
    """Return the square die, in microns, that fills to `utilisation` with logic.

    The cell area comes from the last floorplan's own measurement rather than
    from a target, because ECC's `Core.Utilitization` is rewritten from the
    finished floorplan and does not survive being set beforehand. The core
    height is rounded up to a whole number of `core7` rows, since `buildCore`
    aligns down and would otherwise drop one.
    """
    layout = json.loads(floorplan_measurement(directory).read_text())["Design Layout"]
    cell_area = layout["core_area"] * layout["core_usage"]
    core = (cell_area / utilisation) ** 0.5
    rows = -(-core // (SITE_HEIGHT_MICRON))
    return round(rows * SITE_HEIGHT_MICRON + 2 * core_margin_micron, 3)
