"""Where one fabric variant's inputs and build outputs live.

Both variants build from one tile library, so `Tile/`, `primitives/`,
`user_design/` and the fabric-wide `Fabric/ecc_config.toml` sit at the
repository root. What a grid decides lives under `fabrics/<variant>/`: its
`fabric.csv`, the `Fabric/eFPGA.v` and `eFPGA_geometry.csv` FABulous generated
from it, and the die edges that depend on which tile the grid puts in a shared
column. Each variant directory is a FABulous project in its own right, with
`Tile/` and `primitives/` linked back to the root, and builds into
`build/<variant>/` so the two never share a workspace.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Variant(str, Enum):
    """The fabrics this repository builds from one tile library."""

    BRAM = "bram"
    NOBRAM = "nobram"


ENVIRONMENT = "FLOW_VARIANT"


@dataclass(frozen=True)
class Paths:
    variant: Variant

    @classmethod
    def from_environment(cls) -> Paths:
        """The variant `FLOW_VARIANT` names, for scripts that run outside `flow.cli`."""
        if ENVIRONMENT not in os.environ:
            raise RuntimeError(
                f"{ENVIRONMENT} is not set. Set it to one of "
                f"{[v.value for v in Variant]} to pick the build/<variant> to read."
            )
        return cls(Variant(os.environ[ENVIRONMENT]))

    @property
    def root(self) -> Path:
        return ROOT

    @property
    def tiles(self) -> Path:
        return ROOT / "Tile"

    @property
    def fabric(self) -> Path:
        """The variant's FABulous project directory."""
        return ROOT / "fabrics" / self.variant.value

    @property
    def fabric_verilog(self) -> Path:
        return self.fabric / "Fabric" / "eFPGA.v"

    @property
    def geometry(self) -> Path:
        return self.fabric / "eFPGA_geometry.csv"

    @property
    def dies(self) -> Path:
        """Die edges this variant fixes for tile types it shares with the other."""
        return self.fabric / "dies.toml"

    @property
    def build(self) -> Path:
        return ROOT / "build" / self.variant.value

    @property
    def plan(self) -> Path:
        return self.build / "fabric_plan.json"
