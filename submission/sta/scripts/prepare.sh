#!/usr/bin/env bash
# Tile netlists and SPEFs from the hardened tiles, `$` renamed because iRCX
# writes it unescaped and OpenSTA rejects it.
set -euo pipefail
cd "$(dirname "$0")"
TILES=../tiles
mkdir -p spef
for d in "$TILES"/*/; do
  t=$(basename "$d")
  out="$d/default/RCX_ecc/output"
  zcat "$out/${t}_RCX.v.gz" | sed 's/\$/_DOL_/g' > "tile_${t}.v"
  for c in RCbest_m40C Cbest_m40C Cbest_125C RCbest_125C Cworst_125C Cworst_m40C; do
    sed 's/\$/_DOL_/g' "$out/${t}_${c}.spef" > "spef/${t}_${c}.spef"
  done
done

# The top run's buffer insertion also names nets with `$`.
TOP=../top/default/RCX_ecc/output
for c in RCbest_m40C Cbest_m40C Cbest_125C RCbest_125C Cworst_125C Cworst_m40C; do
  sed 's/\$/_DOL_/g' "$TOP/eFPGA_top_${c}.spef" > "spef/eFPGA_top_${c}.spef"
done
