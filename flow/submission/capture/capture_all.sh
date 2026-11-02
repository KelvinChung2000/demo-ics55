#!/usr/bin/env bash
# Capture the report's waveform and floorplan figures from GTKWave and KLayout
# into submission/images/. Run sim_bitstream.sh and sim_spi.py first.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(git -C "$HERE" rev-parse --show-toplevel)
FIG=$ROOT/build/figures
IMG=$ROOT/submission/images
BIT=$FIG/bitstream/sequential_16bit_en.vcd
SPI=$FIG/spi/config_frontend.vcd
export SETTLE=8
# Times in ps. Configured rises at 433.4365 ms; pad_in leaves 0 at 433.546 ms; $finish at 433.674 ms.
T0=0 T1=433674000000 "$HERE/grab.sh" "$BIT" "$HERE/clock_reset_timing.gtkw" "$IMG/clock_reset_timing.png"
T0=433543000000 T1=433570000000 "$HERE/grab.sh" "$BIT" "$HERE/simulation_waveform.gtkw" "$IMG/simulation_waveform.png"
T0=0 T1=40000000 "$HERE/grab.sh" "$BIT" "$HERE/reset_release.gtkw" "$IMG/reset_release.png"
T0=0 T1=7300000 "$HERE/grab.sh" "$SPI" "$HERE/interface_timing.gtkw" "$IMG/interface_timing.png"
klayout -b -rd gds="$ROOT/build/nobram/top/default/place_dreamplace/output/eFPGA_top_place.gds" \
    -rd out="$IMG/floorplan.png" -r "$HERE/floorplan_klayout.py"
