# A 1 mm² eFPGA on ICS55

Two variants share this spec's tile library and differ only in the east column.
`fabrics/bram` places `E_BRAM` there. `fabrics/nobram` places `E_IO`, for an
integration that cannot depend on the ECOS SRAM compiler, and spends the width
the memory column took on two more logic columns. The sections after this table
describe the block-RAM fabric, and where they name `E_BRAM` the no-BRAM variant
has `E_IO`.

| | `bram` | `nobram` |
|---|---|---|
| array | 954.8 × 884.8 um | 947.0 × 884.8 um |
| area | 844,807 um², 87.6% of 1 mm² | 837,906 um², 83.8% |
| logic | 640 `FABULOUS_LC` | 800 `FABULOUS_LC` |
| DSP | 5 `MACC_8x8_20` | 5 `MACC_8x8_20` |
| block RAM | 80 kbit | none |
| external IO | 26 | 40 |
| tiles | 122 | 151 |
| seam crossings | 26098, all conduct | 31760, all conduct |
| tiles with DRC | `E_BRAM` at 45 | none |
| hard macro | one per two rows | none |
| hardened `eFPGA_top` | not run | 999.0 × 912.6 um, 91.2%, DRC 0 |

The no-BRAM variant carries no hard macro, so it has no vendor dependency and no
tile above zero DRC. Ten logic columns is the last count that fits: eleven would
be 1029.6 um wide, over the 1000 um axis, at 91.1% of the budget. The split is
five each side of the multiplier, which is both the even split and the centred
one, with the multiplier's midline at 477.2 um against the array's 473.5.

This spec sizes a FABulous fabric to a one square millimetre budget on the ICS55
55 nm process, delivered through the OpenECOS MPC shared die. It fixes the grid,
names the memory macro and states which figures are measured and which are not.
Every tile geometry it uses is frozen in `Tile/<type>/ecc_config.toml` and every
cell area comes from `sweep/results.tsv` at 93bf29a, except the block-RAM column, which is
sized from vendor LEFs and one estimate that the text marks.

The fabric is logic, hard multiply accumulate and block RAM. It carries no
register-file tile, and the reason is measured rather than assumed: the logic
budget cannot host a soft CPU, so the register file the column existed for has
no design to serve. What removing it buys is set out in the grid.

## The headline

| | |
|---|---|
| logic | **640** `FABULOUS_LC`, each a LUT4 with flip-flop and carry |
| block RAM | **80 kbit**, five single-port macros, 512 words of 32 bits |
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
| `LUT4x8_ha` × 5 | 413.0 | 43.3% | 8 `FABULOUS_LC` per tile |
| `MACC` | 70.8 | 7.4% | one `MACC_8x8_20` per two rows |
| `LUT4x8_ha` × 3 | 247.8 | 26.0% | 640 `FABULOUS_LC` over the eight columns |
| block RAM | 194.4 | 20.4% | one `512x32_m4` macro per two rows |

The `MACC` column sits between the logic columns rather than beside the memory,
and the split is five to three because that is what centres it: its midline is
at 477.2 um against the array's 477.4, and no logic column is more than five
away from a multiplier where the old arrangement put some of them eight.

Row height is 84.0 um for the ten core rows and 22.4 um for each terminator, so
the array is `2 × 22.4 + 10 × 84.0 = 884.8` um tall. The `LUT4x8_ha` width of
82.6 um is the measured routing floor: 81.8 um places at 0.9888 of its placeable
area but leaves three DRC violations after nine detailed-routing iterations.

Against the previous arrangement, which carried six LUT columns and a 95.8 um
`RegFile` column, the fabric gains two LUT columns for 160 logic cells and four
external bits, and loses 139.0 um of width because the block-RAM macro narrows.
Logic density rises from 530 to 758 `FABULOUS_LC` per mm² of array.

This grid is built rather than only written down. `fabric.csv` describes it,
`Fabric/eFPGA.v` instantiates its 122 tiles, and `flow plan` derives the same
954.8 × 884.8 um from the `[die]` tables with 26,098 links meeting at one
coordinate each.

## The block-RAM column

The column carries `ics55_ecos_sram_512x32_m4` from the ECOS Factory SRAM
compiler, 16 kbit single-port synchronous, measured at 164.430 × 90.535 um from
the release package's own abstract LEF. It sits in a two-row supertile,
`Tile/E_BRAM`, which is the classic FABulous library's `E_IHP_SRAM` renamed: the
wire lists and both switch matrices are upstream's and the only edit is the BEL
line, which now names `primitives/ICS55_SRAM_512x32_1RW`.

**The 32-bit macro is chosen because the vendored tile is drawn for exactly it.**
`E_BRAM_top` carries `top2bot_ADDR` 5, `top2bot_DIN` 16, `top2bot_BM` 16 and
`bot2top_DOUT` 16, and the bottom half carries the matching set, so the tile
presents 10 address, 32 data in, 32 bit-mask and 32 data out. A 32-bit macro
lands on that with no wire to add or tie off, where a 64-bit one would need 32
more data wires and 32 more mask wires through the switch matrix.

**Depth is where the built column and the intended one differ.** The tile's ten
address wires want 1024 words and `ics55_ecos_sram_1024x32_m4` would carry them,
but that configuration is not in the published release set of `ics55_ecos_sram`
and the compiler generates on request, so nothing could be built against it.
`512x32_m4` is in the set, was downloaded and is vendored under
`primitives/ICS55_SRAM_512x32_1RW/ics55/`, and leaves `ADDR[9]` reaching no
macro pin. **The fabric therefore carries 80 kbit and not the 160 the column is
drawn for.** The swap costs nothing when the deeper part exists: width depends
on column count alone, measured at 164.430 on `256x32_m4` and `32x32_m4` across
an eight-fold change in depth, so the 1024-deep part is the same 164.430 wide
and about 155 um tall against this one's 90.535, which the 164 um of core height
still clears. Nothing outside `[macro]` in `Tile/E_BRAM/ecc_config.toml` changes.

The wiring is a wrapper rather than a redraw, and it instantiates the macro
rather than bringing it out on `EXTERNAL` ports the way the IHP original does,
because this fabric abuts hardened tiles and the memory has to sit inside the
column. Read from the behavioural model, the ICS55 part computes
`mem_write[n] = ~CEB & ~GWEB & ~WEB[n]` and `mem_read = ~CEB & GWEB`, so **`WEB`
is a genuine per-bit mask**, and the fold that preserves both operations is
`CEB = ~(MEN & CONFIGURED_top & (WEN | REN))` with `GWEB = ~WEN` and
`WEB = ~BM`. `MAR` and `MARE` tie low, which the datasheet's option table gives
as the characterised read-margin setting rather than a repair configuration.

**What the fold does not preserve is `REN` holding `DOUT` through a write.** The
ICS55 `Q` is registered, holds only while `CEB` is high, and write-throughs the
written bits whatever `REN` says. A design that lowers `REN` to hold `DOUT`
across a write gets the written data instead. The tile CSVs and switch matrix
lists are unchanged by this.

**The macro tops out at MET4 and the fabric's PDN clears it.** The tech LEF makes
MET4 vertical and MET5 horizontal; the macro's `VDD` and `VSS` are `INOUT` pins
on MET4, 0.41 um vertical strips spanning its height, and its obstructions cover
MET1 to MET4 and VIA1 to VIA3 as polygons with the pin access cut out. In the
hardened tile the MET1 follow-pin rails stop at the macro's west face and resume
above it, no MET4 stripe crosses it, and eleven MET5 stripes run over it, which
is the layer its power has to be dropped from.

Column mux is an aspect-ratio knob at constant area rather than an area knob.
`1024x64_m4` is 303.4 × 155.5 um and `1024x64_m8` is 567.6 × 83.6, 47,192
against 47,428 um², 0.5% apart. Doubling the mux multiplies width by 1.87 and
height by 0.54, so a macro can be reshaped to whatever supertile it has to fit
without paying for it. That is what makes the 1024-deep swap above free.

**The 194.4 um column is measured, and it is a floor rather than a choice.** It
is the macro, a 2 um margin each side, and a 25.8 um west channel. The three
channels that leaves are what the tile routes in: 25.8 um west, where all 256
east-west pins land, 19.6 um south and 53.7 um north, where each terminator
row's 24 shared pins come in.

What fills the west channel is not the standard cells. There are 758 of them,
2838 um², against 12,000 um² in the band above the macro alone, and the tile
places at 0.246 of its placeable area. It is the escape routing for the 141
east-west pins that sit beside the macro and have to reach past it. Narrowing
the column was swept with every other column held, and the DRC count is the
channel's:

| column um | west channel um | signoff DRC |
|---|---|---|
| **194.4** | **25.8** | **45** |
| 182.4 | 13.8 | 5524 |
| 176.4 | 7.8 | 10118 |
| 170.4 | 1.8 | 8238 |

Rotating the macro does not recover the width either. At R90 it is
90.535 × 164.430 and would leave 480 um² of a 90.6 um column, far under what the
two switch matrices need, and the compiler's next mux step down stands about
167 um tall against 164 um of core.

**The east channel is 0.17 um and is not a channel.** The 65 boundary pins of
that edge, `FrameData_O` for both sub-rows and `CONFIGURED_top`, answer to
nothing outside the fabric, so `flow.plan.macro_shadow` keeps them out of the
macro's span instead of widening the column for them. Placed into it, they cost
4768 DRC violations that nine detailed-routing iterations never reduced.

**The tile is not clean even so.** It signs off at 45 violations, 38 metal
shorts and 7 cut-spacing, all on MET4, where the other eleven types are at zero.
The router itself reports none and no MET4 signal wire crosses the macro, so the
residual is iRT and the signoff DRC engine disagreeing about MET4 rather than a
placement or a macro fault. It is unexplained and it is not counted as passing.

## What the memory costs, and what the fabric no longer has

The column is 171,965 um² and carries 80 kbit as built, which is 2.100 um²/bit,
against 0.909 for the raw macro. The gap is the price of a column drawn for
1024 words and filled with 512: the switch matrices, the configuration memory
and the 25.8 um west channel are sized for the deeper part and amortise over
half its bits. Filling the column brings it to 1.050 um²/bit and costs no area.

The narrower macro frees 139.0 um of width against the 64-bit part the earlier
spec named, and the departed `RegFile` column frees another 95.8, so 234.8 um is
available; two LUT columns take 165.2 of it and 69.6 um stays unspent.

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

`flow/topwrap.py` writes `eFPGA_top` from the variant's own `eFPGA.v`, so the
frame loader is sized by the grid it drives. The loader is `fabric_config` from
fabulous-fabrics, fed by `config_frontend`, which takes the bitstream over UART,
bitbang, SPI or the parallel `SelfWriteData` port. `flow cli integrate` hardens
that top in one ECC run: the 151 tiles as fixed macros, the loader and the
front-ends placed in a channel west of the array and a strip south of it.

Measured on `nobram`, the only variant this has been run on:

| | |
|---|---|
| die | 999.0 × 912.6 um, 911,687 um², 91.2% of 1 mm² |
| array | 947.0 × 884.8 um at (50.0, 24.6) um |
| channel, west | 48.0 um |
| strip, south | 22.4 um, then one 1.4 um row left empty below the array |
| loader and front-ends | 3,105 cells, 8,852 um² after synthesis |
| overhead over the array | 73,781 um², 7.4% of 1 mm² |
| DRC | 0 |
| LVS, signal | 166 IO, 16,890 instances and 3,165 nets match, 0 open, 0 short |
| LVS, power | 139 tiles open, all fed by abutment |
| runtime | 4 min to filler, 58 min of signoff, almost all STA |

The strip holds each column's 20 FrameStrobe gates under the column and the
channel each row's 32 FrameData flops beside the row. Global placement puts
them there, and it has to: legalising from one corner left every cell there, and
the 260 FrameStrobe nets then needed 260 horizontal tracks through a strip that
has 224. The empty row keeps the strip's top MET1 rail clear of the tiles, whose
abstracts reserve all of MET1.

The 139 power opens are the tiles not in the west column. They take VDD and VSS
from their neighbours' stripes across the seam, which the LVS cannot see and
`flow.stitch` proves conducts. The 32,404 seam nets are withheld from the router,
which has no notion of an abutted pin pair, and restored to the final DEF
unrouted.

**The configuration clock does not close at 100 MHz on the slow corners.**
With the CTS tree propagated, setup fails by 5.50 ns at `ss_1p08_125` Cworst and
by 3.73 ns at the -40 °C worst-case corner, and passes by 4.63 ns at typical.
Every failing path lies within the loader and the front-ends: the worst runs from
the SPI sampler through the bitbang and UART muxes into `frame_select`, and 11.4
ns of its 15.4 ns data path is one `AOI21X0P7` driving 14 loads spread along the
channel and the `NOR3X0P5` taking its slew. The flow neither buffers nor resizes
after placement. Hold closes on the loader's own flop-to-flop paths at every
corner, by 0.051 ns at the tightest. That check sees each tile as its extracted
`.lib`, which carries one setup arc, no hold arc and a model at the `MAX` corner
only, so it says nothing about hold inside or between tiles.

**Full-chip hold closes on every register-to-register path at all seven corners
run.** OpenSTA 2.7 linked all 151 routed tile netlists under the top, with each
tile's iRCX SPEF read per instance and the 32,404 abutted seam nets connected,
one user clock on GBUF A and every switch-matrix arc enabled. The bound mode
stands for any bitstream. The tightest endpoints are MACC at 0.092 ns, LUT at
0.110 ns and IO at 0.553 ns, all at `ff_rcbest_1p32_m40` with Cbest parasitics.
MACC used to fail everywhere, by 0.637 ns at that corner and by 3.046 ns on all
280 registers at `ss_cworst_1p08_m40`. `CLK_INV ? !CLK : CLK` had synthesised
to an `AOI21X0P5` driving all 56 registers, 1.405 ns behind the fabric's other
flops, because the tile flow's CTS traces no clock net and builds no tree.
`MACC_8x8_20` now drives the registers through `clk_buf`, which
`techmap/ics55_models.v` maps to `BUFX4H7L`. The rebuilt MACC keeps the same
die and pins, with DRC 0 and LVS clean. Hold still reports negative, down to
-1.464 ns, only on paths that start at the GBUF A source and reach the LC
set/reset through `GSR_BEG`. The bound mode lets one GBUF line be both the clock
and the reset of the same flops, which no bitstream does. Writes into
the configuration latches keep 1.08 ns before the latch's own hold time at 10
ns, set by FrameStrobe falling at the far MACC latch 9.88 ns after the clock at
`ss_rcworst_1p08_125` with Cworst parasitics. Because `fabric_config` changes
FrameData no sooner than one cycle after the strobe falls, the configuration
clock period must exceed 8.92 ns for that write to hold. The same buffer cleared the MACC's minimum pulse width failures.
No flow step repairs design rules, and the checks show it. The four GBUF nets carry 3.1 ns slew at the fast corner and 6.5 ns at the slow ones.
Every LC output `MUX2X0P5` drives about 0.11 pF against a 0.024 to 0.064 pF
limit. The loader's FrameStrobe and FrameData drivers reach 8.7 ns of slew.
OpenSTA counts 40,235 slew and capacitance violations at
`ff_rcbest_1p32_m40` and 57,968 at `ss_rcworst_1p08_125` with Cworst parasitics.

The block-RAM variant has not been integrated. Its array is 7.8 um wider, so
the same channel and strip would put its die at 1006.8 um, over the axis.

## Three alternatives

| variant | LC | DSP | kbit | IO | width um | array um² | of 1 mm² | ≤1000 um |
|---|---|---|---|---|---|---|---|---|
| **as built**, 8 LUT, 1 MACC, `512x32_m4` | **640** | 5 | 80 | 26 | 954.8 | 844,807 | 87.6% | **yes, ~990 with config** |
| same grid, `1024x32_m4` | 640 | 5 | 160 | 26 | 954.8 | 844,807 | 87.6% | **yes**, on a generated package |
| logic-max, 9 LUT, 1 MACC | 720 | 5 | 80 | 28 | 1037.4 | 917,892 | 94.9% | no |
| DSP-rich, 8 LUT, 2 MACC | 640 | 10 | 80 | 26 | 1025.6 | 907,451 | 93.9% | no |
| memory-heavy, 7 LUT, 1 MACC, `1024x64_m4` | 560 | 5 | 320 | 24 | 1011.2 | 894,710 | 92.6% | no |

The second row is the first one with a deeper macro in the same column, and
costs nothing but a compiler run. Nine LUT columns and two MACC columns together
come to 1108.2 um, which is over the area budget, so the third and fourth rows
are alternatives to each other rather than a pair. The memory-heavy row is the
one to take if 320 kbit matters more than 80 logic cells, and it needs the
switch matrix widened to 64 data and 64 mask wires.

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

The fabric-level run floorplans but does not route. `flow top` places all 122
hardened tiles as macros at their planned coordinates in 12 s and writes the
geometry manifest the ECOS viewer reads, and the klayout stitch proves every
seam. What neither gives is a routed parent, and the reason is the abutment
itself: the parent netlist carries 27,390 nets that are already connected by
geometry, iRT has no notion of a pin pair finished by construction, and building
its shape database over all of them reached 49 GB of resident memory on a 61 GB
machine before routing began. Dropping those nets or marking them pre-routed is
the prerequisite, not tuning.

The fabric carries half the memory the column is drawn for, because
`ics55_ecos_sram_1024x32_m4` has to be generated by the compiler and only
`512x32_m4` could be downloaded. That is a package to request, not a design
change: the deeper part is the same width and the column takes it unchanged.

The SRAM package ships no GDS. `primitives/ICS55_SRAM_512x32_1RW/ics55/` holds
the abstract LEF and one liberty corner and nothing else, so the hardened tile
is an abstract with a hole where the macro sits. It abuts, it stitches and it
views; it is not LVS-complete until OpenECOS publishes the layout.

The block RAM's Yosys memory library was not vendored. Inferring a memory onto
`ICS55_SRAM_512x32_1RW` needs a `memory_libmap` library and a techmap that
`synth_fabulous` does not carry by default, the same gap that made the register
file unreachable. Without it a memory in a user design lowers to flip-flops and
the column goes unused.

The block-RAM column needs no terminator of its own. It stands where `E_IO`
stood and carries the same vertical wires, `N_GBUF` and nothing else, so
`NE_term` and `SE_term` terminate it as they terminated `E_IO`. Both were
rebuilt at 194.4 um wide rather than 21.4.

Fmax is unmeasured. The only figure on record is `sta_frequency_mhz 20` from a
tile hardened in isolation with `set_input_delay 0`, which is an IO-to-IO
feedthrough through the switch matrix rather than a routed design's clock.

Changing the grid means regenerating `fabric.csv` and `eFPGA.v` through
FABulous, re-deriving every `io_pin_order.yaml` and re-running the
configuration-bit mapping. `flow sync-tiles` must not be used for any of it: it
removes every `Tile/<type>/` except `include`, taking all the frozen
`ecc_config.toml` with them.
