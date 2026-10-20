#!/usr/bin/env bash
# Rerun the Test/ bitstream simulation of sequential_16bit_en on eFPGA_top
# (nobram) with a VCD of the testbench and eFPGA_top scopes (depth 2).
# Needs Test/build/sequential_16bit_en.hex from `task build-test-design VARIANT=nobram`.
set -euo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT=$ROOT/build/figures/bitstream
UD=$ROOT/fabrics/nobram/user_design
mkdir -p "$OUT"
cp "$ROOT/Test/build/sequential_16bit_en.hex" "$OUT/"
task -d "$ROOT/Test" copy-files VARIANT=nobram BUILD_DIR="$OUT"
iverilog -g2012 -s sequential_16bit_en_tb -o "$OUT/sim.vvp" \
    "$OUT"/fabric_files/* "$UD/sequential_16bit_en.v" "$UD/sequential_16bit_en_tb.v"
cd "$OUT"
vvp sim.vvp +output_waveform="$OUT/sequential_16bit_en.vcd" +waveform_depth=2 \
    +bitstream_hex="$OUT/sequential_16bit_en.hex" | tee "$OUT/sim.log"
grep -q 'finish called' sim.log  # $fatal on mismatch never reaches $finish
