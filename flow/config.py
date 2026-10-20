"""Read the ECC settings every build in this project is run with.

`ecc.toml`'s `[params.<section>]` tables reach ECC's parameter registry, and
`PARAM_REGISTRY` below is what `ecc param list` prints. A key outside it is
refused at load rather than written into `ecc.toml`, where ECC would ignore it
without saying so. The registry grew on ECC main to hold the die and the PDN
stripes, so nothing this project sets has to be patched into a workspace step
config after synthesis any more.

The file layering mirrors the `gds_config.yaml` files it replaces.
`Fabric/ecc_config.toml` carries what is fabric-wide by construction, so a tile
setting `core_margin_micron` or `stripe_pitch_micron` is rejected rather than
honoured: the stripe pitch has to divide the row height and the margin decides
where abutted cores meet, and neither is a single tile's to choose.
`Tile/include/ecc_config.toml` carries the parameter defaults every tile type is
built with, and an optional `Tile/<type>/ecc_config.toml` replaces individual
entries for one type.

A die is still not written where it is asked for. A `Tile/<type>/ecc_config.toml`
may carry a `[die]` table, and `flow.plan` binds it to the columns and rows that
type occupies before deriving every pin offset and seam from the result, so
`flow.verify` proves the fabric meets on the die that was asked for and only
then does the size reach `ecc.toml`. Setting `floorplan.die_builder` directly
would put it past the only check that can tell whether it abuts, which is why
`gds_config.yaml`'s per-tile `DIE_AREA` has no equivalent here.

A die edge set by a column or row a variant fills differently belongs to the
variant, not the tile. `NE_term` is as wide as whatever sits in the east column,
`E_BRAM` in one variant and `E_IO` in the other, so `fabrics/<variant>/dies.toml`
supplies that edge and the tile's own `[die]` keeps the one both variants share.
An edge stated in both places is refused rather than resolved.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flow.variant import Paths

CONFIG_NAME = "ecc_config.toml"

# `ecc param list` in a project directory, with the type each entry is printed
# at. A key outside this table is refused at load rather than written into
# `ecc.toml`, where ECC would silently ignore it. ECC main added the die to the
# registry, so `floorplan.die_builder` is settable here; the PDN stripes are
# registry entries too but are a list of tables rather than a scalar, so
# `flow.project.stripe_tables` renders them and no key stands for them.
PARAM_REGISTRY: dict[str, type] = {
    "design.frequency_mhz": float,
    "floorplan.die_builder.mode": str,
    "floorplan.die_builder.die_size.width_micron": float,
    "floorplan.die_builder.die_size.height_micron": float,
    "floorplan.core_util": float,
    "floorplan.core_margin": list,
    "floorplan.aspect_ratio": float,
    "synth.max_fanout": int,
    "place.target_density": float,
    "place.target_overflow": float,
    "place.global_right_padding": int,
    "place.cell_padding_x": int,
    "place.routability_opt": int,
    # DreamPlace fills every remaining scrap of whitespace with filler nodes
    # sized from `placeable_area * target_density`, and target_density
    # saturates at 1.0 on an abutted tile, so at these utilisations the fillers
    # compete with real cells for legalisation slack.
    "place.enable_fillers": int,
    # ECC's DreamPlace defaults to global placement and legalisation with no
    # detailed placement at all.
    "place.detailed_place_flag": int,
    "route.bottom_layer": str,
    "route.top_layer": str,
    "sta.max_paths": int,
}

# Registry entries this project derives instead of reading, each with where the
# value does come from, so that one value cannot be given twice or reach a run
# unchecked. `floorplan.die_builder` is named at the depth a file can reach: a
# `[params]` table is read one level deep, so
# `[params.floorplan.die_builder.die_size]` arrives as the section `floorplan`
# holding `die_builder`, and naming the leaves would never match.
RESERVED_PARAMS: dict[str, str] = {
    "design.frequency_mhz": "[design] frequency_mhz, which every tile shares",
    "floorplan.core_margin": "[fabric] core_margin_micron, which decides where "
    "two abutted cores meet",
    "floorplan.die_builder": "the anchor, or a [die] table in this tile's own "
    "file; a die set here would reach the run without flow.plan binding it to "
    "the columns and rows the type occupies, or flow.verify proving the fabric "
    "still meets on it",
}


@dataclass(frozen=True)
class Param:
    """One `[params.<section>]` entry, carrying the type ECC printed it at."""

    section: str
    name: str
    value: float | str

    @property
    def key(self) -> str:
        return f"{self.section}.{self.name}"

    def render(self) -> str:
        """Render the entry as TOML, quoting a layer name and leaving a number bare."""
        literal = f'"{self.value}"' if isinstance(self.value, str) else repr(self.value)
        return f"{self.name} = {literal}"


@dataclass(frozen=True)
class TileDie:
    """One tile type's requested die, from its own `[die]` table.

    Either edge may be left out, and the one left out keeps the size `flow.plan`
    scales from `eFPGA_geometry.csv`. Microns rather than DBU because this is
    what a person writes; `flow.plan` refuses an edge that does not land on the
    site and row grid abutment leaves.
    """

    width_micron: float | None = None
    height_micron: float | None = None


ORIENTATIONS = ("R0", "R90", "R180", "R270", "MX", "MY", "MX90", "MY90")


@dataclass(frozen=True)
class TileMacro:
    """The hard macro one tile type carries, from its own `[macro]` table.

    A tile with no `[macro]` table is standard cells alone and takes none of
    this. The coordinates are the macro's lower-left corner in the tile's own
    die, fixed rather than placed, because an abutted tile has no room for
    DreamPlace to move it into and the pin plan is drawn around where it sits.
    """

    cell: str
    lef: Path
    lib: Path
    x_micron: float
    y_micron: float
    orientation: str
    # Measured from the LEF rather than written down, so the coordinates above
    # and the outline they place cannot describe different macros.
    width_micron: float
    height_micron: float


@dataclass(frozen=True)
class FabricSettings:
    """The values shared by every project this flow writes, tile and fabric alike."""

    clock_port: str
    frequency_mhz: float
    pdk_name: str
    pdk_root: Path
    core_margin_micron: float
    stripe_pitch_micron: float


@dataclass(frozen=True)
class Config:
    """The whole project's ECC configuration, as the three files describe it."""

    fabric: FabricSettings
    fabric_params: tuple[Param, ...]
    tile_defaults: tuple[Param, ...]
    tile_params: dict[str, tuple[Param, ...]]
    tile_die: dict[str, TileDie]
    tile_macro: dict[str, TileMacro]
    synthesis_default: Synthesis
    tile_synthesis: dict[str, Synthesis]
    # Tile type to its `[repair]` table; a type without one is routed as
    # DreamPlace legalised it.
    tile_repair: dict[str, Repair]

    def strategy_for(self, tile_type: str) -> str | None:
        """Return the ABC strategy this tile type synthesises with, if any.

        A tile that names none falls back to the shared default, and a fabric
        that names none anywhere leaves Yosys on its own `DELAY 4`.
        """
        own = self.tile_synthesis.get(tile_type)
        return (own and own.strategy) or self.synthesis_default.strategy

    def avoids_weak_drives(self, tile_type: str) -> bool:
        """Whether this tile type synthesises with `project.WEAK_DRIVES` banned."""
        own = self.tile_synthesis.get(tile_type)
        if own is not None and own.avoid_weak_drives is not None:
            return own.avoid_weak_drives
        return bool(self.synthesis_default.avoid_weak_drives)

    def params_for(self, tile_type: str) -> tuple[Param, ...]:
        """Return one tile type's parameters, its own entries replacing the defaults."""
        merged = {param.key: param for param in self.tile_defaults}
        merged.update(
            {param.key: param for param in self.tile_params.get(tile_type, ())}
        )
        return tuple(merged[key] for key in sorted(merged))


def _read(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text())


def _params(table: object, source: Path) -> tuple[Param, ...]:
    """Validate one file's `[params.*]` tables against ECC's registry."""
    if table is None:
        return ()
    if not isinstance(table, dict):
        raise ValueError(f"{source}: [params] is not a table")
    found = []
    for section, entries in table.items():
        if not isinstance(entries, dict):
            raise ValueError(f"{source}: [params.{section}] is not a table")
        for name, value in entries.items():
            key = f"{section}.{name}"
            if key in RESERVED_PARAMS:
                raise ValueError(
                    f"{source}: {key} cannot be given as a parameter. It comes "
                    f"from {RESERVED_PARAMS[key]}"
                )
            if key not in PARAM_REGISTRY:
                raise ValueError(
                    f"{source}: {key} is not an ECC parameter. `ecc param list` in a "
                    f"project directory names all {len(PARAM_REGISTRY)} of them"
                )
            found.append(
                Param(section=section, name=name, value=_typed(key, value, source))
            )
    return tuple(sorted(found, key=lambda param: param.key))


def _typed(key: str, value: object, source: Path) -> float | str:
    """Coerce a TOML value to the type ECC prints the parameter at, or fail."""
    wanted = PARAM_REGISTRY[key]
    mistyped = ValueError(
        f"{source}: {key} takes a {wanted.__name__}, not a {type(value).__name__}"
    )
    # A bool is an `int` subclass, so it is rejected here rather than accepted as
    # an integer by the registry check below.
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise mistyped
    # TOML has one integer type, so an integral float parameter reads back as
    # `int` and is widened.
    if wanted is float and isinstance(value, int):
        return float(value)
    if not isinstance(value, wanted):
        raise mistyped
    return value


def _die(table: object, source: Path) -> TileDie:
    """Read one tile type's requested die, refusing a key or a value ECC cannot use."""
    if table is None:
        return TileDie()
    if not isinstance(table, dict):
        raise ValueError(f"{source}: [die] is not a table")
    unknown = sorted(set(table) - {"width_micron", "height_micron"})
    if unknown:
        raise ValueError(
            f"{source}: [die] takes width_micron and height_micron, not {unknown}"
        )

    def edge(key: str) -> float | None:
        if key not in table:
            return None
        value = table[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{source}: die.{key} is not a number")
        if value <= 0:
            raise ValueError(f"{source}: die.{key} is {value}, which is not a die edge")
        return float(value)

    return TileDie(
        width_micron=edge("width_micron"), height_micron=edge("height_micron")
    )


def _variant_dies(source: Path, tile_types: tuple[str, ...]) -> dict[str, TileDie]:
    """Read the die edges a variant fixes, one `[<type>]` table per tile type."""
    if not source.exists():
        raise FileNotFoundError(
            f"{source} does not exist. Every variant states the die edges its grid "
            "fixes for tile types it shares with the other, even if there are none."
        )
    table = _read(source)
    unknown = sorted(set(table) - set(tile_types)) if tile_types else []
    if unknown:
        raise ValueError(f"{source}: {unknown} are not tile types this variant places")
    return {name: _die(entry, source) for name, entry in table.items()}


def _merge_die(own: TileDie, variant: TileDie, tile_type: str, source: Path) -> TileDie:
    """Fill the edges a tile leaves open with the variant's, refusing any set twice."""

    def edge(name: str, mine: float | None, theirs: float | None) -> float | None:
        if mine is not None and theirs is not None:
            raise ValueError(
                f"{source}: {tile_type}.{name} is also set in Tile/{tile_type}/"
                f"{CONFIG_NAME}; state each edge in one place"
            )
        return mine if theirs is None else theirs

    return TileDie(
        width_micron=edge("width_micron", own.width_micron, variant.width_micron),
        height_micron=edge("height_micron", own.height_micron, variant.height_micron),
    )


def _macro(table: object, source: Path) -> TileMacro | None:
    """Read one tile type's hard macro, refusing a view that is not on disk.

    The LEF and the liberty are checked here rather than at harden time because
    a missing view only shows up as an unplaceable instance forty minutes in.
    """
    if table is None:
        return None
    if not isinstance(table, dict):
        raise ValueError(f"{source}: [macro] is not a table")
    wanted = {"cell", "lef", "lib", "x_micron", "y_micron", "orientation"}
    missing = sorted(wanted - set(table))
    unknown = sorted(set(table) - wanted)
    if missing or unknown:
        raise ValueError(
            f"{source}: [macro] takes exactly {sorted(wanted)}"
            + (f", missing {missing}" if missing else "")
            + (f", not {unknown}" if unknown else "")
        )
    views = {}
    for key in ("lef", "lib"):
        value = table[key]
        if not isinstance(value, str):
            raise ValueError(f"{source}: macro.{key} is not a path")
        path = (source.parent / value).resolve()
        if not path.is_file():
            raise ValueError(f"{source}: macro.{key} {path} does not exist")
        views[key] = path
    for key in ("cell", "orientation"):
        if not isinstance(table[key], str):
            raise ValueError(f"{source}: macro.{key} is not a string")
    if table["orientation"] not in ORIENTATIONS:
        raise ValueError(
            f"{source}: macro.orientation {table['orientation']!r} is not one ECC "
            f"takes: {list(ORIENTATIONS)}"
        )
    for key in ("x_micron", "y_micron"):
        value = table[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{source}: macro.{key} is not a number")
        if value < 0:
            raise ValueError(f"{source}: macro.{key} is {value}, outside the die")
    size = re.search(
        rf"MACRO {re.escape(table['cell'])}\b.*?SIZE\s+([\d.]+)\s+BY\s+([\d.]+)",
        views["lef"].read_text(),
        re.S,
    )
    if size is None:
        raise ValueError(
            f"{source}: macro.lef {views['lef']} declares no MACRO {table['cell']} "
            "with a SIZE"
        )
    turned = table["orientation"] in ("R90", "R270", "MX90", "MY90")
    edges = (float(size.group(1)), float(size.group(2)))
    return TileMacro(
        cell=table["cell"],
        lef=views["lef"],
        lib=views["lib"],
        x_micron=float(table["x_micron"]),
        y_micron=float(table["y_micron"]),
        orientation=table["orientation"],
        width_micron=edges[turned],
        height_micron=edges[not turned],
    )


STRATEGY = re.compile(r"^(DELAY|AREA|BALANCE) (\d+)$")


@dataclass(frozen=True)
class Synthesis:
    """One layer's `[synthesis]` table; `None` leaves a key to the layer below."""

    strategy: str | None = None
    avoid_weak_drives: bool | None = None


def _synthesis(table: object, source: Path) -> Synthesis:
    """Read one layer's `[synthesis]` table, refusing a spelling Yosys would reject.

    Neither key is an ECC parameter, so neither can go under `[params]`: ECC
    reads the strategy from `YOSYS_SYNTH_STRATEGY`, and `avoid_weak_drives`
    reaches it as `[pdk.overrides] dont_use`. Checking the strategy's spelling
    here matters because a bad one is not caught until the synthesis script has
    already read the liberty files and exits 1.
    """
    if table is None:
        return Synthesis()
    if not isinstance(table, dict):
        raise ValueError(f"{source}: [synthesis] is not a table")
    unknown = sorted(set(table) - {"strategy", "avoid_weak_drives"})
    if unknown:
        raise ValueError(
            f"{source}: [synthesis] takes strategy and avoid_weak_drives, not {unknown}"
        )
    strategy = table.get("strategy")
    if strategy is not None and (
        not isinstance(strategy, str) or not STRATEGY.match(strategy)
    ):
        raise ValueError(
            f"{source}: synthesis.strategy is {strategy!r}, not DELAY, AREA or "
            "BALANCE followed by an index, as in \"AREA 5\""
        )
    weak = table.get("avoid_weak_drives")
    if weak is not None and not isinstance(weak, bool):
        raise ValueError(f"{source}: synthesis.avoid_weak_drives is {weak!r}, not a bool")
    return Synthesis(strategy=strategy, avoid_weak_drives=weak)


@dataclass(frozen=True)
class Repair:
    """One tile's `[repair]` table: OpenROAD's slew and capacitance repair after
    legalisation and before ECC routes."""

    # Percent inside the liberty limits that `repair_design` buffers and sizes
    # to; None skips `repair_design`.
    margin_percent: float | None
    # Wire capacitance multiplier for the upsizing pass that follows; None
    # skips the pass.
    upsize_wire_scale: float | None


def _repair(table: object, source: Path) -> Repair | None:
    """Read a tile's `[repair]` table, which names one or both passes."""
    if table is None:
        return None
    if not isinstance(table, dict):
        raise ValueError(f"{source}: [repair] is not a table")
    keys = {"drv_margin_percent", "upsize_wire_scale"}
    if not table or not set(table) <= keys:
        raise ValueError(
            f"{source}: [repair] takes one or both of {sorted(keys)}, not {sorted(table)}"
        )
    margin = table.get("drv_margin_percent")
    if margin is not None and (
        isinstance(margin, bool)
        or not isinstance(margin, int | float)
        or not 0 <= margin < 100
    ):
        raise ValueError(
            f"{source}: repair.drv_margin_percent is {margin!r}, not 0 to 100"
        )
    scale = table.get("upsize_wire_scale")
    if scale is not None and (
        isinstance(scale, bool) or not isinstance(scale, int | float) or scale < 1
    ):
        raise ValueError(
            f"{source}: repair.upsize_wire_scale is {scale!r}, not a number from 1"
        )
    return Repair(
        margin_percent=None if margin is None else float(margin),
        upsize_wire_scale=None if scale is None else float(scale),
    )


def _section(table: dict[str, object], name: str, source: Path) -> dict[str, object]:
    value = table.get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"{source}: [{name}] is not a table")
    return value


def _fabric(table: dict[str, object], source: Path, root: Path) -> FabricSettings:
    """Read the fabric-wide settings, naming every one the file gets wrong at once.

    A config file is edited by hand, so one read reporting every missing and
    mistyped key beats three runs each reporting the next one.
    """
    design = _section(table, "design", source)
    pdk = _section(table, "pdk", source)
    fabric = _section(table, "fabric", source)
    problems: list[str] = []

    def text(section: dict[str, object], where: str, key: str) -> str:
        value = section.get(key)
        if not isinstance(value, str):
            problems.append(f"{where}.{key} is missing or is not a string")
            return ""
        return value

    def number(section: dict[str, object], where: str, key: str) -> float:
        value = section.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(f"{where}.{key} is missing or is not a number")
            return 0.0
        return float(value)

    settings = FabricSettings(
        clock_port=text(design, "design", "clock_port"),
        frequency_mhz=number(design, "design", "frequency_mhz"),
        pdk_name=text(pdk, "pdk", "name"),
        # A relative root is taken from the repository, where the `pdk` submodule sits.
        pdk_root=root / Path(text(pdk, "pdk", "root")).expanduser(),
        core_margin_micron=number(fabric, "fabric", "core_margin_micron"),
        stripe_pitch_micron=number(fabric, "fabric", "stripe_pitch_micron"),
    )
    if problems:
        raise ValueError(f"{source}: " + "; ".join(problems))
    # An uninitialised submodule is an empty directory, and upstream gitignores
    # the liberty that `make unzip` fetches, so a bare directory test passes both.
    stdcell = settings.pdk_root / "IP" / "STD_cell" / "ics55_LLSC_H7C_V1p10C100"
    if not any(stdcell.glob("*/liberty")):
        raise ValueError(
            f"{source}: pdk.root {settings.pdk_root} has no standard-cell liberty under "
            f"{stdcell}. Run `git submodule update --init pdk` then `make -C pdk unzip`."
        )
    return settings


def load_config(paths: Paths, tile_types: tuple[str, ...] = ()) -> Config:
    """Read the config layers for one variant into one validated `Config`.

    `tile_types` names the types this variant builds. A per-tile file for a type
    the tile library carries but this variant does not place, such as the other
    variant's east column, is skipped; one under a directory that is no tile type
    at all, or misspelled, is reported here rather than ignored for the length of
    a forty-minute build.
    """
    fabric_path = paths.root / "Fabric" / CONFIG_NAME
    if not fabric_path.exists():
        raise FileNotFoundError(
            f"{fabric_path} does not exist. It carries the clock, the PDK and the "
            "fabric-wide floorplan settings every build reads."
        )
    fabric_table = _read(fabric_path)
    defaults_path = paths.tiles / "include" / CONFIG_NAME
    defaults_table = _read(defaults_path)
    # A die belongs to one tile type, and the fabric and the shared defaults
    # cover every type at once, so neither can carry one.
    for table, path in ((fabric_table, fabric_path), (defaults_table, defaults_path)):
        if "die" in table:
            raise ValueError(
                f"{path}: [die] sizes one tile type and this file covers them all. "
                f"Put it in Tile/<type>/{CONFIG_NAME}."
            )
    tiles = {}
    dies = {}
    macros = {}
    strategies: dict[str, Synthesis] = {}
    repairs: dict[str, Repair] = {}
    for path in sorted(paths.tiles.glob(f"*/{CONFIG_NAME}")):
        tile_type = path.parent.name
        if tile_type == "include":
            continue
        if not (path.parent / f"{tile_type}.csv").exists():
            raise ValueError(
                f"{path} configures {tile_type}, but {path.parent} holds no "
                f"{tile_type}.csv, so it is not a tile type the library carries"
            )
        if tile_types and tile_type not in tile_types:
            continue
        table = _read(path)
        tiles[tile_type] = _params(table.get("params"), path)
        dies[tile_type] = _die(table.get("die"), path)
        macro = _macro(table.get("macro"), path)
        if macro is not None:
            macros[tile_type] = macro
        strategies[tile_type] = _synthesis(table.get("synthesis"), path)
        repair = _repair(table.get("repair"), path)
        if repair is not None:
            repairs[tile_type] = repair
    for tile_type, die in _variant_dies(paths.dies, tile_types).items():
        dies[tile_type] = _merge_die(dies.get(tile_type, TileDie()), die, tile_type, paths.dies)
    settings = _fabric(table=fabric_table, source=fabric_path, root=paths.root)
    # `flow.plan` places every pin and sizes every die against its own margin
    # constant, so a config that disagrees with it would move the pins without
    # moving the cores they have to reach.
    from flow.plan import CORE_MARGIN, DBU

    if round(settings.core_margin_micron * DBU) != CORE_MARGIN:
        raise ValueError(
            f"{fabric_path}: core_margin_micron {settings.core_margin_micron} is "
            f"{round(settings.core_margin_micron * DBU)} DBU, but flow.plan places pins "
            f"against a {CORE_MARGIN} DBU margin. Change both or neither."
        )
    return Config(
        fabric=settings,
        fabric_params=_params(fabric_table.get("params"), fabric_path),
        tile_defaults=_params(defaults_table.get("params"), defaults_path),
        tile_params=tiles,
        tile_die=dies,
        tile_macro=macros,
        synthesis_default=_synthesis(defaults_table.get("synthesis"), defaults_path),
        tile_synthesis=strategies,
        tile_repair=repairs,
    )
