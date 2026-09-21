"""Vendor the FABulous tile library into `Tile/`, at a pinned upstream commit.

The tiles are copied rather than referenced. FABulous's `load_fabric` builds its
tile list by intersecting `fabric.csv` against the directory names under
`Tile/`, and `gen_tile` writes each generated `.v` and `_ConfigMem.csv` beside
the `.csv` it came from, so a tile has to be a real directory in this project
and not a path into a submodule that generation would then dirty.

One rewrite is applied while copying. Upstream a tile sits at
`tiles/<library>/<tile>/`, three levels under its repository root, so it reaches
a BEL as `../../../primitives/...`; here a tile sits at `Tile/<tile>/`, two
levels under this repository root, so the same BEL is `../../primitives/...`.
Supertile members are one level deeper on both sides and shift by the same one.
`../common/` needs no rewrite because `Tile/common/` sits at the depth
`tiles/<library>/common/` does.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPOSITORY = "https://github.com/FPGA-Research/fabulous-tiles.git"
COMMIT = "5809cdf23da8055ab7c2487d1b637a569cacb5bc"
LIBRARY = "classic"

TILES: tuple[str, ...] = (
    "LUT4x8_ha",
    "RegFile",
    "N_term_RegFile",
    "S_term_RegFile",
    "MACC",
    "N_term_MACC",
    "S_term_MACC",
    "N_IO",
    "S_IO",
    "E_IO",
    "W_IO",
    "NE_term",
    "NW_term",
    "SE_term",
    "SW_term",
    "E_IHP_SRAM",
)
"""The classic library trimmed to what this fabric places.

`E_IHP_SRAM` is vendored but not yet placed by `fabric.csv`. It is the only
block-RAM tile the library has, a two-row supertile carrying an
`IHP_SRAM_1024x32_1RW` BEL, and the ICS55 SRAM compiler produces the same shape
of macro: single-port synchronous with a write mask. Adapting it means a new
primitive around an ICS55 instance and a matching tile, and the macro has to fit
one supertile, 168 um tall less margins.

Dropped upstream tiles are dropped for a reason each: the `TT_IF` family targets
a Tiny Tapeout harness this fabric does not sit in, and the `W_IO_DDR`, `*_IO2`
and `*_IO4` variants are wider pin counts of edges this fabric already covers
with the plain `*_IO` tile. The `*_IO2` and `*_IO4` variants become relevant the
moment an edge has to carry a memory interface rather than single bits.

`sync` copies each primitive's `fabulous/` directory and nothing else, so the
upstream `yosys/` helpers do not come across. For `IHP_SRAM_1024x32_1RW` that
drops `memlib/IHP_SRAM_1024x32_1RW_lib.txt`, which is what lets Yosys infer an
RTL array into the macro rather than having it instantiated by hand. Bringing it
over is a change to `sync`, not a file to copy beside the others, or the next
sync deletes it.
"""

BEL_DEPTH = re.compile(r"(\.\./)(\.\./\.\./primitives/)")
"""One `../` of a BEL path's prefix, which the shallower `Tile/` layout drops."""

VENDORED_SUFFIXES = frozenset({".csv", ".list", ".v"})
"""What a vendored tile directory keeps.

Upstream's `config.yaml` is LibreLane's `FABulousTile` flow configured for
gf180mcu, sky130 and ihp-sg13g2, none of which this project builds on, and its
die sizes come from `flow.plan` against `eFPGA_geometry.csv` instead. The
per-tile `gds_config.yaml` this project writes replaces it.
"""


@dataclass(frozen=True)
class Vendored:
    """What one `sync` run replaced, for reporting and for testing the rewrite."""

    tiles: tuple[str, ...]
    primitives: tuple[str, ...]
    rewritten: tuple[Path, ...]


def _checkout(cache: Path) -> Path:
    """Clone the library at `COMMIT` into `cache`, reusing an existing checkout."""
    if (cache / ".git").is_dir():
        head = subprocess.run(
            ("git", "-C", str(cache), "rev-parse", "HEAD"),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if head == COMMIT:
            return cache
        shutil.rmtree(cache)

    cache.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(("git", "clone", REPOSITORY, str(cache)), check=True)
    subprocess.run(("git", "-C", str(cache), "checkout", COMMIT), check=True)
    return cache


def _copy_tile(source: Path, destination: Path) -> list[Path]:
    """Copy one tile's source files, rewriting BEL depth. Return the files changed."""
    rewritten: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.suffix not in VENDORED_SUFFIXES:
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = path.read_text(encoding="utf-8")
        shifted = BEL_DEPTH.sub(r"\2", text)
        target.write_text(shifted, encoding="utf-8")
        if shifted != text:
            rewritten.append(target)
    return rewritten


def _required_primitives(tile_root: Path) -> list[str]:
    """Read back the primitive names the vendored tiles name in their BEL lines."""
    wanted: set[str] = set()
    for csv in sorted(tile_root.rglob("*.csv")):
        for line in csv.read_text(encoding="utf-8").splitlines():
            if not line.startswith("BEL,"):
                continue
            path = Path(line.split(",")[1].strip())
            if "primitives" not in path.parts:
                raise ValueError(f"{csv}: BEL outside the library: {path}")
            wanted.add(path.parts[path.parts.index("primitives") + 1])
    return sorted(wanted)


def sync(project: Path, cache: Path) -> Vendored:
    """Replace `Tile/` and `primitives/` with the pinned library's classic tiles.

    `Tile/include` is this project's own ICS55 configuration and survives; every
    other tile directory is removed first, so a tile dropped from `TILES` cannot
    linger and be matched by a stale `fabric.csv` row.
    """
    checkout = _checkout(cache)
    library = checkout / "tiles" / LIBRARY
    missing = [tile for tile in TILES if not (library / tile).is_dir()]
    if missing:
        raise ValueError(f"not in the {LIBRARY} library at {COMMIT}: {missing}")

    tile_root = project / "Tile"
    for existing in sorted(tile_root.iterdir()):
        if existing.is_dir() and existing.name != "include":
            shutil.rmtree(existing)

    rewritten: list[Path] = []
    for tile in TILES:
        rewritten += _copy_tile(library / tile, tile_root / tile)
    rewritten += _copy_tile(library / "common", tile_root / "common")

    primitive_root = project / "primitives"
    if primitive_root.exists():
        shutil.rmtree(primitive_root)
    primitives = _required_primitives(tile_root)
    for primitive in primitives:
        shutil.copytree(
            checkout / "primitives" / primitive / "fabulous",
            primitive_root / primitive / "fabulous",
        )

    shutil.copyfile(checkout / "models_pack.v", project / "Fabric" / "models_pack.v")
    (tile_root / "UPSTREAM").write_text(
        f"{REPOSITORY}\n{COMMIT}\ntiles/{LIBRARY}\n", encoding="utf-8"
    )
    return Vendored(
        tiles=TILES, primitives=tuple(primitives), rewritten=tuple(rewritten)
    )
