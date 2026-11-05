#!/usr/bin/env bash
# Six signoff corners in parallel, about 10 min and 2.7 GB each.
# Usage: run.sh <build> <pdk>; HOLD_UNC defaults to 0.05 ns.
set -euo pipefail
PDK=$(realpath "$2"); TCL="$(dirname "$(realpath "$0")")/full.tcl"
cd "$1/fullsta"
for spec in "ff_rcbest_1p32_m40 RCbest_m40C ff_m40_RCbest" "ff_rcbest_1p32_m40 Cbest_m40C ff_m40_Cbest" "ff_cbest_1p32_125 Cbest_125C ff_125_Cbest" "ff_rcbest_1p08_125 RCbest_125C ff1p08_125_RCbest" "ss_rcworst_1p08_125 Cworst_125C ss_125_Cworst" "ss_cworst_1p08_m40 Cworst_m40C ss_m40_Cworst"; do
  set -- $spec
  env PDK=$PDK LIBC=$1 RC=$2 PERIOD=10 CLKINV=0 HOLD_UNC=${HOLD_UNC:-0.05} TAG=$3 \
    setsid nohup sta -no_init -exit "$TCL" > $3.log 2>&1 < /dev/null &
done
