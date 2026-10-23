# Community Tapeout Project Proposal and Design Report

All figures are for the `nobram` variant at `f82fb9a` on PDK `v1.10.103` (2026-10-14). Every block was built from RTL and pin plans byte-identical to `f82fb9a`.

| Stage | Tools | Build date |
|---|---|---|
| Synthesis | Yosys 0.68 (`38e001a`) inside ECC | as physical |
| Physical | ECC `main` `14be467`, built from source with local edits, one run per tile type and one for `eFPGA_top`. OpenROAD `dcf3613` repairs before routing. | 2026-10-20 for `LUT4x8_ha`, `MACC`, `E_IO`, `S_term`, `S_term_MACC` and `eFPGA_top`. 2026-10-19 for `W_term` and `N_term`. 2026-10-17 for the other five tile types. |
| Signoff | ECC DRC, iLVS and iSTA, with full-chip OpenSTA where stated | as physical |

## Submission Information

| Item | Details |
|---|---|
| Project name | FABulous eFPGA |
| Project lead | King Lok (Kelvin) Chung, kelvin.chung@manchester.ac.uk |
| Contributors | [Names and responsibilities] |
| Source repository | `github.com/KelvinChung2000/demo-ics55`, branch `master`; RTL, builds and simulations at `f82fb9a`, report and appendix at the head. Local at the time of writing, to be pushed before submission. |
| Tapeout run | MPW |
| Process and PDK | ICS55 (55 nm), ECOS PDK `v1.10.103` (`2d72857`), standard cells `ics55_LLSC_H7C_V1p10C100` (`H7CR` and `H7CL`) |
| Report version | v2.0 |
| Submission date | [YYYY-MM-DD] |
| Current project stage | Pre-tapeout |

## 1. Project Overview

### 1.1 Project Summary

The design is an island-style FABulous eFPGA hardened on ICS55 for an OpenECOS MPW die. Its array `eFPGA` abuts 151 hard tiles of 12 types in a 13 × 12 grid of 947.0 × 884.8 µm. The top level `eFPGA_top` adds the configuration controller in 999.0 × 912.6 µm and needs 27 of the MPW's 36 pads. This `nobram` variant omits the block RAM of the `bram` variant.

ECC hardens each tile type once to a routed macro. Abutment connects the 32,404 tile-to-tile nets through coincident pins, so the `eFPGA_top` run routes only the 3,189 nets of the controller, the IO and the configuration buses.

The RTL, the 12 tile types and `eFPGA_top` are hardened and signed off on ECC abstracts (Section 6.3). An RTL bitstream simulation runs a counter on the fabric (Section 5.3). Outstanding are a mask-layer GDS of the whole macro with DRC and LVS (Section 7), the pad and seal rings and a timed user design.

### 1.2 Main Features

| Feature | Description | Implemented in this tapeout? |
|---|---|---|
| Logic cells | 800 `FABULOUS_LC`, 8 per `LUT4x8_ha` tile, each a LUT4 with flip-flop and carry chain | Yes |
| Hard multiply-accumulate | 5 `MACC_8x8_20`, 8 × 8 multiply into a 20-bit accumulator with carry in and out, one per two core rows | Yes |
| User IO | 10 bidirectional bits on `A_IN_top`, `A_EN_top` and `A_OUT_top`, one per `E_IO` tile on the east edge | Yes |
| Global clock network | 4 `GBUF` global clocks in `SW_term`, buffered at every tile hop (Section 2.5) | Yes |
| Frame-based configuration | 69,746 configuration latches (synthesis) written one frame at a time (Section 2.2) | Yes, all 12 rows including the two terminator rows |
| Full and partial reconfiguration | A partial bitstream writes any subset of frames while the rest of the fabric keeps running | Yes by construction of the frame addressing; not yet demonstrated in simulation |
| Configuration controller | `fabric_config` (fabulous-fabrics `7223ee9`) behind `config_frontend`, which merges UART, bitbang and SPI loaders | Yes, hardened in `eFPGA_top` |

### 1.3 Design Highlights and Use Cases (Optional)

The fabric reaches 955 logic cells per mm² of array (95.5% core utilisation) and 877 per mm² of `eFPGA_top`. Configuration and routing set this density, since on one `LUT4x8_ha` the 614 configuration latches take 39.6% of the die and the 345 `MUX4` plus 32 `MUX2` switches 33.3%. Abutment caps the largest tile run at 3,777 instances (`MACC`) and the top run at 3,150 standard cells around 151 fixed macros, against 238,579 instances flat.

![Application scenario](images/application_scenario.png)

**Figure 1-1. Application scenario, with a Raspberry Pi Pico loading the bitstream and clocking the fabric.**

## 2. Design Description

### 2.1 System Architecture

`fabrics/nobram/fabric.csv` sets the grid below. `flow cli integrate` (`flow/topwrap.py`) flattens it with the configuration logic into `build/nobram/top/rtl/eFPGA_top.v`, a netlist of 151 tile macros with the ports of the hierarchical `fabrics/nobram/Fabric/eFPGA_top.v`.

| Column | Width (µm) | Tile types, top to bottom |
|---|---:|---|
| 0 | 28.8 | `NW_term`, `W_term` × 10, `SW_term` |
| 1 to 5 | 82.6 each | `N_term`, `LUT4x8_ha` × 10, `S_term` |
| 6 | 70.8 | `N_term_MACC`, `MACC` supertile × 5, `S_term_MACC` |
| 7 to 11 | 82.6 each | `N_term`, `LUT4x8_ha` × 10, `S_term` |
| 12 | 21.4 | `NE_term`, `E_IO` × 10, `SE_term` |

Core rows are 84.0 µm high and terminator rows 22.4 µm. Routing wires of span 1, 2, 4 and 6 cross each seam. `FrameData` (384 bits, 32 per row) enters on the west edge and `FrameStrobe` (260 bits, 20 per column) on the south edge.

The tiles are the classic library of `FPGA-Research/fabulous-tiles` at `5809cdf` with the FABulous BELs `FABULOUS_LC`, `MACC_8x8_20`, `IOBUF`, `GBUF` and `SYS_RESET`. No other third-party IP is instantiated (Section 11.2). `W_term`, `N_term` and `S_term` are the library's `W_IO`, `N_IO` and `S_IO` without the `IOBUF` BEL, on unchanged dies so every seam pin stays in place.

In `eFPGA_top` the controller occupies a 48 µm west channel and a 22.4 µm south strip. The array's lower-left corner sits at (50.0, 24.6) µm, one 1.4 µm row above the strip.

![System architecture](images/system_architecture.png)

**Figure 2-1. System architecture, configuration path (not to scale).**

### 2.2 Operation

After `resetn` is released a host streams 32-bit words into one loader of `config_frontend`, which gives UART priority over bitbang and bitbang over SPI. Its 32-bit parallel input is tied low because its 33 pins exceed the pad budget. `fabric_config` decodes the stream (Section 2.4) and pulses the `FrameStrobe` of the addressed frame, whose latches capture `FrameData`.

A frame is 32 bits in every row of one column. Each tile holds up to 20 frames (640 bits), of which `LUT4x8_ha` uses 614. A partial bitstream carries only the changed frames while the rest of the fabric keeps running on the separate user clock (Section 2.5). Latches are transparent during `FrameStrobe`, so the user design must hold a rewritten region idle or in reset.

![Data processing flow](images/operation_flow.png)

**Figure 2-2. Configuration and user-mode phases.**

### 2.3 Interface and Port Definitions

The ports below come from `fabrics/nobram/Fabric/eFPGA_top.v` and the loader sources in `Fabric/`. The RTL specifies no reset states.

| Port name | Direction | Width | Clock domain | Active level | Reset state | Description |
|---|---|---:|---|---|---|---|
| `A_OUT_top` | in | 10 | user (fabric) | High | N/A | Pad-to-fabric data, one bit per `E_IO` tile |
| `A_IN_top` | out | 10 | user (fabric) | High | N/A | Fabric-to-pad data |
| `A_EN_top` | out | 10 | user (fabric) | High | N/A | Output enable per IO bit |
| `SYS_RESET_RESET_top` | in | 1 | user (fabric) | Rising edge unless the `GBUF` inverts it | N/A | User clock pad, connected only to the four `GBUF` inputs |
| `CLK` | in | 1 | `CLK` | Rising edge | N/A | Configuration logic clock; does not clock the fabric |
| `resetn` | in | 1 | `CLK` | Low | N/A | Configuration reset; synchronous in `fabric_config`, asynchronous in the bitbang loader |
| `Rx` | in | 1 | `CLK` (sampled) | N/A | N/A | UART bitstream input; one bit lasts `ComRate` + 1 = 218 `CLK` cycles |
| `ComActive` | out | 1 | `CLK` | High | N/A | UART reception in progress |
| `ReceiveLED` | out | 1 | `CLK` | High | N/A | Toggles on UART, bitbang or SPI activity |
| `s_clk`, `s_data` | in | 1 each | `CLK` (sampled) | N/A | N/A | Bitbang configuration clock and data |
| `spi_sck`, `spi_cs_n`, `spi_mosi` | in | 1 each | `CLK` (sampled) | `spi_cs_n` low | N/A | SPI mode-0 write-only slave, no MISO |
| `ConfigBusy` | out | 1 | `CLK` | High | N/A | `fabric_config` is out of idle |
| `Configured` | out | 1 | `CLK` | High | N/A | Cleared by the start word, set by the desync header |

The die needs 27 of the MPW's 36 pads. One bidirectional pad joins the three macro pins of each user IO bit, so the 43 signal pins take 23 signal pads. Four supply pads carry VDD, VSS, VDDIO and VSSIO. The core rails feed the macro's two supply pins in `eFPGA_top_Harden.lef`.

| Pad | Type | `eFPGA_top` pins | Function |
|---|---|---|---|
| `pad[0]` to `pad[9]` | bidirectional | `A_OUT_top[i]`, `A_IN_top[i]`, `A_EN_top[i]` | User IO on `E_IO` X12Y10 (`pad[0]`, bottom of the east edge) to X12Y1 (`pad[9]`, top) |
| 13 single-signal pads | as the port | `SYS_RESET_RESET_top`, `CLK`, `resetn`, `Rx`, `ComActive`, `ReceiveLED`, `s_clk`, `s_data`, `spi_sck`, `spi_cs_n`, `spi_mosi`, `ConfigBusy`, `Configured` | One pad per port, function as in the port table |
| VDD | supply | `vdd_stripe_generate` | Core supply |
| VSS | ground | `vss_stripe_generate` | Core ground |
| VDDIO | supply | none | Pad-ring supply |
| VSSIO | ground | none | Pad-ring ground |

User IO sites come from `fabrics/nobram/user_design/pads.pcf`, while pad positions and package pins are unassigned. The ICS55 IO library `ICSIOA_N55_3P3` offers a 65 × 130 µm signal pad `P65_1233_PBMUX` and a 130 × 130 µm corner. [Pad-cell selection and pad positions, pending the MPW pad-ring rules.]

![Key interface timing](images/interface_timing.png)

**Figure 2-3. SPI loader (mode 0, MSB first) in the cocotb SPI case of `Test/config/test_config_frontend.py` at 25 MHz `CLK`. 32 `spi_sck` bits in one `spi_cs_n` frame yield `bitstream_valid` at 6.84 µs with `0x00AAFF01`, the first word of a `.bit` file.**

### 2.4 Register or Command Definitions (Optional)

The fabric has no memory-mapped registers. It takes a FABulous bitstream of 32-bit words, decoded as below by the loader and `fabric_config` sources in `Fabric/`.

| Address/Command | Name | Access | Reset value | Bit-field definition | Access side effects |
|---|---|---|---|---|---|
| `00 AA FF` + command byte | UART header | W | N/A | Command bit 7 selects hex (1) or binary (0) mode in the default auto mode | Starts a UART load; `ComActive` goes high |
| `0xFAB0_FAB1` | Start word | W | N/A | Fixed pattern | Moves `fabric_config` from idle to header; clears `Configured`; `ConfigBusy` goes high |
| Header word | Frame select | W | N/A | Bits [19:0] one-hot frame, bits [31:27] column, bit 20 desync flag | Selects one frame in one column; the next 12 words are its data |
| Frame data words | Frame data | W | N/A | 32 configuration bits for one row, row 11 first and row 0 last | After the 12th word the column's `FrameStrobe` pulses and the latches capture the frame |
| Header with bit 20 set | Desync | W | N/A | Bit 20 set | Returns `fabric_config` to idle, sets `Configured`, ends configuration |
| Bitbang control `0xFAB1` / `0xFAB0` | Bitbang on/off | W | N/A | 16-bit control word shifted on `s_clk` falling edges | `0xFAB1` latches the 32 data bits shifted on rising edges as one word; `0xFAB0` releases the port |
| SPI word | SPI data | W | N/A | 32 bits shifted in on `spi_sck` rising edges while `spi_cs_n` is low | Each complete word enters the stream |

Because of the FABulous header `00AAFF01000000010000000000000000FAB0FAB1`, a `.bit` file loads unchanged over UART in binary mode or word by word over bitbang or SPI.

### 2.5 Clocks and Resets

`CLK` clocks the configuration logic only and is constrained at 10 ns (100 MHz, `fabric.frequency_mhz` in `Fabric/ecc_config.toml`). The UART divisor `ComRate` keeps its default 217, set for 115,200 baud at 25 MHz, so at 100 MHz the UART runs at 458,716 baud and needs `ComRate` = 867 for 115,200. Bitbang and SPI are independent of the `CLK` frequency.

With `DisableUserCLK` set in `fabric.csv` the fabric has no clock port, so the user clock enters on the `SYS_RESET_RESET_top` pad. Its `SYS_RESET` BEL in `SW_term` drives only the four `GBUF` inputs, which fabric routing can also reach through the `S_term` and `W_term` feed wires, giving up to four global nets. Each `GBUF` drives `E_GBUF` wires along the bottom row and `N_GBUF` wires up every column, buffered at every tile hop. The user-mode clock frequency is unmeasured.

Minimum reset duration, reset release requirements and power-up sequencing are not specified. [to be taken from `fabric_config` and the MPW board's reset circuit].

![Clock and reset timing](images/clock_reset_timing.png)

![Reset release](images/reset_release.png)

**Figure 2-4. Bitstream simulation (Figure 5-2 VCD). Top, 0 to 524.5 ms, `frame_strobe` pulses while `config_busy` is high until `configured` rises (Section 5.3). Bottom, 0 to 40 µs, `resetn` low from 100 ps to 1.5 µs, `configured` leaves X at 0.5 µs, `spi_cs_n` falls at 22 µs and `spi_sck` starts at 28 µs.**

### 2.6 Device Programming

Programming will reuse the bring-up flow of the wafer.space gf180mcu FABulous FPGA, `github.com/mole99/wsrun1-fpga-bringup` (`81a9a99`, Apache-2.0), once the MPW package and test board are known. That flow compiles with Yosys `synth_fabulous`, `nextpnr-generic --uarch fabulous` and the FABulous bitstream generator, then loads from an RP2040 Raspberry Pi Pico on MicroPython. Its `Makefile` flow, bitstream format, Pico file layout and test designs (`counter`, `passthrough`, `all_ones`, `all_zeros`) carry over. The protocol is unchanged.

| Part replaced | Replacement for this fabric |
|---|---|
| nextpnr model and bitstream specification | `fabrics/nobram/.FABulous/` (`pips.txt`, `bel.v3.txt`, `bitStreamSpec.bin`) |
| IO constraints (written) | `fabrics/nobram/user_design/pads.pcf` on the 10 `IOBUF` BELs, `iobuf_map.v` for the `-iopad` cells, clock through `SYS_RESET` at `X0Y11.E` into a `GBUF` as in `top_wrapper.v` |
| Techmaps | Without the register-file and SRAM mappings |
| Pico upload pins | `spi_cs_n`, `spi_sck`, `spi_mosi`, with `ConfigBusy` and `Configured` as status, in place of gf180's `FPGA_MODE`, `FPGA_BUSY`, `CS_N`, `SCLK`, `MOSI` |
| Pico pin assignment | Depends on the MPW test board |

## 3. Design Targets and Results

### 3.1 Functional Metrics

| Metric | Target | Latest result | Measurement or verification method |
|---|---:|---:|---|
| Logic cells | 800 | 800 | Physical: 100 `LUT4x8_ha` × 8 |
| Multiply-accumulate blocks | 5 | 5 | Physical: 5 `MACC` supertiles |
| User IO | 10 | 10 | RTL: `A_*_top[9:0]` |
| Global clocks | 4 | 4 | RTL: `GBUF_A` to `GBUF_D` in `SW_term` |
| Seam connectivity | all declared links meet | 31,760 of 31,760 links over 282 seams | `task check` on `build/nobram/fabric_plan.json`. The `eFPGA_top` netlist counts 32,404 tile-to-tile nets. Its difference from the 31,760 plan links is not yet reconciled. |
| Configuration reaches every row | all 12 rows | 384 of 384 `FrameData` and 260 of 260 `FrameStrobe` bits routed | Routed DEF. Simulation shows rows 1 to 8 and 11 configured (Section 5.3). No simulated design observes row 0. |
| User design on the fabric | runs a test design | 100 of 100 cycles match on all 10 IO bits | Section 5.3 |

### 3.2 Performance, Resource, and Power Metrics

| Metric | Target | Latest result | Conditions |
|---|---:|---:|---|
| Configuration clock | 100 MHz | Met at all corners; worst setup slack +6.853 ns at 10 ns | Full-chip OpenSTA, ss 1.08 V 125 °C, Cworst SPEF (Section 6.3) |
| User-mode operating frequency | [Target] | Pending, unmeasured | No routed user design has been timed (Section 6.3) |
| Processing latency | Not applicable | Not applicable | Set by the configured user design |
| Throughput | Not applicable | Not applicable | Set by the configured user design |
| Standard-cell count/area | ≤ 1 mm² footprint | 911,687 µm² `eFPGA_top`; synthesis 179,692 cells, 683,670 µm² | Breakdown in Sections 6.1 and 6.2 |
| SRAM/ROM/macro resources | none | none | No hard macro in this variant |
| Power | Not applicable | Not reported | Not assessed for this submission |

## 4. IP Reuse and Standardization

### 4.1 Reuse Objectives and Use Cases

- [ ] Shared infrastructure within an MPC, or a reusable module for designs submitted through an MPW shuttle, such as standard I/O, clock and reset, configuration, test, or bus-connectivity logic.
- [ ] An interface controller between a user design, shared platform infrastructure, and chip-level I/O, providing protocol conversion, register access, or control functions.
- [x] A standalone digital IP block, hard macro, logic tile, programmable fabric, accelerator, processor, or peripheral.
- [ ] A design intended only for validation in this tapeout, with no current plan for reuse across projects.

Another project can take the hardened `eFPGA_top`, the abutted `eFPGA` array with its own controller or the 12 tile types abutted into a different grid (interface in Section 4.4). A new grid in `fabrics/<variant>/fabric.csv` keeps one width per column and one height per row. It needs `eFPGA.v` and each `io_pin_order.yaml` regenerated through FABulous and the Section 4.6 flow re-run, but no tile re-hardened unless a die changes.

### 4.2 Supported Reuse Levels

| Reuse level | Supported? | Deliverables or limitations |
|---|---|---|
| RTL-level reuse | Yes | `fabrics/nobram/Fabric/`, `Tile/`, `primitives/`. Regenerating the Verilog byte-identically needs FABulous `c0ca476` (`user-clk-attr`), while `io_pin_order.yaml` needs `092f606` (`fix-direction`). Neither checkout produces both. |
| Post-synthesis netlist reuse | Yes, per tile and for `eFPGA_top` | `build/nobram/tiles/<type>/`, `build/nobram/top/` |
| Hard-macro reuse | Per tile and `eFPGA_top` | Per tile abstract LEF, extracted Liberty, routed DEF, SPEF at six RC corners and abstract GDS. `eFPGA_top` routed DEF, netlist and SPEF at nine RC corners, plus ECC Harden's abstract LEF (999.000 × 912.600 µm, 45 pins including the two supplies), ss 125 °C 1.08 V Liberty with 2 timing arcs and pin/OBS GDS in `build/nobram/top/default/Harden_ecc/output/` |
| Tile/fabric-level reuse | Yes | `build/nobram/fabric_plan.json` holds every die, pin offset and seam |
| MPW top-level integration | Partly | No pad ring, seal ring or chip-level GDS |

### 4.3 IP Baseline Specification

| Category | Required information |
|---|---|
| Process environment | As in Submission Information, technology LEF `N551P6M_ecos.lef`. ECC STA runs 13 corners over tt 1.2 V 25 °C, ss 1.08 V and ff 1.32 V at 125 °C and −40 °C. |
| Physical dimensions | Section 6.2; array aspect 1.07. Tile edges lie on the 0.2 µm `core7` site and the 2.8 µm row grid. |
| Resource capacity | 800 `FABULOUS_LC`, 1,110 tile flip-flops, 5 `MACC_8x8_20`, 4 `GBUF`, 10 IO, no SRAM, ROM or PLL |
| Clocks and resets | Section 2.5 |
| Functional interfaces | Section 2.3 |
| I/O and pins | 43 signal and two supply pins mapped to 27 pads (Section 2.3). No pad ring, ESD cell or package pins; `IOBUF` is logic-level. Tile east and west pins on MET3 at 0.6 µm minimum pitch, north and south on MET4 at 0.4 µm, on the 0.2 µm track grid, ordered by each tile's `io_pin_order.yaml`. |
| Power and PDN | `VDD` and `VSS`, nominal 1.2 V. Per tile MET1 follow-pin rails, MET4 vertical and MET5 horizontal stripes, VDD and VSS alternating every 8.4 µm to the die edge, joined by abutment. `eFPGA_top` adds PDN only over the channel and strip (113 strip and 6 channel MET4 stripes, 3 strip and 104 channel MET5 stripes, 650 MET1 rails). |
| Physical constraints | MET1 to MET5; the top run blocks routing over the array. Orientation R0 only. No DRC or antenna waivers claimed. |
| Metrics and operating conditions | Section 3.2 |
| Portability | ICS55-specific are the netlists, the tile dies and `techmap/ics55_models.v`; the RTL and `fabric.csv` are PDK-independent |

### 4.4 Standard Interfaces and Integration

1. A user design reaches the fabric through its 10 IO bits. The fabric is configured from a host over SPI, UART or bitbang, not through a bus.
2. Not applicable, since the fabric is not an interface controller. All loaders sample their inputs, `s_clk` and `spi_sck` included, on `CLK`.
3. The top level provides `CLK`, `resetn`, at least one loader, the 10 IO bits and a user clock on `SYS_RESET_RESET_top`. Unused loader inputs are tied to their idle level.
4. Used as a block, `eFPGA_top` fixes its die, its 43 pin positions and its power stripes. Re-abutted tiles fix every die, edge pin order and offset, the signal layers (MET3 east and west, MET4 north and south), the PDN layers and the stripe positions. `flow check` refuses a plan where any link does not meet.

### 4.5 Reusable Deliverables

| Deliverable | Required? | Requirements |
|---|---|---|
| RTL and/or netlist | Yes | RTL at `f82fb9a`; netlists as in Section 4.2 |
| Constraint files | Yes | `build/nobram/top/top.sdc`; tile SDC is ECC-generated. `Fabric/ecc_config.toml`, `Tile/include/ecc_config.toml` and `Tile/<type>/ecc_config.toml` hold every floorplan and placement setting. |
| Synthesis and physical implementation scripts | When applicable | `flow/` (with `repair_tile.tcl`, `repair_top.tcl`), `Taskfile.yml`, `techmap/ics55_models.v` |
| Physical views | When applicable | Section 4.2; `eFPGA_top` filler DEF in `build/nobram/top/default/filler_ecc/output/`, SPEF in `RCX_ecc/output/`. Mask-layer GDS of `SE_term` only (Section 7). |
| I/O pin-placement file | When applicable | `Tile/<type>/io_pin_order.yaml` for edge order; `build/nobram/fabric_plan.json` for coordinates |
| PDN configuration | When applicable | `Fabric/ecc_config.toml`; `flow/integrate.py` draws the top's channel and strip PDN |
| Verification environment | Yes | Section 5.1; testbench `fabrics/nobram/user_design/sequential_16bit_en_tb.v`, cocotb tests in `Test/config/`, STA in `flow/sta/` |
| Example project | Recommended | `fabrics/nobram/user_design/sequential_16bit_en.v` with its testbench |
| Documentation | Yes | `README.md`, `SPEC.md` |
| License and third-party inventory | Yes | Section 11.2. The repository has no top-level licence file. |

### 4.6 Single Entry Point and Reproducibility

The build runs as five stages, each stopping at the first failure.

    task plan VARIANT=nobram        # size every tile and place every pin, writes build/nobram/fabric_plan.json
    task check VARIANT=nobram       # test the plan's wiring properties, no EDA tool
    task harden VARIANT=nobram      # one ECC run per tile type, synthesis to macro
    python3 -m flow.cli --variant nobram integrate   # harden eFPGA_top around the fixed tiles
    flow/sta/prepare.sh build/nobram pdk && flow/sta/run.sh build/nobram pdk   # full-chip OpenSTA, six corners

| Stage | Run time |
|---|---|
| `task harden`, all 12 tile types (2026-10-17) | [time] |
| `task harden`, three terminator types (2026-10-19) | 5 minutes at three jobs |
| `integrate` (2026-10-20) | 63 minutes, 58 of them from RCX through Harden |
| Full-chip OpenSTA | about 8.5 minutes and 2.7 GB per corner |

Logs go to `build/nobram/logs/`. A clean checkout does not yet reproduce the build, for five reasons.

1. ECC `main` at `14be467` needs two uncommitted edits, a Nix flake override for boost and a `YOSYS_TECHMAP_FILES` block in `yosys_synthesis.tcl` (ecc#302).
2. RTL and pin orders need the two FABulous checkouts of Section 4.2.
3. The PDK liberty and GDS come from a GitHub release fetched by `make` in `pdk/`.
4. The bitstream simulation needs Yosys 0.62 (Section 5.1).
5. The gitignored `fabrics/nobram/.FABulous/` (`pips.txt`, `bel.v2.txt`, `bitStreamSpec.bin`) is regenerated by FABulous `c0ca476` with `load_fabric`, `gen_model_npnr` and `gen_bitStream_spec`.

### 4.7 Reuse Acceptance Criteria

| Acceptance item | Passing criteria | Result |
|---|---|---|
| Environment reproducibility | The applicable build, verification, or export flow completes in the specified environment, and all versions and dependencies are traceable | Pending verification, with the five gaps of Section 4.6 open |
| Functional verification | Basic tests and regression tests pass | Pass for basic tests (Section 5.3); no regression suite exists |
| Timing closure | The target frequency is met; otherwise, the failing paths and their impact are documented | `CLK` passes at 100 MHz in all six corners. User-clock hold is met and its Fmax unmeasured. Slew, capacitance and pulse width have 0 violations (Section 6.3). |
| Physical verification/signoff | DRC, LVS, antenna, and PDN checks meet the project requirements; all remaining violations and approved waivers are documented | Pass per tile and on `eFPGA_top` signal nets. The top has 278 power opens and antenna is not run (Section 6.3). All checks run on ECC abstracts, not mask GDS. |
| Physical interface conformance | Dimensions, pin locations, metal layers, coordinates, and PDN match the baseline specification | Pass. All 151 tiles sit fixed at their planned coordinates in the `eFPGA_top` DEF. Every tile reports all pins held at their planned position. |
| Reference integration | The IP can be instantiated and connected in the minimal example project | Pending verification, as no pad ring or chip top exists |
| Documentation and licensing | Documentation, version information, licenses, and third-party dependency records are complete | Pending verification, as no project licence file exists |

### 4.8 Versioning, Compatibility, and Maintenance

Changing a tile die, an edge pin order, the signal or PDN layers or the stripe pitch breaks abutment and increments the major version. A grid change alone affects only the fabric and top views. The current v3.0 (`f82fb9a`) replaced 30 IO tiles with terminators. Later drive and repair changes re-hardened five tile types on unchanged dies and pins. Known issues are in Section 11.1, planned work is in Section 10.3 and the maintainer is King Lok (Kelvin) Chung.

## 5. Design Verification

### 5.1 Verification Environment

| Check | Tool | What it checks |
|---|---|---|
| Plan wiring | `task check`, no EDA tool | Every seam link declared in `Fabric/eFPGA.v` meets at one coordinate on both tiles |
| Per-tile signoff | ECC | iEDA DRC, iLVS of routed DEF connectivity against the netlist, 13-corner iSTA |
| `eFPGA_top` signoff | ECC | The same checks, after refusing any tile whose LEF pins differ from the netlist ports and fixing all 151 tiles at their planned coordinates |
| Full-chip STA | OpenSTA, six corners | `eFPGA_top` netlist written from the filler DEF (the only view with the tile-to-tile nets), the 12 tile netlists and per-instance tile SPEF |
| Bitstream simulation | Yosys 0.62 `synth_fabulous`, `nextpnr-generic --uarch fabulous`, FABulous `bit_gen`, Icarus Verilog | `sequential_16bit_en` loaded into the `eFPGA_top` RTL over SPI, all 10 IO bits compared against the design simulated directly |
| Loader tests | cocotb 2.0.1 on Icarus, `Test/config/test_config_frontend.py` | A bitstream through each of the UART, bitbang, SPI and parallel loaders arrives in order. A 7-bit SPI fragment yields no word. |

The bitstream simulation runs as `task VARIANT=nobram WAVEFORM_TYPE=vcd YOSYS_PATH=<yosys 0.62> build-test-design run-simulation` in `Test/`. It shifts 4,096 words (the bitstream padded to `MAX_BITBYTES`) at 128 cycles per word, with `spi_sck` at a quarter of the 1 MHz clock, over 524,531 cycles. Its VCD (`+waveform_depth=1`) is 19.6 MB.

![Verification environment](images/verification_environment.png)

**Figure 5-1. Verification environment.**

### 5.2 Verification Scope and Methods

DRC and LVS are iEDA's checks on LEF abstracts and DEF connectivity. The streamed GDS of Section 7 has no mask-geometry check, because the PDK's decks in `pdk/pv/` are Calibre, unlicensed here, while `pdk/` holds no open deck (KLayout `.lydrc` or `.lylvs`, Magic tech file or netgen setup). Whether the MPW organisers run Calibre DRC and LVS on submitted GDS is unconfirmed. There are no random, formal, gate-level or FPGA-prototype tests.

### 5.3 Verification Results

| Test category | Test cases | Passed | Failed | Conclusion and open issues |
|---|---:|---:|---:|---|
| Plan wiring (`task check`) | 31,760 links | 31,760 | 0 | Every link meets at one coordinate |
| Per-tile DRC (iEDA) | 12 tile types | 12 | 0 | 0 violations each |
| Per-tile iLVS | 12 tile types | 12 | 0 | 0 opens, 0 shorts |
| `eFPGA_top` DRC (iEDA) | 1 | 1 | 0 | 0 violations |
| `eFPGA_top` iLVS | 3,189 nets, 16,666 instances | 3,189 | 0 | 43 of 43 IO, instances and nets match; 278 power opens (Section 6.3) |
| Full-chip STA (OpenSTA) | 6 corners | 6 | 0 | Section 6.3 |
| Antenna | 0 | 0 | 0 | Not run; the ECC flow reports no antenna result |
| Bitstream simulation | 1 design, 100 compared cycles | 1 | 0 | No compare error (2026-10-20, `f82fb9a`). `ConfigBusy` rose at 668.5 µs and `Configured` at 433,436.5 µs. The design uses 13 of 800 `FABULOUS_LC`, 10 of 10 `IOBUF` and 1 of 4 `GBUF`. `A_EN_top[9:2]` rising as the `E_IO` frames load and the counter running on `GBUF` A show rows 1 to 8 and 11 configured. Log in `submission/sim/results/bitstream_sim.log`. |
| cocotb loader tests | 4 loaders | 4 | 0 | 166 s, 2026-10-18 |

![Key simulation waveform](images/simulation_waveform.png)

**Figure 5-2. User mode at 524,423 to 524,450 µs in `build/figures/bitstream/sequential_16bit_en.vcd`. `pad_in` goes 0, 3 (reset), 2 (run), `A_IN_top` counts with `A_IN_top_gold` and `A_EN_top` equals the gold `3FC`.**

## 6. Synthesis and Physical Implementation Results

### 6.1 Synthesis Results

Tile figures are each tile type's unrounded result times its grid count. Top figures are the configuration logic, synthesised flat with tiles as black boxes. All runs map to `ss_rcworst_1p08_125` liberty through `techmap/ics55_models.v`. `LUT4x8_ha` uses ABC `AREA 5`, while `LUT4x8_ha`, `MACC` and `E_IO` bar X0P5 to X1 combinational drives from ABC.

| Item | Result | Tool/Version | Conditions |
|---|---:|---|---|
| Standard-cell count | 179,692 (177,163 in tiles, 2,529 at top) | Yosys 0.68 / ECC `14be467` | As above |
| Combinational cell count | 108,054 (106,307 in tiles, 1,747 at top) | Yosys 0.68 / ECC `14be467` | Total minus flip-flops and latches |
| Sequential cell count | 71,638 (70,856 in tiles, 782 at top) | Yosys 0.68 / ECC `14be467` | Tiles hold 1,110 flip-flops and 69,746 configuration latches, the top 782 flip-flops |
| Macro count | 151 tile macros at top, 0 hard IP | Yosys 0.68 / ECC `14be467` | No hard macro |
| Synthesized area | 683,670 µm² (674,731 in tiles, 8,939 at top) | Yosys 0.68 / ECC `14be467` | Cell area, of which configuration logic is 1.3% |
| Post-synthesis timing | Section 6.3 | ECC STA | Tile constraints time paths through the unconfigured switch matrix, not a user clock |

| Tile | Count | Cells | Area (µm²) | Flip-flops | Latches |
|---|---:|---:|---:|---:|---:|
| `LUT4x8_ha` | 100 | 1,514 | 5,847.5 | 8 | 614 |
| `MACC` | 5 | 2,806 | 10,083.9 | 56 | 830 |
| `E_IO` | 10 | 326 | 1,190.8 | 3 | 120 |
| `W_term` | 10 | 253 | 862.4 | 0 | 96 |
| `N_term` | 10 | 249 | 856.8 | 0 | 96 |
| `S_term` | 10 | 273 | 937.4 | 0 | 104 |
| `N_term_MACC` | 1 | 104 | 116.5 | 0 | 0 |
| `S_term_MACC` | 1 | 126 | 192.4 | 0 | 8 |
| `NW_term` | 1 | 114 | 147.8 | 0 | 4 |
| `NE_term` | 1 | 104 | 116.5 | 0 | 0 |
| `SW_term` | 1 | 157 | 358.4 | 0 | 20 |
| `SE_term` | 1 | 118 | 153.4 | 0 | 4 |
| Configuration logic (`eFPGA_top`) | 1 | 2,529 | 8,938.7 | 782 | 0 |
| Total | | 179,692 | 683,670 | 1,892 | 69,746 |

Without the `IOBUF` BEL each `W_term`, `N_term` and `S_term` has 3 fewer flip-flops and 16 fewer latches than its parent IO tile (Section 2.1). The table below splits the configuration logic by each cell's hierarchical prefix after flattening.

| Module | Block | Cells | Area (µm²) | Flip-flops |
|---|---|---:|---:|---:|
| `config_frontend` | `config_UART` loader | 759 | 2,519.7 | 192 |
| `config_frontend` | `config_spi` loader | 170 | 858.2 | 81 |
| `config_frontend` | `bitbang` loader | 112 | 599.8 | 58 |
| `config_frontend` | Priority multiplexer over the loaders, parallel input tied low | 220 | 622.4 | 34 |
| `fabric_config` | Frame FSM, header decode, row, frame and column select | 152 | 363.4 | 31 |
| `fabric_config` | `FrameData` register, 384 bits | 769 | 3,440.4 | 384 |
| `fabric_config` | `FrameStrobe` decode, 260 bits | 260 | 364.0 | 0 |
| `eFPGA_top` | Cells named after top-level ports (`Configured` 62, `ComActive` 19, `ConfigBusy` 4, `ReceiveLED` 2) | 87 | 170.8 | 2 |
| | Total | 2,529 | 8,938.7 | 782 |

The `config_frontend` loaders take 51% of the configuration logic area (1,261 cells, 4,600.1 µm²), the UART alone 28%. `fabric_config` takes at least 1,181 cells and 4,167.8 µm², 83% of it the `FrameData` register, plus FSM cells in the port-named row.

After routing the configuration logic is 3,150 cells and 12,020.7 µm². CTS adds 47 buffers (156.2 µm²). The OpenROAD repair adds 574 cells (260 frame-strobe buffers, the `resetn` buffer, 296 slew and capacitance buffers and 17 hold buffers) and resizes the 260 strobe drivers and 155 other cells.

### 6.2 Physical Implementation Results

| Item | Result | Notes |
|---|---:|---|
| Die dimensions | `eFPGA_top` 999.0 × 912.6 µm (911,687 µm²); array 947.0 × 884.8 µm (837,906 µm²) | Array frame from `build/nobram/fabric_plan.json`; the array covers 91.9% of the die |
| Core dimensions | `eFPGA_top` core 904,057 µm²; per tile, die minus 2 µm margin | `LUT4x8_ha` core 6,272.3 µm² |
| Core utilization | `eFPGA_top` 0.42 by ECC's count; tiles in the table below | Netlist cell area over core area, excluding fillers and tap cells |
| Instance count | 238,579 in the routed tiles over the grid; 16,666 at top level | Including physical cells; `LUT4x8_ha` 1,891 (1,524 logic) |
| Macro count | 151 tile macros, 0 hard IP | 100 `LUT4x8_ha`, 5 `MACC`, 10 `E_IO`, 30 edge terminators, 2 `MACC` terminators, 4 corners |
| Peak routing congestion | `LUT4x8_ha`: 81 layer-assignment overflows, 0 detailed-routing violations. `eFPGA_top`: 41,907 layer-assignment overflows, 2,013 detailed-routing violations reported by iRT | iDRC signoff reports 0 on `eFPGA_top` (Section 6.3). The origin of iRT's residual count is not yet identified. |
| Clock-tree synthesis (CTS) results | Top: 47 buffers, 3 to 4 per path, 829 clock sinks. Tiles: none | The fabric clock is the `GBUF` network (Section 2.5) |
| I/O pin placement | Meets macro-integration requirements | Tile pins from ECC's file-driven IO placer at `fabric_plan.json` offsets, all held; `eFPGA_top` 43 signal pins (30 user IO, 1 user clock, 12 configuration) and two supply pins |
| Power distribution network (PDN) | Meets requirements | Section 4.3 |

| Tile | Die (µm) | Instances | Core utilisation | Wire (µm) | Vias |
|---|---|---:|---:|---:|---:|
| `LUT4x8_ha` | 82.6 × 84.0 | 1,891 | 0.94 | 59,105 | 12,997 |
| `MACC` | 70.8 × 168.0 | 3,777 | 0.93 | 108,631 | 24,141 |
| `E_IO` | 21.4 × 84.0 | 586 | 0.86 | 11,638 | 2,394 |
| `W_term` | 28.8 × 84.0 | 914 | 0.44 | 9,226 | 1,470 |
| `N_term` | 82.6 × 22.4 | 640 | 0.60 | 8,608 | 1,559 |
| `S_term` | 82.6 × 22.4 | 705 | 0.66 | 9,589 | 1,800 |
| `N_term_MACC` | 70.8 × 22.4 | 494 | 0.10 | 6,329 | 520 |
| `S_term_MACC` | 70.8 × 22.4 | 528 | 0.16 | 7,032 | 745 |
| `NW_term` | 28.8 × 22.4 | 319 | 0.33 | 1,618 | 354 |
| `NE_term` | 21.4 × 22.4 | 282 | 0.37 | 1,247 | 302 |
| `SW_term` | 28.8 × 22.4 | 217 | 0.79 | 2,368 | 708 |
| `SE_term` | 21.4 × 22.4 | 304 | 0.48 | 1,459 | 374 |
| `eFPGA_top` configuration logic | 999.0 × 912.6 | 3,150 | 0.16 | 190,689 | 22,631 |

Values are from the filler step. The top's 0.16 utilisation is 12,020.7 µm² of routed logic over 73,782 µm² of die outside the array. Its 16,666 instances are 3,150 logic cells, 151 tile macros, 4,059 tap cells, 2,666 decap cells and 6,640 fillers.

![Floorplan and placement results](images/floorplan.png)

**Figure 6-1. Placed `eFPGA_top` cell outlines (KLayout 0.30.7, `build/nobram/top/default/place_dreamplace/output/eFPGA_top_place.gds`), with the configuration logic in the west channel and south strip.**

### 6.3 Signoff Results

Per-tile and `eFPGA_top` signoff come from ECC `14be467`, full-chip OpenSTA from `build/nobram/fullsta/` and per-tile OpenSTA from `build/sta-recheck-2026-10-21/`. A full-chip rerun from the main checkout on 2026-10-21 gave byte-identical logs at all six corners.

| Check | Status | Violation count | Disposition |
|---|---|---:|---|
| Setup timing, tiles (iSTA) | Fail | Worst corner 81 endpoints on `LUT4x8_ha` (WNS −14.924 ns) and 188 on `MACC` (WNS −65.706 ns), 0 on the other 10 types | Waived. The paths are combinational loops of up to 122 stages (`MACC`) through the unconfigured switch matrix and transparent configuration latches, which no configured design forms. OpenSTA breaks the loops differently and reports −14.337 and −67.463 ns at ss 125 °C Cworst. ECC's totals of 387 and 2,331 sum the 13 corners. |
| Hold timing, tiles (iSTA) | Fail | Every type, worst-corner WNS −0.456 to −0.500 ns. Worst corner 265 endpoints on `LUT4x8_ha` and 441 on `MACC` | The ECC SDC puts 0.5 ns uncertainty (5% of 10 ns) on an ideal clock, which every feedthrough under 0.5 ns and every flip-flop self-loop fails. The worst `LUT4x8_ha` path in OpenSTA is a 0.6 ps wire at −0.499 ns. With the full chip's 50 ps uncertainty the tile registers pass (table below). |
| Setup and hold, `eFPGA_top` alone (iSTA) | Pass, superseded | 0 | Setup +6.820 ns at ss 125 °C Cworst and hold +0.079 ns at ff −40 °C Cbest, against the ss-only tile Liberty (no hold arc) with no hold uncertainty. Full-chip OpenSTA replaces these figures and agrees on setup within 33 ps at the same endpoints. |
| Full-chip setup and hold (OpenSTA) | Pass | 0 | Table below |
| Minimum pulse width (OpenSTA) | Pass | 0 | All six corners, full chip and each tile type |
| Slew and capacitance (OpenSTA) | Pass | 0 | All six corners, full chip and each of the 12 tile types under its own SDC and SPEF, after the drive-buffer and repair steps below. iSTA's tile report writes both as a constant 0 (`TimingReporter.cpp`), so OpenSTA checks them. |
| DRC | Pass | 0 per tile; 0 on `eFPGA_top` | iEDA DRC on abstracts |
| LVS | Pass on signal, power opens on top | 0 per tile; 278 on `eFPGA_top` | iLVS of routed DEF connectivity against the netlist. On `eFPGA_top` 3,189 of 3,189 nets connect with 0 shorts. The 278 opens are 139 VDD and 139 VSS tile supply pins fed by abutment, which iLVS does not see. The check excludes the 32,404 tile-to-tile nets. |
| Antenna checks | Not run | N/A | The ECC flow reports no antenna result |
| Other checks | Pass, plan level | 0 | `task check`: 31,760 of 31,760 seam links meet |

Full-chip OpenSTA slack (ns, `flow/sta/run.sh`) times both clocks at 10 ns with 50 ps hold uncertainty (`HOLD_UNC`). The user clock starts at the `SW_term` GBUF A XOR with the GBUF A and `MACC` clock-inversion bits at 0. Its setup depends on the configured design and is not timed.

| Corner (liberty, SPEF) | `CLK` setup | `CLK` hold | User-clock hold, `LUT4x8_ha` | User-clock hold, IO | User-clock hold, `MACC` |
|---|---:|---:|---:|---:|---:|
| ff 1.32 V −40 °C, RCbest | +8.927 | +0.041 | +0.046 | +2.910 | +0.043 |
| ff 1.32 V −40 °C, Cbest | +8.968 | +0.038 | +0.044 | +2.752 | +0.042 |
| ff 1.32 V 125 °C, Cbest | +8.817 | +0.045 | +0.058 | +3.138 | +0.052 |
| ff 1.08 V 125 °C, RCbest | +8.350 | +0.086 | +0.102 | +4.515 | +0.097 |
| ss 1.08 V 125 °C, Cworst | +6.853 | +0.199 | +0.229 | +9.493 | +0.220 |
| ss 1.08 V −40 °C, Cworst | +6.927 | +0.192 | +0.215 | +9.074 | +0.204 |

All 1,110 user-clock flip-flops (800 in the logic cells, 280 in `MACC`, 30 in `E_IO`) meet hold. IO hold slack is largest because every IO flip-flop sits in column 12, at the far end of the `E_GBUF` spine from `SW_term`.

Because ECC sizes no cell after ABC, the unrepaired build has between 38,729 and 47,332 slew and capacitance violations per corner. Drive buffers in `techmap/ics55_models.v` and OpenROAD repair before routing (`flow/repair_tile.tcl`, `flow/repair_top.tcl`) clear them. The table splits the 47,332 at ss 125 °C Cworst by source, with repair counts against the placement-stage wire estimate.

| Source | Violations | Fix |
|---|---:|---|
| `LUT4x8_ha` (100 tiles) | 35,185 | `BUFX8H7L` per `FABULOUS_LC` output (about 40 switch-matrix loads, 0.09 to 0.10 pF); `repair_design`, 30 to 0 |
| `MACC` | 8,690 | `BUFX8H7L` per Q bit, `BUFX4H7L` enable and reset copies, `BUFX5H7L` strobes; driver upsizing against 1.5 times estimated wire capacitance, 156 to 0 |
| `S_term` frame strobes | 1,153 | `BUFX5H7L` per strobe |
| Configuration logic | 1,821 | `NOR2BX6H7L` strobe drivers with a `BUFX12H7L` per tile pin (iRT detours of 100 to 1,000 µm against a 3 µm estimate), `resetn` buffer for 364 loads, `repair_design` and `repair_timing -hold`, 1,967 to 0 |
| `E_IO`, `S_term_MACC`, `SW_term` | 483 | Techmap drive buffers |

The repair also raises `CLK` setup slack at ss 125 °C Cworst from +1.969 to +6.853 ns. It cuts the arrival of the worst path, `ComActive_reg_p` to `frame_data_143__reg_p`, from 8.344 to 3.510 ns by fixing one `NOR2X1P4H7L` that drove 0.103 pF in a 3.570 ns stage.

## 7. Layout

The layout of record is `build/nobram/top/default/filler_ecc/output/eFPGA_top_filler.def.gz`, the only view carrying all 35,593 nets (3,189 routed, 32,404 tile-to-tile restored unrouted).

ECC's GDS is not mask data. It writes standard cells and tile macros as flat LEF abstracts, so in the top GDS `Master_N_term_MACC` is 549 shapes with no sub-cells. It numbers layers by their order in the tech LEF `pdk/prtech/techLEF/N551P6M.lef` (MET1 7/0, MET5 15/0), not by `pdk/techfile/icsprout55.layermap` (MET1 81/1).

Mask-layer GDS exists for `SE_term` only (Figure 7-3), from the KLayout script `build/gds-stream-2026-10-22/def2gds.py`. It maps the routed DEF through `icsprout55.layermap` and takes every cell from the PDK `ics55_LLSC_H7C{R,L}_M2.gds`, whose MET2 pins match the `_ecos` LEFs ECC routed against. On `SE_term` it resolves 304 of 304 placed cells to PDK layout, labels 116 of 116 pins and matches the DEF die. The script fails on any unmapped layer or empty cell. The other 11 tile types and `eFPGA_top` are not yet streamed out.

The GDS lacks a cell boundary, because the layermap has no entry for the LEF `OVERLAP` layer or the DEF outline and the foundry's boundary layer is unknown. It also lacks a pad ring of `ICSIOA_N55_3P3_1P6M1TM.gds` IO cells and a seal ring, which the PDK does not ship.

![Final layout](images/final_layout.png)

**Figure 7-1. Routed `eFPGA_top`, ECC render after filler insertion, with tiles drawn as LEF abstracts.**

![LUT4x8_ha routed layout](images/lut4x8_ha_layout.png)

**Figure 7-2. Routed `LUT4x8_ha` tile, 82.6 × 84.0 µm, ECC render at the STA step.**

![SE_term mask-layer GDS](images/se_term_mask_gds.png)

**Figure 7-3. `SE_term`, 21.4 × 22.4 µm, KLayout render of `build/gds-stream-2026-10-22/SE_term.gds` with PDK standard-cell layout on ICS55 layer numbers.**

## 8. Post-Silicon Test Plan

### 8.1 Test Setup

In the planned setup, pending MPW package and board information, a host builds bitstreams (Section 2.6) and a Pico loads them over SPI. The Pico also reads `ConfigBusy` and `Configured`, supplies the user clock, holds `resetn` and samples the IO bits.

[Power supplies, clock source for `CLK`, probes and board connections, pending the MPW board.]

![Post-silicon test setup](images/silicon_test_setup.png)

**Figure 8-1. Planned post-silicon test setup.**

### 8.2 Test Procedures and Expected Results

| Test item | Procedure | Expected result | Passing criteria |
|---|---|---|---|
| Power-up and reset | Apply supply, hold `resetn` low, release | `ConfigBusy` and `Configured` low, IO outputs as the unconfigured fabric leaves them | [Criteria] |
| Basic functionality | Load a counter bitstream over SPI, clock it through the `SYS_RESET` pad | `ConfigBusy` high during the load, `Configured` high after it; counter value on the IO bits | Output matches the simulated design cycle for cycle |
| Boundary conditions | Load a design that uses all 5 `MACC` and the carry chain across a full column | Products and sums match the reference model | [Criteria] |
| Partial reconfiguration | Load a counter, then rewrite the frames of one column while the counter runs elsewhere | The untouched region keeps counting; the rewritten region takes its new function | [Criteria] |
| Frequency/voltage sweep | Raise the user clock until the counter fails, at several supplies | Pending: no Fmax prediction exists | [Criteria] |

## 9. Open-Source Contribution

### 9.1 Motivation for Participating in the Open-Source Tapeout Program

[Describe your motivation, the design idea you intend to validate, and why you chose the open-source community tapeout program.]

### 9.2 Artifacts to Be Released

| Artifact | Will it be released? | Planned release date | Notes |
|---|---|---|---|
| RTL/netlist | Yes | [YYYY-MM-DD] | FABulous RTL, configuration logic, per-tile and `eFPGA_top` netlists |
| Verification environment and test vectors | Yes | [YYYY-MM-DD] | `flow` checks, full-chip STA scripts, bitstream testbench, cocotb loader tests |
| Software, drivers, or reference models | Yes | [YYYY-MM-DD] | FABulous toolchain is upstream |
| Physical data such as LEF/DEF/GDSII/OASIS | Yes | [YYYY-MM-DD] | Tile LEF, Liberty, DEF and SPEF, `eFPGA_top` DEF and SPEF; mask-layer GDS once every tile and the top are streamed out |
| Tool scripts and configuration | Yes | [YYYY-MM-DD] | `flow/`, `Taskfile.yml`, `ecc_config.toml` files |
| Post-silicon measurement data | Yes | After bring-up | Published as it is taken; none exists before silicon returns |
| Documentation and tutorials | Yes | [YYYY-MM-DD] | `README.md`, `SPEC.md` |

### 9.3 Value to the Open-Source Community

To the best of the authors' knowledge, this project is the first fully open FPGA taped out on the open ICS55 55 nm process. Every layer of it is open. FABulous generates the fabric, the tiles come from the open fabulous-tiles library, and ECC synthesises, places, routes and signs off every tile and the top level on the open ECOS PDK. The project fills a gap in the open 55 nm ecosystem and adds a complete, verified programmable-logic example to the open-source chip ecosystem built around the ECOS platform.

The project provides reusable IP for this process node. The 12 hardened tile types have frozen dies, fixed pin orders and a PDN that joins by abutment. A later project can take the hardened `eFPGA_top` as one block, or re-abut the same tiles into a fabric of the size its own die allows without hardening anything again. The baseline specification, deliverables and acceptance status that make this reuse possible are set out in Sections 4.3, 4.5 and 4.7.

On this chip an MPW user's logic is fixed by a bitstream rather than by the masks. Logic mapped onto the 800 logic cells, 5 `MACC_8x8_20` blocks and 10 IO bits is corrected or replaced after fabrication by loading a new bitstream. A partial bitstream rewrites only the frames being changed while the rest of the fabric keeps running (Section 2.2). A research group can use the fabric as delivered for an experimental accelerator, an instrument or sensor interface or a teaching platform, or generate a fabric sized for its own application from the same open flow on ICS55.

By opening the complete path from fabric generation to signed-off layout, the project makes chip design accessible to more universities, research teams and individual developers. It supports open sharing, collaborative development and self-directed innovation across the open-source chip ecosystem at 55 nm.

#### 9.3（中文版）开源社区价值

据我们所知，本项目是首个在开放的 ICS55 55 纳米工艺上流片的全开源 FPGA。项目从架构到版图全链条开源：FPGA 架构由 FABulous 生成，逻辑单元（tile）来自开源的 fabulous-tiles 库，每一种 tile 以及顶层均在开源的 ECOS PDK 上由 ECC 完成综合、布局、布线与签核。本项目填补了开放 55 纳米工艺生态在可编程逻辑方面的空白，为以 ECOS 平台为核心的开源芯片生态贡献了一个完整且经过验证的可编程逻辑实例。

本项目为该工艺节点提供可复用的 IP。12 种已完成物理实现的 tile 具有固定的尺寸和引脚顺序，其供电网络通过拼接（abutment）即可直接连通。后续项目既可以将已完成物理实现的 `eFPGA_top` 作为一个整体模块直接集成，也可以根据自身芯片面积，将同一套 tile 重新拼接为不同规模的 FPGA，无需重新进行物理实现。支撑上述复用的基线规格、交付物与验收情况详见第 4.3、4.5 和 4.7 节。

在本芯片上，MPW 用户的逻辑由比特流而非掩模决定。映射到 800 个逻辑单元、5 个 `MACC_8x8_20` 模块和 10 个 IO 位上的逻辑，在芯片制造完成后仍可通过加载新的比特流进行修正或替换。部分比特流可以在其余逻辑持续运行的同时，仅重写需要修改的帧（见第 2.2 节）。研究团队既可以直接使用本 FPGA 开发实验性加速器、仪器或传感器接口以及教学平台，也可以基于同一套开源流程，在 ICS55 上生成面向自身应用规模的定制 FPGA。

通过开放从 FPGA 架构生成到签核版图的完整链路，本项目让更多高校、科研团队和个人开发者能够参与芯片设计，助力 55 纳米开源芯片生态的开放共享、协同发展与自主创新。

### 9.4 Suggestions for the Platform and Flow

1. A hook for a user techmap before ECC's `flatten` (ecc#302), so FABulous `my_buf` buffers survive as cells.
2. A tagged ECC release with the file-driven IO placer (`io_placer.mode = "file"`), which is on `main` only and not on `v0.1.0-alpha.12`.
3. Harden outputs with the routed layout and port timing, in place of the LEF-abstract GDS and 2-arc timing model ECC writes for `eFPGA_top`.
4. A way to mark abutment-connected nets in iRT. On the 122-tile `bram` fabric 27,390 such nets grew the shape database to 49 GB before routing.
5. A flag to stream full standard-cell layouts into iEDA's GDS, which now holds LEF abstracts.
6. Escaping of `$` in iRCX SPEF and netlist names, which OpenSTA rejects.
7. Public MPW die-size, pad-ring and seal-ring rules, with a seal ring in the PDK.

## 10. Lessons Learned and Future Work (Optional)

### 10.1 Lessons from Design and Verification

Plan checks belong before hardening. `task check` and the stale-die guard in `harden` reject a broken or stale plan in seconds rather than after a full harden.

Dense tiles route only with DreamPlace detailed placement and area-driven synthesis. At 0.93 core utilisation `LUT4x8_ha` oscillated between 2,134 and 2,643 violations over nine detailed-routing iterations without detailed placement and fell through 687, 72, 21 and 3 to 0 with it. ABC `AREA 5` gives 5,817.0 µm² against 5,882.0 µm² for the default `DELAY 4` (2026-09, earlier toolchain), enough for the 82.6 µm die to route clean.

A global clock that crosses abutted tiles needs full-chip STA with per-instance tile SPEF, since per-tile STA sees each tile's `GBUF` feedthrough as a wire. Unbuffered, each global clock was one net of fanout 345 driven by one XOR. The design therefore has one buffer per tile hop. Drive strength likewise needs post-placement repair, because ECC sizes cells only in synthesis (Section 6.3).

### 10.2 Physical Implementation Issues

1. **LUT column width.** `LUT4x8_ha` routes at 82.6 µm but not at 81.8 µm, where placement reaches 0.9888 of the placeable area and three DRC violations remain after nine detailed-routing iterations.
2. **Boundary buffers.** ECC synthesis flattens every FABulous `my_buf` into a net alias. A techmap onto `BUFX1H7L`, with a mux map onto `MUX4X1H7L` and `MUX2X1H7L`, keeps the 288 buffers per tile for about 1% of cell area through an uncommitted ECC edit.
3. **Top-level routing.** The tile-to-tile nets connect by geometry only in the DEF. A planned alternative separates the tiles by a 1.4 µm gap with one straight pre-routed wire per seam net and bridged power stripes. On the upper half of the double-height `MACC` this needs a re-harden at 168 µm plus the gap or iRT jogs on those nets.
4. **Global placement on the top.** Legalise-only placement piles every standard cell into one corner. Global placement converges only with `place.target_overflow = 0.15`.
5. **Timing.** No user-mode clock path has been timed (Section 6.3).

### 10.3 Planned Improvements

The next revision targets a mask-ready GDS with the pad ring and seal ring, a partial-reconfiguration simulation, `ComRate` matched to the 100 MHz `CLK` and a routed user design timed across the tiles' extracted Liberty, all on an ECC build with no uncommitted edits.

## 11. Additional Information

### 11.1 Known Limitations

- User-mode Fmax is unmeasured. The tile-level `sta_frequency_mhz` 40 on `LUT4x8_ha` reflects a loop through the unconfigured switch matrix.
- Only `GBUF` A is shown to work. A counter clocked through `GBUF` C stays X in RTL simulation although nextpnr routes the clock to every flip-flop, for a reason not yet found. `GBUF` B and D are untested.
- Simulation is RTL only, with no gate-level or partial-reconfiguration run.
- `ComRate` = 217 is mismatched to the 100 MHz `CLK` (Section 2.5).
- Mask-layer GDS for `SE_term` only, with no cell boundary layer, pad ring or seal ring. The PDK's Calibre decks have not been run and no open deck exists (Sections 5.2 and 7).
- 10 user IO bits in total, all in column 12.
- Row 0 configuration is shown only by routed nets, not in simulation.
- The `eFPGA_top` Liberty holds 2 timing arcs for 43 pins.
- 278 power opens in `eFPGA_top` iLVS (Section 6.3).
- No block RAM or multi-port storage. `FABULOUS_LC` has no LUT RAM because only the configuration chain writes its truth table.
- A plain `git archive` of the branch ships three primitives this variant does not instantiate (`ICS55_SRAM_512x32_1RW` with its vendor Liberty, `IHP_SRAM_1024x32_1RW`, `RAM_32x4_2R_1W`), so they must be stripped before release.
- Device programming and the post-silicon setup are plans (Sections 2.6 and 8.1).

### 11.2 Open-Source Projects, Third-Party IP, and Licenses

| Name | Purpose | Source/Repository | Version | License | Modified? |
|---|---|---|---|---|---|
| FABulous | Fabric generator, RTL and pin-order generation | `github.com/FPGA-Research/FABulous` | `c0ca476` (`user-clk-attr`), `092f606` (`fix-direction`) | Apache-2.0 | [Yes/No] |
| fabulous-tiles, classic library | Tile definitions and switch matrices | `github.com/FPGA-Research/fabulous-tiles` | `5809cdf` | [License] | Trimmed to the tiles used; `ecc_config.toml` added per tile |
| fabulous-fabrics `fabric_config` | Frame-based configuration FSM | [URL] | `7223ee9` | Apache-2.0 (SPDX header in `Fabric/fabric_config.sv`) | Vendored; front-ends added beside it |
| ECC (ECOS Chip Compiler) | Synthesis to routed macro per tile and for `eFPGA_top` | [URL] | `main` `14be467` | Apache-2.0 | Yes: two uncommitted edits (Section 4.6) |
| Yosys | Synthesis, inside ECC | `github.com/YosysHQ/yosys` | 0.68 `38e001a` | ISC | No |
| iEDA, DreamPlace | Placement, routing, DRC, iLVS, STA, inside ECC | [URL] | as bundled with ECC `14be467` | [License] | No |
| OpenSTA | Full-chip STA | `github.com/parallaxsw/OpenSTA` | [version] | GPL-3.0 | No |
| OpenROAD | Slew, capacitance and hold repair between legalisation and routing (Section 6.3) | `github.com/The-OpenROAD-Project/OpenROAD` | `dcf3613` | BSD-3-Clause | No |
| wsrun1-fpga-bringup | Planned bring-up flow and Pico loader | `github.com/mole99/wsrun1-fpga-bringup` | `81a9a99` | Apache-2.0 | Yes, planned (Section 2.6) |
| ICS55 ECOS PDK | Technology, standard cells and IO cells | `github.com/openecos-projects/icsprout55-pdk` | `v1.10.103` (`2d72857`) | Apache-2.0 (repository licence; cell-library terms to be confirmed) | No |
| This project | Flow, configuration, frozen dies | `github.com/KelvinChung2000/demo-ics55` | `f82fb9a` | [No licence file yet] | N/A |

### 11.3 Attachments and Deliverables

`submission/collect.py` rebuilds the self-contained appendix `submission/` from the working tree and `build/nobram/`, taking the RTL as the Yosys module closure of `eFPGA_top`. Table paths are relative to `submission/` and other paths to the repository root.

| File/Directory | Revision or commit | Purpose | Submitted? |
|---|---|---|---|
| `ECOS_Community_Tapeout_Project_Design_Report.md`, `images/` | this report | Report, figures and `.drawio` sources; the GTKWave and KLayout capture scripts for Figures 2-3, 2-4, 5-2 and 6-1 are in `capture/` | Yes |
| `rtl/` with `rtl/filelist.f` | `f82fb9a` | The 51 source files of `eFPGA_top` in Icarus compile order | Yes |
| `rtl/config/` | `f82fb9a` | `fabric.csv`, `dies.toml`, per-tile `io_pin_order.yaml` and `ecc_config.toml` | Yes |
| `sim/` | `f82fb9a` | Counter design, testbench, bitstream, Section 5.3 log, nextpnr model and bitstream specification (cocotb tests stay in `Test/config/`) | Yes |
| `physical/eFPGA_top/` | built from `f82fb9a` | Filler DEF, netlist, ECC GDS, SPEF at nine RC corners, Harden LEF, Liberty and GDS | Yes |
| `physical/tiles/<type>/` | built from `f82fb9a` | Filler DEF, netlist, ECC GDS, SPEF at nine RC corners, abstract LEF, extracted Liberty | Yes |
| `physical/fabric_plan.json` | built from `f82fb9a` | Dies, pin offsets, seams | Yes |
| `signoff/<block>/` | built from `f82fb9a` | ECC DRC, iLVS and iSTA summaries | Yes |
| `sta/` | built from `f82fb9a` | Full-chip OpenSTA scripts, logs, reports and `summary.txt` | Yes |
| `gl/` | built from `f82fb9a` | `top_full.v` with all seam nets and the 12 tile netlists, for a gate-level simulation not yet run | Yes |

Every appendix GDS is an ECC abstract (Section 7). The build flow and documentation stay in the repository.

## Pre-Submission Checklist

- [ ] Project name, project lead, contributors, repository URL, source revision (commit/tag), and process/PDK version are provided.
- [ ] Targets and measured results are clearly distinguished, with units, tool versions, and test conditions included.
- [ ] Top-level interfaces, clocks, resets, I/O, PDN, and physical boundaries are documented.
- [ ] If IP reuse is planned, the supported reuse levels, baseline specification, deliverables, and acceptance criteria are complete.
- [ ] If reuse is not currently supported, the reasons and future plans are documented.
- [ ] Simulation, synthesis, place-and-route, DRC/LVS, and other signoff results match the final submitted revision.
- [ ] Figures, source code, scripts, netlists, physical views, and licenses are archived according to the deliverables list.
- [ ] Known issues, waivers, and post-silicon test considerations are documented.
