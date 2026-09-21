# A 1 mm² eFPGA on ICS55

This spec sizes a FABulous fabric to a one square millimetre budget on the ICS55
55 nm process, delivered through the OpenECOS MPC shared die. It fixes the grid,
names the memory macro and states which figures are measured and which are not.
Every tile geometry it uses is frozen in `Tile/<type>/ecc_config.toml` and every
cell area comes from `sweep/results.tsv`, except the block-RAM column, which is
sized from vendor LEFs and one estimate that the text marks.

## The headline

| | |
|---|---|
| logic | **480** `FABULOUS_LC`, each a LUT4 with flip-flop and carry |
| block RAM | **320 kbit**, five single-port macros |
| DSP | **5** `MACC_8x8_20` |
| register file | **1280 bit** 2R1W, ten `RAM_32x4_2R_1W` tiles |
| hosts a picorv32 | **no**, measured: it needs 2122 cells at minimum |
| external IO | 22 bidirectional bits |
| Fmax | unmeasured |
| array | 1024.4 × 884.8 um, 906,389 um², aspect 1.16 |
| with config and channel | 937,512 um², 93.8% of 1 mm² |

## The grid

Ten core rows between two terminator rows, and six column types. Abutment gives
a column one width and a row one height, so the table is the whole geometry.

| column | width um | share | what it holds |
|---|---|---|---|
| `W_IO` | 28.8 | 2.8% | one `IOBUF` per row, 10 external bits |
| `LUT4x8_ha` × 6 | 495.6 | 48.4% | 8 `FABULOUS_LC` per tile, 480 total |
| `RegFile` | 95.8 | 9.4% | one `RAM_32x4_2R_1W` per tile, 2R1W |
| `MACC` | 70.8 | 6.9% | one `MACC_8x8_20` per two rows |
| block RAM | 333.4 | 32.5% | one SRAM macro per two rows |

Row height is 84.0 um for the ten core rows and 22.4 um for each terminator, so
the array is `2 × 22.4 + 10 × 84.0 = 884.8` um tall. The `LUT4x8_ha` width of
82.6 um is the measured routing floor: 81.8 um places at 0.9888 of its placeable
area but leaves three DRC violations after nine detailed-routing iterations.

## The block-RAM column

The column carries `ics55_ecos_sram_1024x64_m4` from the ECOS Factory SRAM
compiler, 303.415 × 155.535 um, 64 kbit single-port synchronous. It sits in a
two-row supertile adapted from `Tile/E_IHP_SRAM`, which the classic FABulous
library builds around `IHP_SRAM_1024x32_1RW` on the same pattern: the macro is a
BEL in the bottom half and its interface splits across both rows.

Two rows give `2 × 84.0 − 4 = 164` um of core height, so the macro fits with
8.5 um to spare. Its width sets the column, the way `MACC`'s macro sets 70.8.

**The macro tops out at MET4.** Nine configurations were downloaded from the
`ics55_ecos_sram` releases and every one names MET1 to MET4 and VIA1 to VIA3 and
nothing else, obstructions included. `VDD` and `VSS` are `INOUT` pins on MET4,
vertical stripes 0.41 um wide spanning the macro height. The fabric's PDN runs
MET1 and MET5 vertically with MET4 horizontally, so **the MET5 straps cross the
macro freely and MET4 is the layer that has to route around it**, together with
the east-west signal layer which shares MET4.

Column mux is an aspect-ratio knob at constant area rather than an area knob.
`1024x64_m4` is 303.4 × 155.5 um and `1024x64_m8` is 567.6 × 83.6, 47,192
against 47,428 um², 0.5% apart. Doubling the mux multiplies width by 1.87 and
height by 0.54, so the macro can be reshaped to whatever supertile it has to fit
without paying for it.

The 333.4 um column is the macro plus a 2 um margin each side plus **26 um of
switch-matrix strip, which is an estimate rather than a measurement**. It scales
`RegFile`'s switch matrix and configuration, about 4400 um² across 299 matrix
lines, down to the 231 lines `E_IHP_SRAM` carries, and spreads the result over a
164 um core at 0.8 density. One hardened tile replaces it with a number.

## What the memory costs and buys

At 294,992 um² for 320 kbit the column runs at 0.900 um²/bit. The `RegFile`
column beside it runs at 65 um²/bit, 72 times worse, and that ratio is why the
two are not substitutes in the other direction either: `RAM_32x4_2R_1W` is
genuinely two-read one-write, and a single-port macro cannot serve a register
file that reads two operands and writes a result in one cycle. The fabric has no
distributed LUT RAM to fall back on, since `FABULOUS_LC`'s `INIT` comes from
`ConfigBits`, declared `GLOBAL` and written only by the configuration chain.

Ten rows give ten `RegFile` tiles, which is one 32 × 32-bit RV32 register file
in eight of them with 256 bits spare.

## The MPC interface

The shared die exposes `user_io[72:0]`, of which `user_io[6:0]` is a 7-bit
design ID sampled during reset and `user_io[72:7]` is the 66-bit payload the
design sees as `io_in`, `io_out` and `io_oe`.

| | payload bits |
|---|---|
| fabric IO, 22 bidirectional | 22 |
| `SYS_RESET_RESET_top` | 1 |
| `Rx`, `s_clk`, `s_data`, `ComActive`, `ReceiveLED` | 5 |
| **total** | **28 of 66** |

External IO is 22 because `W_IO` gives one bit per core row, ten of them, while
`N_IO` and `S_IO` sit only over the LUT columns, six each, and the block-RAM
column takes the east edge that `E_IO`'s fourteen bits would have used.

`CLK` and `resetn` map to the frame's own `clock` and `reset` and cost no
payload. The parallel configuration path, `SelfWriteData[31:0]` with
`SelfWriteStrobe`, would add 33 and is left unused; configuration goes over UART
or bitbang. `primitives/IOBUF/fabulous/IOBUF.v` is logic-level with no pad cell,
so the mapping is direct: `IN_top` is `io_out`, `EN_top` is `io_oe` and
`OUT_top` is `io_in`.

**Thirty-eight payload bits are spare, and external IO is the weakest line in
this spec.** Twenty-two bits is thin for an eFPGA. The upstream tile library
carries `W_IO2` and `W_IO4` variants giving two and four bits per row, which the
repo dropped as "wider pin counts of edges this fabric does not need". Bringing
`W_IO4` back would take the west edge from 10 bits to 40 and the total to 52,
inside the payload with room, at the cost of a wider `W_IO` column whose width is
not known here.

## Top-level integration

The array is stitched from hardened tiles, not built flat, and `eFPGA_top` wraps
it with one `eFPGA_Config`, one `Frame_Data_Reg` per core row and ten
`Frame_Select`. The 11,123 um² budgeted above is the fourteen-row block hardened
standalone at 0.85, used here as a ceiling: at ten rows four `Frame_Data_Reg` come
out, 1,160 um² of cells less. A further 20,000 um² on top of that is reserved for
the routing channel between the configuration logic and the
array edge and for the PDN straps over it, and **that reserve is a placeholder
rather than a measurement**, since no top-level floorplan has been run. Nothing
in `flow/` targets `eFPGA_top` today: `TOP_MODULE` is `"eFPGA"` in both
`flow/cli.py` and `flow/topdesign.py`, so the flow stops at the tile array.

That leaves 62,488 um² spare against the budget, 6.2%.

## Two alternatives

| variant | LC | kbit | DSP | IO | array um² | of 1 mm² | aspect |
|---|---|---|---|---|---|---|---|
| **balanced**, 6 LUT × 10 rows, `1024x64_m4` | **480** | **320** | 5 | 22 | 906,389 | 93.8% | 1.16 |
| logic-heavy, 8 LUT × 10 rows, `256x32_m4` | 640 | 80 | 5 | 26 | 929,571 | 96.1% | 1.19 |
| square, 6 LUT × 10 rows, `256x32_m4` | 480 | 80 | 5 | 22 | 783,402 | 81.5% | 1.00 |

The logic-heavy variant trades a quarter of the memory for a third more logic and
uses a one-row block-RAM tile, which is a new tile rather than an adaptation of
`E_IHP_SRAM`: the two-row split exists precisely so a 32-bit interface can land
across two rows of switch matrix, and collapsing it to one row is unproven.

## Against commercial parts

The feature list is comparable. LUT4 with flip-flop and carry, hard multiply
accumulate, embedded single-port RAM and distributed two-read one-write register
files are what a small commercial eFPGA core advertises.

**The split is not uniform, and it decides which line leads a datasheet.** The
block-RAM column runs at 0.900 um²/bit, which is within a small factor of any
compiled 55 nm SRAM because it *is* a compiled 55 nm SRAM with a switch matrix
beside it, so the memory figure is commercial-grade on its own terms. The logic
figure is not.

**The logic density is not comparable, and no arrangement of columns changes it.**
Measured on one `LUT4x8_ha`, 614 `LATHX1H7L` configuration latches are 39.6% of
the die and 345 `MUX4X1H7L` with 32 `MUX2X1H7L` are 33.3%, so configuration
storage and routing switches together are 73% of the silicon. Commercial eFPGA
builds neither out of standard cells: a configuration bit is a custom 5T or 6T
cell drawn to pitch and a routing switch is a pass transistor, not a
`MUX4X1H7L` at 6.44 um². That is where the gap lives and it is an implementation
problem. This fabric runs at 530 LC/mm² of array in the balanced variant, down
from 773 because memory takes area. No commercial per-node density figure is
quoted here because none has been sourced.

## What is not known

**This fabric does not host a picorv32, and that is now measured rather than
assumed.** `synth_fabulous` against picorv32 gives 2122 logic cells in its
leanest usable configuration, 2698 at its defaults and 4421 with multiply and
divide. The balanced variant offers 480. A minimal picorv32 at 100% occupancy
needs 19 LUT columns over 14 rows, about 2.56 mm², and at a realistic 80%
occupancy about 3.07 mm².

    picorv32 minimal        2122 LC    1663 LUT  +  459 LUTFF
    picorv32 no counters    2229 LC
    picorv32 default        2698 LC    2101 LUT  +  597 LUTFF
    picorv32 with mul/div   4421 LC

**So a soft CPU is not what one square millimetre of this fabric is for.** The
spec stands as an accelerator or glue fabric beside a hard core, which is the
ordinary eFPGA arrangement and the one the MPC reference SoC already implies by
carrying its own NPC core. If the fabric is meant to host a CPU instead, the
budget is wrong by a factor of three to four, not by a column.

That reframing weakens the `RegFile` column's justification, since the register
file it exists for belongs to a CPU the fabric cannot hold. Ten tiles and 95.8 um
of width are still the cheapest two-read one-write storage available, but the
case for them is no longer the RV32 one.

**Whether eight stacked `RegFile` tiles route as one register file is
unmeasured.** Ganging them into 32 bits broadcasts fifteen address, three enable
and three clock wires up the column through the switch matrix and gathers 96 data
wires back. That is nextpnr's answer rather than arithmetic, and the CPU register
file is the use case the column exists for.

The register-file inference path is not wired up. `synth_fabulous` runs
`memory_libmap -lib +/fabulous/ram_regfile.txt` by default, which emits
`RegFile_32x4`, a primitive with flat bit-split ports that this fabric does not
have; the tile carries `RAM_32x4_2R_1W` with vector ports. The upstream library
ships the bridge at `primitives/RAM_32x4_2R_1W/yosys/`, three files that were not
vendored, and its techmap matches `$__RAM_32x4_2R_1W_[AS][AS]_`, which only the
upstream memlib emits. So `-noregfile` plus an explicit `memory_libmap` and
`techmap` is needed, not a file copy. Without it a register file lowers to
flip-flops, and a 32 × 32-bit one costs 1728 logic cells.

Fmax is unmeasured. The only figure on record is `sta_frequency_mhz 20` from a
tile hardened in isolation with `set_input_delay 0`, which is an IO-to-IO
feedthrough through the switch matrix rather than a routed design's clock.

The block-RAM tile does not exist. `Tile/E_IHP_SRAM` is vendored and inert, its
CSVs cut for a 1024×32 macro where `1024x64_m4` is 64 bits wide, so the extra 32
bits either widen the `top2bot` interface or are tied off. Its Yosys memory
library was not vendored either, for the same reason as the register file's.

Two terminator tiles do not exist yet. The block-RAM column needs its own
`N_term` and `S_term` the way `MACC` and `RegFile` have theirs, sized to the
333.4 um column and 22.4 um terminator rows.

Changing the grid means regenerating `fabric.csv` and `eFPGA.v` through
FABulous, re-deriving every `io_pin_order.yaml` and re-running the
configuration-bit mapping. `flow sync-tiles` must not be used for any of it: it
removes every `Tile/<type>/` except `include`, taking all the frozen
`ecc_config.toml` with them.
