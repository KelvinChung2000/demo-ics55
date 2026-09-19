# Building this fabric on ICS55 with ECC

`flow` hardens each of the fifteen tile types this fabric uses, abuts them into
one layout and proves that every wire `Fabric/eFPGA.v` declares across a seam
actually conducts through it. `FINDINGS.md`, one directory up, records why each
step exists and what in the toolchain forced it; this file says how to run them.

The whole build is `task`, which runs the six stages below in order and stops at
the first that fails. Hardening fifteen tile types takes about forty minutes at
three concurrent jobs, so start it under `nohup` and read `build/logs`.

    task plan     # size every tile, place every pin
    task check    # test the plan's wiring properties, no EDA tool involved
    task harden   # fifteen ECC runs, synthesis to macro
    task paint    # draw the pins and boundary power into each GDS
    task stitch   # abut the fabric and check every seam
    task top      # the fabric-level ECC project, floorplan only

`task --list` gives the rest, including `view-fabric` and `view-tile` for the
ECOS layout viewer, `image` for a rendered PNG, `drc` for every tile's signoff
count and `flat` for the whole eFPGA hardened as one design rather than abutted.

## Where the tiles come from

`Tile/` is vendored from the classic library of
[fabulous-tiles](https://github.com/FPGA-Research/fabulous-tiles), pinned to the
commit `Tile/UPSTREAM` names. The tiles are copied rather than referenced
through a submodule because FABulous builds its tile list from the directory
names under `Tile/` and writes each generated `.v` beside the `.csv` it came
from. `task sync-tiles` re-copies the `.csv`, `.list` and `.v` files, which
discards every generated `.v` and every `io_pin_order.yaml` with them, so it
has to be followed by a FABulous `run_FABulous_fabric` and by
`task gen-io-order` before anything downstream will build. That second command
runs a FABulous branch this project pins for nothing else, because
`generate_IO_pin_order_config` is not on the revision `Tile/UPSTREAM` names;
`--fabulous-python` selects it. Upstream's per-tile
`config.yaml` does not come across at all: it configures LibreLane for PDKs this
project does not build on, and `Tile/include/gds_config.yaml` replaces it.

The classic library is trimmed to what this fabric places. `E_IHP_SRAM` and
`E_IHP_BRAM` wrap IHP macros ICS55 has no equivalent of, so the East column is
`E_IO` and this fabric has no block RAM; the `TT_IF` family targets a Tiny
Tapeout harness this fabric does not sit in. `fabric.csv` sets `DisableUserCLK`,
so a tile takes its clock off the global-buffer network the library carries and
`Fabric/eFPGA.v` has no top-level `UserCLK` port.

## What each stage leaves behind

`plan` writes `build/fabric_plan.json`, which every later stage reads and nothing
later modifies: one die size per tile type, one offset per scalar pin, and the
seam list. The order of pins along an edge is not this flow's to choose: it
comes from each tile's `io_pin_order.yaml`, which FABulous writes and
`task gen-io-order` regenerates. Facing sides list the same buses at the same
positions, so an order chosen per tile still meets across a seam, and `plan`
only decides which tracks that order lands on. Its one free parameter is `ANCHOR`, the width of a `LUT4x8_ha` in
microns, from which every other tile is scaled using `eFPGA_geometry.csv`'s
proportions. The 110 that routes and the 90 that oscillates without converging
were both measured on the old `LUT4AB`, so neither bound has been re-established
for the library's LUT.

`harden` leaves one ECC workspace per tile type under `build/tiles`, each with
an abstract LEF, an extracted timing model and a GDS. Between `macroPlacement`
and `postFloorplan` it writes the plan's offsets into the workspace's
`config/io_location.txt` and puts ECC's IO placer in `file` mode, so iEDA places
each pin itself rather than cutting the pin list into four index-quarters as its
automatic mode does. `paint` writes `build/painted`, `stitch` writes
`build/eFPGA.gds`, and `top` writes a fabric-level project under `build/fabric`.

## Failing loudly

A stage refuses to run on stale inputs rather than producing a plausible wrong
answer. `check` rejects a plan whose links do not meet at one coordinate.
`harden` rejects a tile whose die does not match the plan, and reports any pin
that moved between `postFloorplan` and the filler DEF. ECC's placer rejects the
whole placement file on the first pin that is off-track or outside the core, and
`check` tests both rules on the plan so that failure arrives in a second rather
than forty minutes in. `paint` rejects a pin that
does not overlap its own net's routing. `stitch` rejects a seam carrying the
wrong number of crossings, or one joining two pins that are not the ends of a
link `eFPGA.v` declares.

One flag exists only to attribute a failure and should be left alone otherwise.
`harden --no-extend-power` leaves the PDN inside the core, so an abutted fabric
has no power across its seams and a routing failure can be blamed on the wide
metal along the die edges or on something else.
