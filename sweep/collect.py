"""Record what one anchor actually built, from the workspace the run left behind.

`harden --force` deletes the tile directory, so every number a point is judged
on is copied out here before the next point starts. The detailed router's
violation count per iteration is the discriminating one: it falls to zero on a
die that routes and bottoms out then climbs on one that does not, which a final
`drc_count` alone does not distinguish from a run that was still improving.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SWEEP = Path(__file__).resolve().parent
TILES = SWEEP.parent / "build" / "tiles"
RESULTS = SWEEP / "results.tsv"
COLUMNS = (
    "tile round strategy die_w die_h die_area core_usage dp_util cell_area "
    "dr_iters dr_min dr_final drc_count verdict"
).split()

ITERATION = re.compile(r"End Iteration (\d+)/(\d+)")
# A clean violation table prints `| Total | 0 | 0.00% |`, so the percentage
# cannot be pinned to 100.00% without dropping exactly the rows that matter.
TOTAL = re.compile(r"printTableList\] \|\s+Total \|\s+(\d+) \| \d+\.\d+% \|\s*$")
PLACEABLE = re.compile(r"0\.99 \* placeable-area limit \(([\d.e+-]+)\)")
STRATEGY = re.compile(r"\[INFO\]: STRATEGY = (\S+)")


def violations(log: Path) -> list[int]:
    """Return the violation total the router reported at the end of each DR pass.

    iEDA prints several `Total` tables per iteration and the violation one is the
    last before the iteration ends, so the tables are carried forward and read
    off when the iteration closes rather than matched by their own header.

    A die DreamPlace refuses outright never reaches the router and leaves no
    log, which is a recordable outcome rather than an error: the row still says
    which anchor was tried, and `steps.json` beside it says where it stopped.
    """
    if not log.exists():
        return []
    counts, pending = [], None
    for line in log.read_text(errors="replace").splitlines():
        total = TOTAL.search(line)
        if total:
            pending = int(total.group(1))
        if ITERATION.search(line) and "/9" in line and pending is not None:
            counts.append(pending)
    return counts


def placeable_area(log: Path) -> float | None:
    """Return the area DreamPlace will actually place into, in square microns.

    `core_usage` in the floorplan report is not the number that decides a run.
    DreamPlace measures against its placeable area, which drops whatever the
    blockages take, and at this tile's density that is about five percent less.
    The figure is only in the log, in the line where cell padding is cut back,
    and it is printed as `0.99 * placeable` in square DBU.

    `dp_util` built from this is raw cell area over placeable area, which is not
    what `flow.project.placed_density` returns: that is DreamPlace's own figure
    and counts the movable area after cell padding. The two agree only where the
    padding was cut to 0. Do not fold them together, since every row already in
    `results.tsv` carries this definition.
    """
    if not log.exists():
        return None
    found = PLACEABLE.search(log.read_text(errors="replace"))
    return None if found is None else float(found.group(1)) / 0.99 / 1e6


def strategy(log: Path) -> str:
    """Return the ABC strategy the netlist was built with, as Yosys logged it."""
    if not log.exists():
        return "-"
    found = STRATEGY.search(log.read_text(errors="replace"))
    return "-" if found is None else found.group(1)


def metric(tile: Path, step: str, name: str) -> float | None:
    path = tile / step / "analysis" / "qor_metrics.json"
    if not path.exists():
        return None
    entries = json.loads(path.read_text())["metrics"]
    return next((m["value"] for m in entries if m["id"] == name), None)


def main(tile_type: str, round_name: str) -> dict:
    """Record what one tile type's run built, keyed by the round that asked for it.

    Every tile type is swept against the same six free dimensions rather than
    one anchor, so the point is named by the round and read back per type.
    """
    tile = TILES / tile_type / "default"
    layout = json.loads(
        (tile / "postFloorplan_ecc" / "feature" / "postFloorplan.db.json").read_text()
    )["Design Layout"]
    steps = {
        s["name"]: s["state"]
        for s in json.loads((tile / "home" / "flow.json").read_text())["steps"]
    }
    counts = violations(tile / "route_ecc" / "log" / "route.log")
    drc = metric(tile, "drc_ecc", "drc_count")
    cell_area = layout["core_area"] * layout["core_usage"]
    placeable = placeable_area(tile / "place_dreamplace" / "log" / "place.log")
    # A tile with no logic to place skips the router entirely, which is a pass
    # rather than an empty trajectory to judge.
    routed = steps.get("route") == "Success"
    row = {
        "tile": tile_type,
        "round": round_name,
        "strategy": strategy(tile / "Synthesis_yosys" / "log" / "Synthesis.log"),
        "dp_util": "-" if placeable is None else round(cell_area / placeable, 4),
        "die_w": layout["die_bounding_width"],
        "die_h": layout["die_bounding_height"],
        "die_area": round(layout["die_area"], 1),
        "core_usage": round(layout["core_usage"], 4),
        "cell_area": round(cell_area, 1),
        "dr_iters": len(counts),
        "dr_min": min(counts) if counts else "-",
        "dr_final": counts[-1] if counts else "-",
        "drc_count": "-" if drc is None else int(drc),
        "verdict": "pass"
        if steps.get("Harden") == "Success"
        and drc == 0
        and (counts[-1:] == [0] or (routed and not counts))
        else "FAIL",
    }
    if not RESULTS.exists():
        RESULTS.write_text("\t".join(COLUMNS) + "\n")
    with RESULTS.open("a") as handle:
        handle.write("\t".join(str(row[c]) for c in COLUMNS) + "\n")

    keep = SWEEP / f"round_{round_name}" / tile_type
    keep.mkdir(parents=True, exist_ok=True)
    (keep / "point.json").write_text(json.dumps({**row, "dr_trend": counts}, indent=2))
    (keep / "steps.json").write_text(json.dumps(steps, indent=2))
    return row


if __name__ == "__main__":
    print("\t".join(f"{c}={main(sys.argv[1], sys.argv[2])[c]}" for c in COLUMNS))
