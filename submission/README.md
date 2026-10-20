# FABulous eFPGA on ICS55, submission appendix

This directory is what the project submits to the OpenECOS MPW. `ECOS_Community_Tapeout_Project_Design_Report.md` is the report, and everything else here is its appendix: the RTL, the simulation set-up and results, the physical views, the signoff and STA reports and the inputs for a gate-level simulation. Section 11.3 of the report maps each directory to what it supports.

The design is `eFPGA_top`, a 13 × 12 tile FABulous fabric with 800 logic cells, 5 multiply-accumulate blocks and 10 user IO on its east edge, plus its configuration controller, hardened by ECC on ICS55 (PDK `v1.10.103`) at commit `f82fb9a`.

## Layout

| Directory | Contents |
|---|---|
| `images/` | Report figures, their `.drawio` sources, and `waveforms.py` and `floorplan.py`, which draw the timing and floorplan figures |
| `rtl/` | The 51 source files of `eFPGA_top`; `rtl/filelist.f` lists them relative to this directory. `rtl/config/` holds the grid, dies, pin orders and ECC settings. |
| `sim/` | The counter test design and testbench, its prebuilt bitstream, the passing simulation log, and the nextpnr model and bitstream specification (`fabulous_model/`, gzipped) |
| `physical/` | `eFPGA_top` and per-tile DEF, netlist, GDS, SPEF at nine RC corners, LEF and Liberty, and `fabric_plan.json` |
| `signoff/` | ECC DRC, iLVS and iSTA summaries for `eFPGA_top` and each tile type |
| `sta/` | Full-chip OpenSTA scripts, per-corner reports and `summary.txt` |
| `gl/` | Gate-level netlists and the X-initialisation generator, not yet simulated |

Every GDS here holds standard cells and tile macros as LEF abstracts, so none of them is a mask-ready layout.

## Testing

The commands below run from this directory. They need Icarus Verilog; the cocotb test also needs cocotb 2.x and pytest.

The RTL bitstream simulation loads the prebuilt counter bitstream over SPI and compares all 10 IO bits against the counter simulated directly. The SPI load is 524,531 cycles and takes about seven minutes; the run passes when the log ends in `$finish` rather than `$fatal`.

    iverilog -g2012 -s sequential_16bit_en_tb -o sim.vvp -c rtl/filelist.f \
        sim/user_design/sequential_16bit_en.v sim/user_design/sequential_16bit_en_tb.v
    vvp sim.vvp +bitstream_hex=sim/bitstream/sequential_16bit_en.hex

Add `+output_waveform=sim.vcd +waveform_depth=1` for a waveform of the testbench scope, about 20 MB; without `+waveform_depth` the whole fabric is dumped, an estimated 25 GB for the SPI load, scaled from the 1 GB the 20,700-cycle parallel load gave.

The cocotb test drives each of the four configuration loaders and checks the word stream. It reads the loader RTL from `../Fabric/`, so it runs from a checkout of the full repository:

    cd ../Test/config && python3 -m pytest test_config_frontend.py

A new user design goes through Yosys `synth_fabulous`, `nextpnr-generic --uarch fabulous` and FABulous `bit_gen`, with `sim/fabulous_model/` gunzipped into the project's `.FABulous/`. Synthesis needs Yosys 0.62 or earlier: from 0.68 `synth_fabulous` maps LUTs and flip-flops only when given `-lut`, `-ff` and `-cells-map`, and the flow does not pass them.

Pins are placed with a PCF. The design's top-level ports are the pads, `-iopad` inserts a pad cell on each, `iobuf_map.v` turns those cells into this fabric's `IOBUF`, and nextpnr places each port where the PCF says. `sim/user_design/pads.pcf` lists all 10 pads as `set_io pad[i] X<x>Y<y>/A`, where `pad[i]` is the bit `eFPGA_top` exposes as `A_IN_top[i]`, `A_EN_top[i]` and `A_OUT_top[i]`; renaming `pad[i]` to one of your own ports places that port on pad `i`. `sequential_16bit_en_pcf.v` is the counter written this way, and from `Test/` in the repository it builds and simulates with:

    task VARIANT=nobram YOSYS_PATH=<yosys 0.62> WAVEFORM_TYPE=vcd \
        TOP_WRAPPER=sequential_16bit_en_pcf \
        SYNTH_EXTRA_ARGS="-iopad -extra-map ../fabrics/nobram/user_design/iobuf_map.v" \
        NEXTPNR_EXTRA_ARGS="-o pcf=../fabrics/nobram/user_design/pads.pcf" \
        build-test-design run-simulation

A clock has to reach the fabric through a `GBUF`, so a design instantiates one on its clock pad as `sequential_16bit_en_pcf.v` does, pinned to `X0Y11.A`. A counter clocked through `GBUF` C stays X in RTL simulation, and `GBUF` B and D are untested. The older route, `top_wrapper.v` with one `IOBUF` per pad and a `(* BEL *)` attribute on each, still builds and passes.

## Gate-level simulation, not yet run

`gl/top_full.v.gz` is `eFPGA_top` written from the routed filler DEF. It is the only netlist that carries all 32,404 tile-to-tile nets, and it instantiates the 12 routed tile netlists in `gl/tile_*.v.gz`. The cell models are in the ICS55 PDK at `IP/STD_cell/ics55_LLSC_H7C_V1p10C100/ics55_LLSC_H7C{R,L,H}/verilog/`.

Two pieces are missing before the testbench can drive it. `top_full.v` declares its 43 ports as scalars (`A_EN_top_0` and so on), so the vector ports the testbench connects need a wrapper. The configuration latches power up X, so `gl/gen_gl_xinit.py --pdk ics55` has to generate a `force_block.vh` that the testbench includes under `-DGL_SIM`. A zero-delay run (`-Dfunctional`) is the intended first step, since full-chip timing is covered by `sta/`. The run length is unknown; the RTL run spans 524,531 `CLK` cycles, almost all of them the SPI load.

## Rebuilding this directory

`python3 submission/collect.py` from the repository root replaces `rtl/`, `sim/`, `physical/`, `signoff/`, `sta/` and `gl/` from the working tree and `build/nobram/`. It takes the RTL as the module closure of `eFPGA_top` that Yosys resolves, so primitives the variant does not instantiate stay out. The report, `images/` and this file are edited by hand.
