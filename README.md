# Building this fabric on ICS55 with ECC

`flow` hardens each of the fifteen tile types this fabric uses, abuts them into
one layout and proves that every wire `Fabric/eFPGA.v` declares across a seam
actually conducts through it. `FINDINGS.md`, one directory up, records why each
step exists and what in the toolchain forced it; this file says how to run them.

The whole build is `task efpga`, aliased to `task build` and to bare `task`,
which runs the five stages below in order and stops at the first that fails.
Hardening fifteen tile types takes about forty minutes at three concurrent jobs,
so start it under `nohup` and read `build/logs`.

    task plan      # size every tile, place every pin
    task check     # test the plan's wiring properties, no EDA tool involved
    task harden    # fifteen ECC runs, synthesis to macro
    task assemble  # paint every tile and abut them into one fabric layout

`assemble` takes `STITCHER`. At `klayout`, the default, `stitch` paints every
hardened tile and abuts them and proves every seam, then `top` writes the
fabric-level ECC project and floorplans it. Painting is not a stage of its own:
a painted GDS carries the pins and boundary power one plan placed, so it is drawn
against the plan being abutted in the same command, and a tile hardened to an
older die is refused there rather than surfacing later as a seam that does not
conduct. At `ecc`, the stitch is skipped and that same parent
is carried on to a layout: placement, CTS and legalisation are seeded from the
floorplan the way a logic-free tile's are, and the flow runs from routing to
filler, which is the step that writes the GDS. At `both` each runs, which is the
only way to get ECC's layout and the seam proof from one command.

The two assemblies are not interchangeable. Only the klayout one proves that a
seam conducts and joins the two ends of a link `eFPGA.v` declares; only the ECC
one leaves a layout the rest of the ECC flow can read. `task efpga STITCHER=both`
is the combination to run when the answer has to be both.

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
discards every generated `.v` with them, so it has to be followed by a FABulous
`run_FABulous_fabric` before anything downstream will build. Upstream's per-tile
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
seam list. Its one free parameter is `ANCHOR`, the width of a `LUT4x8_ha` in
microns, from which every other tile is scaled using `eFPGA_geometry.csv`'s
proportions. The 110 that routes and the 90 that oscillates without converging
were both measured on the old `LUT4AB`, so neither bound has been re-established
for the library's LUT.

`harden` leaves one ECC workspace per tile type under `build/tiles`, each with
an abstract LEF, an extracted timing model and a GDS. `stitch` writes
`build/painted` and then `build/eFPGA.gds` from it, and `top` writes a
fabric-level project under `build/fabric`.

`synth` belongs to the flat control rather than to the abutted flow and leaves a
synthesis-only workspace at `build/tiles/<type>_nl`, beside the hardened tile but
never sharing a directory with it, so rebuilding the control cannot discard a
forty-minute run. `task flat` runs it first, then composes those fifteen gate
netlists under a bit-blasted parent and hardens the whole eFPGA under
`build/flat`. The duplicate synthesis is what buys the separation.

## Where the ECC settings live

Every project this flow writes, the fifteen tile runs, the fabric-level run and
the flat control, renders its `ecc.toml` from three files through
`flow.project.write_ecc_toml`, so no setting can drift between them.

    Fabric/ecc_config.toml         clock, PDK, core margin, stripe pitch
    Tile/include/ecc_config.toml   the ECC parameters every tile is hardened with
    Tile/<type>/ecc_config.toml    optional, replaces entries for one tile type

`flow.config` refuses at load any key that is not one `ecc param list` prints,
any value of the wrong type, and a per-tile file under a directory that is not a
tile type, so a misspelling is reported in a second rather than forty minutes in.
It also refuses a tile setting `core_margin` or `frequency_mhz`, which
`Fabric/ecc_config.toml` owns for the whole fabric: the stripe pitch has to
divide every row height and the margin decides where two abutted cores meet.

### Sizing one tile type

ECC's registry holds thirteen entries and no die among them, so a die reaches a
run through the workspace step config that `flow.project.patch_floorplan` writes
after synthesis, never through `ecc.toml`. It is still configurable per type,
through `plan` rather than around it. A `Tile/<type>/ecc_config.toml` may carry

    [die]
    width_micron = 120.0
    height_micron = 117.6

and either edge may be left out, in which case it keeps the size `ANCHOR` scales
from `eFPGA_geometry.csv`.

Abutment is what makes this less free than it looks. The fabric has one width per
column and one height per row, so a width reaches every type sharing those
columns and a height every type sharing those rows. In this fabric only `W_IO`
owns a column alone; `LUT4x8_ha`'s width is also `N_IO`'s and
`S_IO`'s, and any core type's height is also the other four's.
`plan` applies that propagation and refuses the cases where it cannot: two types
in one column or row asking for different sizes, an edge off the 0.2 um site or
2.8 um row grid, and a height on a supertile like `MACC`, which spans two rows and
so does not say how tall each is.

Because the override goes through `plan`, `check` still proves the fabric on it.
`W_IO` widened to 90 um gives a 1064.2 x 1668.8 um fabric whose 32523 links
still meet at one coordinate. After editing a `[die]` run `task plan`, `task
check` and then `task harden` for every type whose size moved, which is every
type sharing those columns and rows. Forgetting the harden is not silent:
`task assemble` refuses the stale tile by name.

## Failing loudly

A stage refuses to run on stale inputs rather than producing a plausible wrong
answer. `check` rejects a plan whose links do not meet at one coordinate.
`harden` rejects a tile whose die does not match the plan, and reports any pin
that moved between the floorplan and the filler DEF. `stitch` rejects a tile
whose routed die is not the size the plan being abutted says, which is the case
that arises from editing a `[die]` and re-planning without re-hardening, and a
pin that does not overlap its own net's routing. `stitch` rejects a seam carrying the
wrong number of crossings, or one joining two pins that are not the ends of a
link `eFPGA.v` declares.

Two flags exist only to attribute a failure and should be left alone otherwise.
`harden --no-extend-power` leaves the PDN inside the core, so an abutted fabric
has no power across its seams, and `harden --status PLACED` writes the pins in
the status iEDA silently overwrites.
