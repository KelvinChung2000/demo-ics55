# FABulous eFPGA on ICS55, submission appendix

This directory is what the project submits to the OpenECOS MPW. `ECOS_Community_Tapeout_Project_Design_Report.md` is the report, and everything else here is its appendix: the RTL, the simulation set-up and results, the physical views, the signoff and STA reports and the inputs for a gate-level simulation. Section 11.3 of the report maps each directory to what it supports.

The design is `eFPGA_top`, a 13 × 12 tile FABulous fabric with 800 logic cells, 5 multiply-accumulate blocks and 10 user IO on its east edge, plus its configuration controller, hardened by ECC on ICS55 (PDK `v1.10.103`) from the RTL and pin plans of commit `20f8422`.

## Layout

| Directory | Contents |
|---|---|
| `images/` | Report figures and their `.drawio` sources. The waveform and floorplan figures are GTKWave and KLayout captures made by `capture/` |
| `rtl/` | The 52 source files of `eFPGA_top`; `rtl/filelist.f` lists them relative to this directory. `rtl/config/` holds the grid, dies, pin orders and ECC settings. |
| `fabric/` | The FABulous project of the fabric, with `fabric.csv`, `dies.toml`, `eFPGA_geometry.csv`, the 12 tile types with `Tile/common` and `Tile/include`, and the six primitives the fabric instantiates. Every path a tile file names resolves inside it. FABulous `c0ca476` (`user-clk-attr`) generated `Fabric/eFPGA.v`, `eFPGA_top.v` and the tile Verilog. The project's `.FABulous/` is left out, and its model files are in `test/fabulous_model/` |
| `physical/` | `eFPGA_top` and per-tile DEF, netlist, GDS, SPEF at nine RC corners, LEF and Liberty, and `fabric_plan.json` |
| `signoff/` | For `eFPGA_top` and each tile type, the ECC DRC count (`drc.json`) and per-layer table (`drc.csv`), the iLVS report (`lvs.rpt`) and the iSTA reports of every corner (`sta/<library corner>_<RC corner>/`) |
| `sta/` | Full-chip OpenSTA scripts, per-corner reports and `summary.txt` |
| `gl/` | Gate-level netlists, the inputs of the report's gate-level simulation |
| `chip/` | The pad-ring netlist `top.v` and `top.sdc`, the extracted `eFPGA_top` timing model and the chip-level OpenSTA log |
| `test/` | The verification harness and what it runs on. `Taskfile.yml` runs the RTL and gate-level simulations and the bitstream build on the files of this directory only. `user_design/` holds the counter design, testbench and PCF, `bitstream/` the submitted bitstream, `results/` the passing RTL and gate-level simulation logs, `fabulous_model/` the gzipped nextpnr model and bitstream specification, `yosys/` the FABulous primitives and technology maps Yosys 0.67 and newer need and `config/` the cocotb loader test |

Every GDS here holds standard cells and tile macros as LEF abstracts, so none of them is a mask-ready layout.

## Testing

Every test runs from `test/` and reads only files of this directory, so it checks exactly what is submitted. The gate-level simulations also need the ICS55 PDK, passed as `GL_PDK_ROOT`. The tools are [Task](https://taskfile.dev) and Icarus Verilog, plus cocotb 2.x and pytest for the cocotb test. Outputs go to `test/build/`.

The RTL bitstream simulation loads `test/bitstream/sequential_16bit_en.hex` over SPI, stopping at the end of the file, and compares the eight output pads, `A_IN_top[9:2]`, against the counter simulated directly. Pads 0 and 1 are the counter's `rst` and `en` inputs and are not compared; at the chip pads they read back what the testbench drives. `count` and `count_gold` in the testbench are the two counter values as one 8-bit signal each, for a waveform viewer. The run is 433,674 cycles and takes about six minutes. It passes when `test/build/bitstream_sim.log` ends in `$finish` rather than `$fatal`.

    cd test
    task run-simulation WAVEFORM_TYPE=vcd VVP_ARGS=+waveform_depth=1

`+waveform_depth=1` limits `test/build/sequential_16bit_en.vcd` to the testbench scope, about 16 MB. Without it the whole fabric is dumped, an estimated 21 GB for the SPI load, scaled from the 1 GB the 20,700-cycle parallel load gave. `task gtkwave WAVEFORM_TYPE=vcd` opens it.

The cocotb test drives each of the four configuration loaders in `rtl/Fabric/` and checks the word stream:

    cd test/config && python3 -m pytest test_config_frontend.py

A new user design goes through Yosys `synth_fabulous`, `nextpnr-generic --uarch fabulous` and FABulous `bit_gen`. `task build-test-design` runs all three into `test/build/`, with `test/fabulous_model/` gunzipped into `test/build/fabulous/.FABulous/` as the FABulous project root that nextpnr and `bit_gen` read. Synthesis runs on Yosys before and after the 0.67 rework of `synth_fabulous`. From 0.67 Yosys no longer bundles the FABulous primitives and technology maps, so `test/yosys/`, taken from FABulous PR #1085, supplies them; `run-yosys` passes that library when `synth_fabulous` accepts `-cells-map`, and `-iopad -complex-dff` otherwise. Yosys 0.62 rebuilds `bitstream/` byte for byte. Yosys 0.68 maps the counter onto the same 8 `LUTFF_ESR`, 10 `IOBUF` and 2 `GBUF` but places it differently, and that bitstream also passes the RTL and gate-level chip simulations. The simulations take the submitted bitstream unless given `BITSTREAM_HEX=build/<design>.hex`.

Pins are placed with a PCF. The design's top-level ports are the pads, `synth_fabulous` inserts a pad cell on each, `iobuf_map.v` turns those cells into this fabric's `IOBUF`, and nextpnr places each port where the PCF says. `test/user_design/pads.pcf`, written by `test/gen_pcf.py` from `rtl/`, lists all 10 pads as `set_io pad[i] X<x>Y<y>/A`, where `pad[i]` is the bit `eFPGA_top` exposes as `A_IN_top[i]`, `A_EN_top[i]` and `A_OUT_top[i]`; renaming `pad[i]` to one of your own ports places that port on pad `i`. `sequential_16bit_en_pcf.v` is the counter written this way, and builds and simulates from `test/` with:

    task WAVEFORM_TYPE=vcd VVP_ARGS=+waveform_depth=1 \
        TOP_WRAPPER=sequential_16bit_en_pcf \
        SYNTH_EXTRA_ARGS="-extra-map user_design/iobuf_map.v" \
        NEXTPNR_EXTRA_ARGS="-o pcf=user_design/pads.pcf" \
        BITSTREAM_HEX=build/sequential_16bit_en.hex \
        build-test-design run-simulation

A clock has to reach the fabric through a `GBUF`, so a design instantiates one on its clock pad as `sequential_16bit_en_pcf.v` does, pinned to `X0Y11.A`. A counter clocked through `GBUF` C stays X in RTL simulation, and `GBUF` B and D are untested. `top_wrapper.v`, with one `IOBUF` per pad and a `(* BEL *)` attribute on each, also builds and passes.

## Gate-level simulation

`gl/top_full.v.gz` is `eFPGA_top` written from the routed filler DEF. It is the only netlist that carries all 31,760 tile-to-tile nets and the 644 unconnected edge outputs, and it instantiates the 12 routed tile netlists in `gl/tile_*.v.gz`. The cell models are in the ICS55 PDK at `IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7C{R,L,H}/verilog/` and the pad model at `IP/IO/ICsprout_55LLULP1233_IO_251013/verilog/icsIOA_N55_3P3.v`.

    cd test
    task run-gl-chip GL_PDK_ROOT=<ICS55 PDK root>

`run-gl-chip` simulates these netlists inside `chip/top.v` with zero-delay cells (`-Dfunctional`), and `run-gl-top` simulates the bare macro. `test/gen_gl_top.py` writes the wrapper. It maps the 42 scalar netlist ports of `gl/top_full.v` back to the vectors of `rtl/eFPGA/eFPGA_top.v` and onto the pads of `chip/top.v`, and once `Configured` rises it forces each logic cell whose loaded configuration is constant to that constant. Section 5.3 of the report gives the reason and what the force masks. Each run takes about 4 minutes and passes 123 of 123 compares into `test/build/gl_chip_sim.log` or `gl_top_sim.log`, the logs `test/results/` holds. `VVP_ARGS="+waveform_depth=2 +output_waveform=build/gl_chip.fst -fst"` adds a waveform of the testbench, the pads and `eFPGA_top`; `+max_cycles=<n>` stops the run early.

## Rebuilding this directory

`python3 submission/collect.py` from the repository root replaces `rtl/`, `fabric/`, `physical/`, `signoff/`, `sta/`, `gl/`, `chip/` and `test/bitstream/`, `test/results/` and `test/fabulous_model/` from the working tree and `build/nobram/`. It takes the RTL as the module closure of `eFPGA_top` that Yosys resolves, so primitives the variant does not instantiate stay out. It takes the bitstream and the simulation logs from `test/build/`. The report, `images/`, the rest of `test/` and this file are edited by hand. `test/user_design/` is the design's only copy, and `fabrics/nobram/user_design` in the repository links to it.
