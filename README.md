# Building this fabric on ICS55 with ECC

`flow` hardens each of the thirteen tile types this fabric uses, abuts them into
one layout and proves that every wire `Fabric/eFPGA.v` declares across a seam
actually conducts through it. `FINDINGS.md`, one directory up, records why each
step exists and what in the toolchain forced it; this file says how to run them.

The whole build is `task`, which runs the six stages below in order and stops at
the first that fails. Hardening thirteen tile types takes about forty minutes at
three concurrent jobs, so start it under `nohup` and read `build/logs`.

    task plan     # size every tile, place every pin
    task check    # test the plan's wiring properties, no EDA tool involved
    task harden   # thirteen ECC runs, synthesis to macro
    task paint    # draw the pins and boundary power into each GDS
    task stitch   # abut the fabric and check every seam
    task top      # the fabric-level ECC project, floorplan only

`task --list` gives the rest, including `view-fabric` and `view-tile` for the
ECOS layout viewer, `image` for a rendered PNG, `drc` for every tile's signoff
count and `flat` for the whole eFPGA hardened as one design rather than abutted.

## What each stage leaves behind

`plan` writes `build/fabric_plan.json`, which every later stage reads and nothing
later modifies: one die size per tile type, one offset per scalar pin, and the
seam list. Its one free parameter is `ANCHOR`, the width of a `LUT4AB` in
microns, from which every other tile is scaled using `eFPGA_geometry.csv`'s
proportions. At 110 the tiles route and every type signs off at zero DRC
violations; at 90 detailed routing oscillates and never converges.

`harden` leaves one ECC workspace per tile type under `build/tiles`, each with
an abstract LEF, an extracted timing model and a GDS. `paint` writes
`build/painted`, `stitch` writes `build/eFPGA.gds`, and `top` writes a
fabric-level project under `build/fabric`.

## Failing loudly

A stage refuses to run on stale inputs rather than producing a plausible wrong
answer. `check` rejects a plan whose links do not meet at one coordinate.
`harden` rejects a tile whose die does not match the plan, and reports any pin
that moved between the floorplan and the filler DEF. `paint` rejects a pin that
does not overlap its own net's routing. `stitch` rejects a seam carrying the
wrong number of crossings, or one joining two pins that are not the ends of a
link `eFPGA.v` declares.

Two flags exist only to attribute a failure and should be left alone otherwise.
`harden --no-extend-power` leaves the PDN inside the core, so an abutted fabric
has no power across its seams, and `harden --status PLACED` writes the pins in
the status iEDA silently overwrites.
