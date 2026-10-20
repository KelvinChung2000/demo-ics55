"""OpenROAD design-rule and hold repair on a legalised DEF, before ECC routes it.

ECC runs no sizer after placement, so nothing else buffers or upsizes a driver
against its placed wire. The tile run repairs slew and capacitance only; the
top run, `repair_top.tcl`, also sizes the frame strobes and repairs hold.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

from flow import defedit

TILE_TCL = Path(__file__).with_name("repair_tile.tcl")
TOP_TCL = Path(__file__).with_name("repair_top.tcl")
SPECIALNETS_RE = re.compile(r"^SPECIALNETS \d+ ;$.*?^END SPECIALNETS$", re.M | re.S)
PINS_RE = re.compile(r"^PINS \d+ ;$.*?^END PINS$", re.M | re.S)
VIOLATED_RE = re.compile(r"\(VIOLATED\)")


def run(
    script: Path,
    def_path: Path,
    *,
    env: Mapping[str, str],
    reports: Path,
    keep_pins: bool,
) -> str:
    """Run `script` on `def_path` and write its result back in place.

    OpenROAD writes every power connection out explicitly, which drops the
    `( * vdd_stripe_generate )` term the tile stripes need, so the input's
    SPECIALNETS block is put back whole: the PDN is not touched here, and its
    `( * VDD )` reaches the cells the repair adds. With `keep_pins` the input's
    PINS block is put back too: OpenROAD rewrites each pin as a `+ PORT`, which
    iEDA then draws into the PINS cell that flow.paint needs empty. The script
    gets DEF_IN and
    DEF_OUT on top of `env` and writes drv_before.txt and drv_after.txt into
    `reports`. Raises `CalledProcessError` if OpenROAD fails, check_placement
    included. Returns the violator counts before and after.
    """
    reports.mkdir(parents=True, exist_ok=True)
    original = defedit.read_def(def_path)
    with tempfile.TemporaryDirectory() as scratch:
        plain = Path(scratch) / "legalised.def"
        repaired = Path(scratch) / "repaired.def"
        plain.write_text(original)
        with (reports / "repair.log").open("w") as log:
            subprocess.run(
                ["openroad", "-exit", "-no_init", str(script)],
                cwd=reports,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
                env={
                    **os.environ,
                    **env,
                    "DEF_IN": str(plain),
                    "DEF_OUT": str(repaired),
                },
            )
        text = repaired.read_text()
    power = SPECIALNETS_RE.search(original)
    rewritten = SPECIALNETS_RE.search(text)
    if power is None or rewritten is None:
        raise ValueError(f"{def_path} or its repair has no SPECIALNETS section")
    text = text[: rewritten.start()] + power.group(0) + text[rewritten.end() :]
    if keep_pins:
        pins = PINS_RE.search(original)
        rewritten = PINS_RE.search(text)
        if pins is None or rewritten is None:
            raise ValueError(f"{def_path} or its repair has no PINS section")
        if pins.group(0).splitlines()[0] != rewritten.group(0).splitlines()[0]:
            raise ValueError(f"the repair of {def_path} changed its pin count")
        text = text[: rewritten.start()] + pins.group(0) + text[rewritten.end() :]
    defedit.write_def(def_path, text, gzipped=def_path.suffix == ".gz")
    before, after = (
        len(VIOLATED_RE.findall((reports / name).read_text()))
        for name in ("drv_before.txt", "drv_after.txt")
    )
    return f"DRV {before} -> {after} (placement estimate)"


def tile(
    def_path: Path, *, pdk_root: Path, margin_percent: float, reports: Path
) -> str:
    """Repair slew and capacitance on a legalised tile, `margin_percent` inside the
    liberty limits to cover the gap between the placement estimate and the route."""
    return run(
        TILE_TCL,
        def_path,
        env={"PDK": str(pdk_root), "MARGIN": str(margin_percent)},
        reports=reports,
        keep_pins=True,
    )
