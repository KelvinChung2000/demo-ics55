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
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

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
    "route.bottom_layer": str,
    "route.top_layer": str,
    "sta.max_paths": int,
}

# Registry entries this project sets from `[design]` and `[fabric]` instead, so
# that one value cannot be given twice in one file. `core_margin` decides where
# two abutted cores meet and `frequency_mhz` constrains the clock every tile
# shares, so both are fabric-wide.
RESERVED_PARAMS = frozenset({"design.frequency_mhz", "floorplan.core_margin"})


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
                    f"{source}: {key} is set in [design] or [fabric] for the whole "
                    "fabric and cannot be given as a parameter"
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


def _section(table: dict[str, object], name: str, source: Path) -> dict[str, object]:
    value = table.get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"{source}: [{name}] is not a table")
    return value


def _fabric(table: dict[str, object], source: Path) -> FabricSettings:
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
        pdk_root=Path(text(pdk, "pdk", "root")).expanduser(),
        core_margin_micron=number(fabric, "fabric", "core_margin_micron"),
        stripe_pitch_micron=number(fabric, "fabric", "stripe_pitch_micron"),
    )
    if problems:
        raise ValueError(f"{source}: " + "; ".join(problems))
    if not settings.pdk_root.is_dir():
        raise ValueError(f"{source}: pdk.root {settings.pdk_root} is not a directory")
    return settings


def load_config(project: Path, tile_types: tuple[str, ...] = ()) -> Config:
    """Read the three config layers under `project` into one validated `Config`.

    `tile_types` names the types a per-tile file is allowed to exist for, so a
    file under a directory that is not a tile type, or one misspelled, is
    reported here rather than ignored for the length of a forty-minute build.
    """
    fabric_path = project / "Fabric" / CONFIG_NAME
    if not fabric_path.exists():
        raise FileNotFoundError(
            f"{fabric_path} does not exist. It carries the clock, the PDK and the "
            "fabric-wide floorplan settings every build reads."
        )
    fabric_table = _read(fabric_path)
    defaults_path = project / "Tile" / "include" / CONFIG_NAME
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
    for path in sorted((project / "Tile").glob(f"*/{CONFIG_NAME}")):
        tile_type = path.parent.name
        if tile_type == "include":
            continue
        if tile_types and tile_type not in tile_types:
            raise ValueError(
                f"{path} configures {tile_type}, which is not a tile type this fabric "
                f"uses: {sorted(tile_types)}"
            )
        table = _read(path)
        tiles[tile_type] = _params(table.get("params"), path)
        dies[tile_type] = _die(table.get("die"), path)
    settings = _fabric(fabric_table, fabric_path)
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
    )
