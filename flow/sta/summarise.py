"""Summarise the full-chip STA run.sh leaves in <build>/fullsta: hold per clock and
DRV violators per check and tile type, one table each per corner."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import typer

CORNERS = (
    "ff_m40_RCbest",
    "ff_m40_Cbest",
    "ff_125_Cbest",
    "ff1p08_125_RCbest",
    "ss_125_Cworst",
    "ss_m40_Cworst",
)
# A `-format end` row ends in `<slack> (MET)`, a full path in `<slack>   slack (MET)`.
SLACK_RE = re.compile(r"\s(-?\d+\.\d+)(?:\s+slack)? \((?:MET|VIOLATED)\)")
TILE_RE = re.compile(r"Tile_X\d+Y\d+_(\w+?)/")
# A pin on the frame-strobe path: the top decoder outputs and, in a tile, the
# strobe buffers and the ConfigMem latch gates they drive.
STROBE_RE = re.compile(r"^frame_strobe_|/strobe_|ConfigMem\..*/G$")
CHECKS = {"max slew": "slew", "max capacitance": "cap", "max fanout": "fanout"}


def worst_after(log: str, header: str) -> float:
    """The first slack reported after `header`; a missing section is an error."""
    start = log.find(header)
    if start < 0:
        raise ValueError(f"no section {header!r} in the STA log")
    match = SLACK_RE.search(log, start)
    if match is None:
        raise ValueError(f"no slack after {header!r}")
    return float(match.group(1))


@dataclass(frozen=True)
class Violation:
    check: str
    owner: str
    slack: float


def violations(report: Path) -> list[Violation]:
    """Violators of a report_check_types file, owned by tile type or `top`, with
    the frame-strobe path split out."""
    check: str | None = None
    found: list[Violation] = []
    for line in report.read_text().splitlines():
        text = line.strip()
        if text in CHECKS:
            check = CHECKS[text]
            continue
        if "(VIOLATED)" not in text:
            continue
        if check is None:
            raise ValueError(f"{report}: violator before any check header")
        pin, *_, slack, _ = text.split()
        tile = TILE_RE.match(pin)
        owner = tile.group(1) if tile else "top"
        if STROBE_RE.search(pin):
            owner += " strobe"
        found.append(Violation(check=check, owner=owner, slack=float(slack)))
    return found


def main(fullsta: Path) -> None:
    typer.echo(
        "corner | CLK setup | CLK hold | uclk LUT | uclk IO | uclk MACC | uclk violators"
        " | USER_RESET setup | USER_RESET hold"
    )
    for tag in CORNERS:
        log = (fullsta / f"{tag}.log").read_text()
        held = (fullsta / f"hold_violators_{tag}.txt").read_text().count("VIOLATED")
        slacks = [
            worst_after(log, "==== CLK register-to-register"),
            worst_after(log, "min_delay/hold group CLK"),
            worst_after(log, "worst hold into LUT"),
            worst_after(log, "worst hold into IO"),
            worst_after(log, "worst hold into MACC"),
        ]
        reset = [
            worst_after(log, "==== USER_RESET setup into GSR"),
            worst_after(log, "==== USER_RESET hold into GSR"),
        ]
        typer.echo(
            " | ".join(
                [tag, *(f"{s:.3f}" for s in slacks), str(held), *(f"{s:.3f}" for s in reset)]
            )
        )
    for tag in CORNERS:
        found = violations(fullsta / f"drv_{tag}.txt")
        counts = Counter((v.check, v.owner) for v in found)
        typer.echo(f"\n{tag}: {len(found)} DRV violators")
        for check, owner in sorted(counts):
            worst = min(v.slack for v in found if (v.check, v.owner) == (check, owner))
            typer.echo(
                f"  {check:7} {owner:20} {counts[check, owner]:6}  worst {worst:.3f}"
            )


if __name__ == "__main__":
    typer.run(main)
