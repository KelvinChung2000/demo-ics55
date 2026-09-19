"""Hand the fabric's pin plan to ECC's own IO placer.

`ifp::IOPlacer` places every top-level pin from a file when `io_placer.mode` is
`file`, on the edge and offset each line names, and gives the shape a depth it
derives from the access layer's track pitch so that it runs from the die
boundary inward. Writing that file replaces the floorplan-DEF rewrite this flow
used before ECC grew the mode: a pin ECC places is `+ FIXED` in its own
database and stays where it was put, while one written into the DEF behind
iEDA's back was only there until a step reloaded the binary database.

Three rules come from the parser rather than from this fabric, and `flow.plan`
already places pins under all three. `offset_micron` is a die coordinate rather
than an offset from the core; it must sit exactly on a track of the pin's own
layer; and the whole pin shape must lie inside the core, which is the die inset
by the floorplan margin. The parser also demands every pin exactly once, so a
plan that has lost a bit fails here rather than at routing.

The edge a pin goes on is named from the tile's point of view elsewhere in this
flow and from the die's here: `flow.fabric`'s `W` is ECC's `left`.
"""

from __future__ import annotations

import json
from pathlib import Path

from flow.plan import DBU, PinPlacement, Side

LOCATION_FILE = "io_location.txt"
EDGE: dict[Side, str] = {"N": "top", "S": "bottom", "E": "right", "W": "left"}


def _micron(value: int) -> str:
    """Render DBU as microns without a trailing zero the parser would keep reading."""
    return f"{value / DBU:.4f}".rstrip("0").rstrip(".")


def location_file(pins: list[PinPlacement]) -> str:
    """Render one tile's pin plan as an `io_location.txt`."""
    lines = ["# pin_name edge offset_micron layer"]
    for pin in sorted(pins, key=lambda pin: (pin.side, pin.offset)):
        lines.append(f"{pin.name} {EDGE[pin.side]} {_micron(pin.offset)} {pin.layer}")
    return "\n".join(lines) + "\n"


def install(workspace: Path, pins: list[PinPlacement]) -> str:
    """Write the placement file and point the floorplan config at it.

    `_refresh_floorplan_config` rewrites the floorplan config before every step,
    but it only `setdefault`s the keys it owns and never touches `io_placer`, so
    the mode set here survives the refresh the same way the die size does.
    """
    config = workspace / "config" / "floorplan_ecc.json"
    if not config.exists():
        raise FileNotFoundError(
            f"{config} does not exist. Run through macroPlacement first so ECC creates it."
        )
    (workspace / "config" / LOCATION_FILE).write_text(location_file(pins))

    data = json.loads(config.read_text())
    placer = data["io_placer"]
    layers = {pin.layer for pin in pins}
    missing = layers - set(placer["io_layer_list"])
    if missing:
        raise ValueError(
            f"the plan places pins on {sorted(missing)}, which "
            f"io_layer_list does not carry: {placer['io_layer_list']}"
        )
    placer["mode"] = "file"
    placer["file_path"] = LOCATION_FILE
    config.write_text(json.dumps(data, indent=4))
    return f"{len(pins)} pins written to config/{LOCATION_FILE}"
