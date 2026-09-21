"""Write the [die] table of each tile type that owns a free column or row.

Six tile types carry the fabric's six free dimensions, one each, because
`flow.plan` binds a width to every column a type occupies and a height to every
row. The terminator types sharing those columns and rows take no [die] of their
own, since two types claiming one column with different numbers is refused.
Which type binds a dimension is a separate question and changes between rounds:
column 0 is carried by W_IO here and bound by SW_term beside it.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
OWNER = {  # tile type -> the dimension it carries
    "W_IO": "width_micron",
    "RegFile": "width_micron",
    "MACC": "width_micron",
    "E_IO": "width_micron",
    "N_IO": "height_micron",
    "S_IO": "height_micron",
}
NOTE = {
    "width_micron": "The width of this tile's fabric column, which every type in "
    "it is built to.",
    "height_micron": "The height of this tile's fabric row, which every type in "
    "it is built to.",
}


def write(values: dict[str, float]) -> None:
    """Replace each type's [die] table and leave everything else in the file.

    The die and the ABC strategy are chosen by different sweeps and written by
    different scripts, so overwriting the file would silently drop whichever ran
    first and harden the tile on a netlist its column was not sized for.
    """
    for tile, value in values.items():
        key = OWNER[tile]
        path = PROJECT / "Tile" / tile / "ecc_config.toml"
        kept = (
            [block for block in path.read_text().split("\n\n") if "[die]" not in block]
            if path.exists()
            else []
        )
        block = f"# {NOTE[key]}\n[die]\n{key} = {value}\n"
        path.write_text("\n\n".join([*(b for b in kept if b.strip()), block]))


if __name__ == "__main__":
    write(dict(zip(OWNER, (float(v) for v in sys.argv[1:]), strict=True)))
