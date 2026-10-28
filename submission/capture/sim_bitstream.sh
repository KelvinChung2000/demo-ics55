#!/usr/bin/env bash
# Rerun the submission/test bitstream simulation of sequential_16bit_en on eFPGA_top
# (nobram) with a VCD of the testbench and eFPGA_top scopes (depth 2).
set -euo pipefail
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT=$ROOT/build/figures/bitstream
task -d "$ROOT/submission/test" run-simulation BUILD_DIR="$OUT" WAVEFORM_TYPE=vcd VVP_ARGS=+waveform_depth=2
grep -q 'finish called' "$OUT/bitstream_sim.log"  # $fatal on mismatch never reaches $finish
