#!/usr/bin/env bash
# Stage the full-chip STA inputs in <build>/fullsta: tile netlists and SPEFs,
# the top SPEFs and the routed top netlist. `$` is renamed throughout because
# iRCX writes it unescaped and OpenSTA rejects it. Usage: prepare.sh <build> <pdk>
set -euo pipefail
HERE=$(dirname "$(realpath "$0")"); BUILD=$(realpath "$1"); PDK=$(realpath "$2")
CORNERS="RCbest_m40C Cbest_m40C Cbest_125C RCbest_125C Cworst_125C Cworst_m40C"
mkdir -p "$BUILD/fullsta/spef"
cd "$BUILD/fullsta"
for d in "$BUILD"/tiles/*/; do
  t=$(basename "$d")
  out="$d/default/RCX_ecc/output"
  zcat "$out/${t}_RCX.v.gz" | sed 's/\$/_DOL_/g' > "tile_${t}.v"
  for c in $CORNERS; do
    sed 's/\$/_DOL_/g' "$out/${t}_${c}.spef" > "spef/${t}_${c}.spef"
  done
done
TOP="$BUILD/top/default"
for c in $CORNERS; do
  sed 's/\$/_DOL_/g' "$TOP/RCX_ecc/output/eFPGA_top_${c}.spef" > "spef/eFPGA_top_${c}.spef"
done
PDK=$PDK MACROS="$TOP/../macros" DEF="$TOP/filler_ecc/output/eFPGA_top_filler.def.gz" \
  openroad -exit -no_init "$HERE/write_v.tcl" > write_v.log
[ -s top_full.v ] || { echo "write_v.tcl wrote no top_full.v, see write_v.log" >&2; exit 1; }
sed -i 's/\$/_DOL_/g' top_full.v
