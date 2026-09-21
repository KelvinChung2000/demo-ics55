"""Write each free dimension into its tile's `[die]` table with what measured it.

`setdie` writes a bare number during a sweep, because a round has no result yet.
This runs once the six have settled and replaces each block with the evidence:
the die that passed, the detailed-routing trajectory it passed on, the placeable
utilisation it reached and which tile type actually bound the dimension, which is
not always the type carrying the table. `results.tsv` lives under `build/`, which
`task clean` deletes, so the comment is the record that survives.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from setdie import OWNER, PROJECT  # noqa: E402

SWEEP = Path(__file__).resolve().parent
# Which type's run justifies each dimension, where it is not the one carrying it.
BINDER = {"W_IO": "SW_term"}


def rows() -> dict[str, dict[str, str]]:
    """Return each type's most recent run, whichever round last built it.

    A round rebuilds only the types whose die it changed, so the tiles carrying
    the final geometry are spread across rounds: RegFile and E_IO passed in r1
    and were never re-run, because nothing after r1 moved them.
    """
    found: dict[str, dict[str, str]] = {}
    for row in csv.DictReader((SWEEP / "results.tsv").open(), delimiter="\t"):
        found[row["tile"]] = row
    return found


def trajectory(row: dict[str, str]) -> str:
    import json

    point = SWEEP / f"round_{row['round']}" / row["tile"] / "point.json"
    trend = json.loads(point.read_text())["dr_trend"]
    return " -> ".join(str(v) for v in trend) if trend else "no routing needed"


WHAT = {
    "width_micron": "width of this tile's fabric column",
    "height_micron": "height of this tile's fabric row",
}


def write() -> None:
    measured = rows()
    for tile, key in OWNER.items():
        own = measured[tile]
        binder = measured[BINDER.get(tile, tile)]
        value = float(own["die_w"] if key == "width_micron" else own["die_h"])
        note = (
            f"# The {WHAT[key]}, which every type in it is built to.\n"
            f"# Bound by {binder['tile']}: at {binder['die_w']} x {binder['die_h']} um it "
            f"fills {binder['core_usage']} of its core and\n"
            f"# {binder['dp_util']} of the area DreamPlace places into, and routes "
            f"{trajectory(binder)}\n"
            f"# with {binder['drc_count']} DRC. Round {binder['round']}, 2026-09-21.\n"
        )
        path = PROJECT / "Tile" / tile / "ecc_config.toml"
        kept = [block for block in path.read_text().split("\n\n") if "[die]" not in block]
        table = f"{note}[die]\n{key} = {value}\n"
        path.write_text("\n\n".join([*(b for b in kept if b.strip()), table]))
        print(f"{tile:16s} {key} = {value}  bound by {binder['tile']}")


if __name__ == "__main__":
    write()
