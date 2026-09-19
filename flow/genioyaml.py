"""Write one `io_pin_order.yaml` per tile type, using FABulous's own generator.

Run by a FABulous interpreter rather than by the flow's, so it imports nothing
from `flow`. `generate_IO_pin_order_config` is not on the FABulous revision
this project pins for `run_FABulous_fabric`; it lives on the branch
`flow.cli`'s `--fabulous-python` points at, and the files it writes are
vendored beside each tile's CSV.

A supertile is hardened as one macro, so the two sub-tiles `MACC` is built from
get no file of their own and the supertile's covers both under its `X0Y0` and
`X0Y1` keys.
"""

import sys
from pathlib import Path

from fabulous.fabric_generator.code_generator.code_generator_Verilog import (
    VerilogCodeGenerator,
)
from fabulous.fabulous_api import FABulous_API


def main(project: Path) -> int:
    api = FABulous_API(VerilogCodeGenerator())
    api.loadFabric(project / "fabric.csv")

    supertiles = getattr(api.fabric, "superTileDic", {})
    inside = {
        sub.name
        for super_tile in supertiles.values()
        for row in super_tile.tileMap
        for sub in row
        if sub is not None
    }
    elements = [
        tile for name, tile in api.fabric.tileDic.items() if name not in inside
    ] + list(supertiles.values())

    for element in elements:
        directory = project / "Tile" / element.name
        if not directory.is_dir():
            raise FileNotFoundError(
                f"{directory} does not exist, so {element.name} has nowhere to "
                "keep its pin order; re-vendor the tile library first"
            )
        api.gen_io_pin_order_config(element, directory / "io_pin_order.yaml")
    print(f"{len(elements)} written: {sorted(e.name for e in elements)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
