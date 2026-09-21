"""Run one point of the die sweep: set the six free dimensions, harden, collect.

A point is six numbers, not one anchor, because the LUT fixes six of the ten
columns and fourteen of the sixteen rows and the rest are independent. Each
round writes them, replans, hardens every tile type affected and records one row
per type in `sweep/results.tsv`, so a failure is attributed to the one
dimension that carries it rather than to the fabric.

`harden --force` deletes the workspace it is about to rebuild, so a round
collects before the next one starts, and rewrites each `[die]` table with what
the run measured. That last step is not cosmetic: `setdie` writes a bare number
at the top of a round, so a round left unfinalised strips the evidence from
every table a previous one wrote.

`ANCHOR` is the LUT width the user fixed, and it no longer sets any edge. Every
one of the fifteen types now carries a `[die]` table, so `flow.plan` overrides
every column and row it scaled and the anchor only has to be a number `cli.plan`
accepts. It is kept here because `cli.plan` still requires one, reading the
compiled LUT when the option is absent.

`setdie` and `finalise` each know six of the fifteen files, and `finalise` is the
more dangerous of the two: it rewrites those six `[die]` tables from `results.tsv`
carrying only the one edge it tracks, so `W_IO` would lose its frozen
`height_micron` with no error, since a missing claim is not a disagreement and
`_claim` stays quiet. The freeze decays without failing.

`setdie` knows six of the fifteen files. A round run at a dimension the frozen
tables do not already hold rewrites those six and leaves the other nine at the
old size, which `flow.plan._claim` then refuses as a column carrying two widths.
Widen the map before sweeping again.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect  # noqa: E402
import finalise  # noqa: E402
import setdie  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1]
PYTHON = "/nix/store/lzfww5sff83ml4izdnzck7r0icjw8n22-FABulous-env/bin/python3"
ANCHOR = "82.5"


def flow(*arguments: str) -> None:
    subprocess.run(
        [PYTHON, "-m", "flow.cli", *arguments], cwd=PROJECT, check=True
    )


def main(name: str, dimensions: list[float], tiles: list[str], jobs: int) -> None:
    setdie.write(dict(zip(setdie.OWNER, dimensions, strict=True)))
    flow("plan", "--anchor-micron", ANCHOR)
    flow("check")
    harden = [PYTHON, "-m", "flow.cli", "harden", "--force", "--jobs", str(jobs)]
    for tile in tiles:
        harden += ["--tile", tile]
    # A failing tile is the point of the round, so its exit code is not fatal.
    subprocess.run(harden, cwd=PROJECT, check=False)
    print(f"\n=== round {name} ===")
    for tile in tiles:
        try:
            row = collect.main(tile, name)
        except (FileNotFoundError, KeyError) as missing:
            print(f"{tile:16s} no workspace to read: {missing}")
            continue
        print(
            f"{tile:16s} {row['die_w']:6.1f} x {row['die_h']:6.1f}  "
            f"core {row['core_usage']:.3f}  dp {row['dp_util']}  "
            f"dr {row['dr_iters']}/{row['dr_final']}  drc {row['drc_count']}  "
            f"{row['verdict']}"
        )
    finalise.write()


if __name__ == "__main__":
    main(
        name=sys.argv[1],
        dimensions=[float(v) for v in sys.argv[2:8]],
        jobs=int(sys.argv[8]),
        tiles=sys.argv[9:],
    )
