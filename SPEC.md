# A 1 mm² eFPGA on ICS55

This spec sizes a FABulous fabric to a one square millimetre budget on the ICS55
55 nm process, delivered through the OpenECOS MPC shared die. It fixes the grid,
names the memory macro and states which figures are measured and which are not.
Every tile geometry it uses is frozen in `Tile/<type>/ecc_config.toml` and every
cell area comes from `sweep/results.tsv`, except the block-RAM column, which is
sized from vendor LEFs and one estimate that the text marks.

The fabric is logic, hard multiply accumulate and block RAM. It carries no
register-file tile, and the reason is measured rather than assumed: the logic
budget cannot host a soft CPU, so the register file the column existed for has
no design to serve. What removing it buys is set out in the grid.

## The headline

| | |
|---|---|
| logic | **640** `FABULOUS_LC`, each a LUT4 with flip-flop and carry |
| block RAM | **160 kbit**, five single-port macros, 32-bit port |
| DSP | **5** `MACC_8x8_20` |
| multi-port storage | **none**, see the limitation below |
| hosts a picorv32 | **no**, measured: it needs 2122 cells at minimum |
| external IO | 26 bidirectional bits |
| Fmax | unmeasured |
| array | 954.8 × 884.8 um, 844,807 um², aspect 1.08 |
| with config and channel | 875,930 um², 87.6% of 1 mm² |

The array is 954.8 um wide and 884.8 um tall, and the configuration block and
channel add about 35 um on whichever edge they sit, so the footprint is roughly
990 × 885 or 955 × 917. Either way it clears 1000 um on both axes, with the MPC
frame's own overhead unknown. The three variants at the end all spend the
remaining 12.4% and none of them clears 1000 um.

## The grid

Ten core rows between two terminator rows, and four column types. Abutment gives
a column one width and a row one height, so the table is the whole geometry.

| column | width um | share | what it holds |
|---|---|---|---|
| `W_IO` | 28.8 | 3.0% | one `IOBUF` per row, 10 external bits |
| `LUT4x8_ha` × 8 | 660.8 | 69.2% | 8 `FABULOUS_LC` per tile, 640 total |
| `MACC` | 70.8 | 7.4% | one `MACC_8x8_20` per two rows |
| block RAM | 194.4 | 20.4% | one `1024x32_m4` macro per two rows |

Row height is 84.0 um for the ten core rows and 22.4 um for each terminator, so
the array is `2 × 22.4 + 10 × 84.0 = 884.8` um tall. The `LUT4x8_ha` width of
82.6 um is the measured routing floor: 81.8 um places at 0.9888 of its placeable
area but leaves three DRC violations after nine detailed-routing iterations.

Against the previous arrangement, which carried six LUT columns and a 95.8 um
`RegFile` column, the fabric gains two LUT columns for 160 logic cells and four
external bits, and loses 139.0 um of width because the block-RAM macro narrows.
Logic density rises from 530 to 758 `FABULOUS_LC` per mm² of array.

## The block-RAM column

The column carries `ics55_ecos_sram_1024x32_m4` from the ECOS Factory SRAM
compiler, 32 kbit single-port synchronous. It sits in a two-row supertile
adapted from `Tile/E_IHP_SRAM`, which the classic FABulous library builds around
`IHP_SRAM_1024x32_1RW`: the macro is a BEL in the bottom half and its interface
splits across both rows.

**The 32-bit macro is chosen because the vendored tile is drawn for exactly it.**
`E_IHP_SRAM_top` carries `top2bot_ADDR` 5, `top2bot_DIN` 16, `top2bot_BM` 16 and
`bot2top_DOUT` 16, and the bottom half carries the matching set, so the tile
presents 10 address, 32 data in, 32 bit-mask and 32 data out. A 1024-deep 32-bit
macro lands on that with no wire to add or tie off. `1024x64_m4` would need 32
more data wires and 32 more mask wires through the switch matrix, and a
512-deep macro would leave an address bit dead.

The wiring is a wrapper rather than a redraw. `IHP_SRAM_1024x32_1RW` is a
pass-through that exposes `CLK`, `ADDR[9:0]`, `DIN`, `BM`, `WEN`, `MEN`, `REN`
and `DOUT` to the fabric and gates `MEN` on `CONFIGURED_top`; the ICS55 macro
exposes `CLK`, `A[9:0]`, `D`, `WEB[31:0]`, `GWEB`, `CEB`, `Q` and the margin
pins `MAR[3:0]` with `MARE`. Read from the behavioural model, the ICS55 part
computes `mem_write[n] = ~CEB & ~GWEB & ~WEB[n]` and `mem_read = ~CEB & GWEB`,
so **`WEB` is a genuine per-bit mask** and `BM` maps to it one for one inverted,
`WEN` is `GWEB` inverted and `MEN` is `CEB` inverted. `MAR` and `MARE` tie off
through the primitive's own `TIE_LOW_SRAM`.

**`REN` has no counterpart, and that is a semantic difference rather than a
spare wire.** The ICS55 `Q` is a registered output that holds only while `CEB`
is high, and it write-throughs the written bits on a write cycle. A design that
lowers `REN` to hold `DOUT` while leaving `MEN` asserted gets a fresh read
instead. The wrapper either ties `REN` off and documents the hold as
`MEN`-controlled, or folds it into `CEB` as `MEN & REN` and gives up the
write-through path. That choice is the one open question in the adaptation; the
tile CSVs and switch matrix lists do not change either way.

**The dimensions are not directly measured.** `1024x32_m4` is not in the
published release set of `ics55_ecos_sram`, and the compiler generates a
configuration on request rather than serving a fixed catalogue, so its package
has to be built before the number is a measurement. Width is 164.430 um and that
is measured twice: `256x32_m4` and `32x32_m4` both have 128 columns and both
report `SIZE 164.430`, across an eight-fold change in depth, so width depends on
columns alone and 1024 words at mux 4 gives the same 128. Height is predicted at
about 155 um from `1024x64_m4`, which has the same 256 rows and reports 155.535,
and height is not linear in rows, so treat it as approximate. Two rows give
`2 × 84.0 − 4 = 164` um of core height, which clears either figure.

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
without paying for it. Halving it to mux 2 would narrow the column to about
127 um at 64 columns, which `256x16_m4` measures at 97.230, but 512 rows then
stand about 278 um tall and need a four-row supertile, and the vendored tile is
a two-row one.

The 194.4 um column is the macro plus a 2 um margin each side plus **26 um of
switch-matrix strip, which is an estimate rather than a measurement**. It scales
`RegFile`'s switch matrix and configuration, about 4400 um² across 299 matrix
lines, down to the 231 lines `E_IHP_SRAM` carries, and spreads the result over a
164 um core at 0.8 density. One hardened tile replaces it with a number.

## What the memory costs, and what the fabric no longer has

At 172,005 um² for 160 kbit the column runs at 1.050 um²/bit. The 64-bit macro
it replaces ran the column at 0.900, so the narrower part costs **17% more per
bit**, partly because `1024x32_m4` is 0.780 um²/bit of raw macro against
`1024x64_m4`'s 0.720, and partly because the 26 um switch strip amortises over
half as many bits. The narrower macro frees 139.0 um and the departed `RegFile`
column frees another 95.8, so 234.8 um is available; two LUT columns take 165.2
of it and 69.6 um stays unspent.

**The fabric has no multi-port storage at all, and nothing recovers it.** The
ECOS macro is single-port by specification, the compiler offers no dual-port
configuration, and `FABULOUS_LC` has no LUT RAM because its `INIT` comes from
`ConfigBits`, declared `GLOBAL` and written only by the configuration chain. Any
design needing a simultaneous read and write of small storage builds it from
flip-flops at one `FABULOUS_LC` per bit, so a 32 × 32-bit two-read one-write
file costs 1728 cells and does not fit. That is the price of removing the
`RegFile` column and it is the weakest line in this spec after external IO.

Restoring it is a column, not a redesign. `Tile/RegFile` is still in the tree
with a frozen 95.8 um die, so a variant that wants 1280 bits of two-read
one-write storage adds the column back and gives up one LUT column and 13.2 um.

## The MPC interface

The shared die exposes `user_io[72:0]`, of which `user_io[6:0]` is a 7-bit
design ID sampled during reset and `user_io[72:7]` is the 66-bit payload the
design sees as `io_in`, `io_out` and `io_oe`.

| | payload bits |
|---|---|
| fabric IO, 26 bidirectional | 26 |
| `SYS_RESET_RESET_top` | 1 |
| `Rx`, `s_clk`, `s_data`, `ComActive`, `ReceiveLED` | 5 |
| **total** | **32 of 66** |

External IO is 26 because `W_IO` gives one bit per core row, ten of them, while
`N_IO` and `S_IO` sit only over the LUT columns, eight each, and the block-RAM
column takes the east edge that `E_IO`'s fourteen bits would have used.

`CLK` and `resetn` map to the frame's own `clock` and `reset` and cost no
payload. The parallel configuration path, `SelfWriteData[31:0]` with
`SelfWriteStrobe`, would add 33 and is left unused; configuration goes over UART
or bitbang. `primitives/IOBUF/fabulous/IOBUF.v` is logic-level with no pad cell,
so the mapping is direct: `IN_top` is `io_out`, `EN_top` is `io_oe` and
`OUT_top` is `io_in`.

**Thirty-four payload bits are spare, and external IO is still the weakest line
in this spec.** Twenty-six bits is thin for an eFPGA. The upstream tile library
carries `W_IO2` and `W_IO4` variants giving two and four bits per row, which the
repo dropped as "wider pin counts of edges this fabric does not need". Bringing
`W_IO4` back would take the west edge from 10 bits to 40 and the total to 56,
inside the payload with room, at the cost of a wider `W_IO` column whose width is
not known here. The 12.4% of the budget left unspent is where that width comes
from.

## Top-level integration

The array is stitched from hardened tiles, not built flat, and `eFPGA_top` wraps
it with one `eFPGA_Config`, one `Frame_Data_Reg` per core row and one
`Frame_Select` per column. The 11,123 um² budgeted above is the fourteen-row
block hardened standalone at 0.85, used here as a ceiling: at ten rows four
`Frame_Data_Reg` come out, 1,160 um² of cells less, against one `Frame_Select`
added for the eleventh column. A further 20,000 um² on top of that is reserved
for the routing channel between the configuration logic and the array edge and
for the PDN straps over it, and **that reserve is a placeholder rather than a
measurement**, since no top-level floorplan has been run. Nothing in `flow/`
targets `eFPGA_top` today: `TOP_MODULE` is `"eFPGA"` in both `flow/cli.py` and
`flow/topdesign.py`, so the flow stops at the tile array.

That leaves 124,070 um² spare against the budget, 12.4%.

## Three alternatives

| variant | LC | DSP | kbit | IO | width um | array um² | of 1 mm² | ≤1000 um |
|---|---|---|---|---|---|---|---|---|
| **as specified**, 8 LUT, 1 MACC, `1024x32_m4` | **640** | 5 | 160 | 26 | 954.8 | 844,807 | 87.6% | **yes, ~990 with config** |
| logic-max, 9 LUT, 1 MACC | 720 | 5 | 160 | 28 | 1037.4 | 917,892 | 94.9% | no |
| DSP-rich, 8 LUT, 2 MACC | 640 | 10 | 160 | 26 | 1025.6 | 907,451 | 93.9% | no |
| memory-heavy, 7 LUT, 1 MACC, `1024x64_m4` | 560 | 5 | 320 | 24 | 1011.2 | 894,710 | 92.6% | no |

Nine LUT columns and two MACC columns together come to 1108.2 um, which is over
the area budget, so the second and third rows are alternatives to each other
rather than a pair. The memory-heavy row is the only one that uses a macro
already downloaded and measured, and it is the arrangement to take if the
`1024x32_m4` package turns out not to build.

The logic-to-DSP ratio is a stated choice rather than an accident. As specified
the fabric runs 128 logic cells per multiply accumulate; the DSP-rich row halves
it to 64. No commercial ratio is quoted against it because none has been sourced.

## Against commercial parts

The feature list is shorter than it was. LUT4 with flip-flop and carry, hard
multiply accumulate and embedded single-port RAM are what a small commercial
eFPGA core advertises; distributed two-read one-write storage is the line this
fabric no longer has, and commercial parts do have it.

**The split is not uniform, and it decides which line leads a datasheet.** The
block-RAM column runs at 1.050 um²/bit, which is within a small factor of any
compiled 55 nm SRAM because it *is* a compiled 55 nm SRAM with a switch matrix
beside it, so the memory figure is commercial-grade on its own terms. The logic
figure is not.

**The logic density is not comparable, and no arrangement of columns changes
it.** Measured on one `LUT4x8_ha`, 614 `LATHX1H7L` configuration latches are
39.6% of the die and 345 `MUX4X1H7L` with 32 `MUX2X1H7L` are 33.3%, so
configuration storage and routing switches together are 73% of the silicon.
Commercial eFPGA builds neither out of standard cells: a configuration bit is a
custom 5T or 6T cell drawn to pitch and a routing switch is a pass transistor,
not a `MUX4X1H7L` at 6.44 um². That is where the gap lives and it is an
implementation problem. This fabric runs at 758 LC/mm² of array, up from 530
once the `RegFile` column leaves and the memory column narrows. No commercial
per-node density figure is quoted here because none has been sourced.

The `tiny` tile family does not move this. Against `classic` its LUT tile has
222 muxes to 234, 1136 total mux inputs to 1296 and 423 routing configuration
bits to 471, so about 9% less cell area, bought by deleting every length-4 and
length-6 wire.

## What is not known

**This fabric does not host a picorv32, and that is measured rather than
assumed.** `synth_fabulous` against picorv32 gives 2122 logic cells in its
leanest usable configuration, 2698 at its defaults and 4421 with multiply and
divide. This spec offers 640. A minimal picorv32 at 100% occupancy needs 19 LUT
columns over 14 rows, about 2.56 mm², and at a realistic 80% occupancy about
3.07 mm².

    picorv32 minimal        2122 LC    1663 LUT  +  459 LUTFF
    picorv32 no counters    2229 LC
    picorv32 default        2698 LC    2101 LUT  +  597 LUTFF
    picorv32 with mul/div   4421 LC

**So a soft CPU is not what one square millimetre of this fabric is for.** The
spec stands as an accelerator or glue fabric beside a hard core, which is the
ordinary eFPGA arrangement and the one the MPC reference SoC already implies by
carrying its own NPC core. If the fabric is meant to host a CPU instead, the
budget is wrong by a factor of three to four, not by a column.

The block-RAM tile does not exist as a hardened tile. `Tile/E_IHP_SRAM` is
vendored and inert. Its interface needs no change for `1024x32_m4`, as set out
above, but its BEL still points at `primitives/IHP_SRAM_1024x32_1RW`, which has
to become an ICS55 wrapper, and the tile has never been placed or routed at a
194.4 × 168 um die, so the 26 um switch strip is the unmeasured part of the
column width.

The block RAM's Yosys memory library was not vendored. Inferring a memory onto
`IHP_SRAM_1024x32_1RW` needs a `memory_libmap` library and a techmap that
`synth_fabulous` does not carry by default, the same gap that made the register
file unreachable. Without it a memory lowers to flip-flops.

Two terminator tiles do not exist yet. The block-RAM column needs its own
`N_term` and `S_term` the way `MACC` has `N_term_MACC` and `S_term_MACC`, sized
to the 194.4 um column and 22.4 um terminator rows. `N_term_RegFile` and
`S_term_RegFile` leave the fabric with the column they terminate.

Fmax is unmeasured. The only figure on record is `sta_frequency_mhz 20` from a
tile hardened in isolation with `set_input_delay 0`, which is an IO-to-IO
feedthrough through the switch matrix rather than a routed design's clock.

Changing the grid means regenerating `fabric.csv` and `eFPGA.v` through
FABulous, re-deriving every `io_pin_order.yaml` and re-running the
configuration-bit mapping. `flow sync-tiles` must not be used for any of it: it
removes every `Tile/<type>/` except `include`, taking all the frozen
`ecc_config.toml` with them.
