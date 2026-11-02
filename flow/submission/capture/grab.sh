#!/usr/bin/env bash
# Open <dump> in GTKWave with <save.gtkw> on a headless X server, zoom to
# [T0, T1] via zoom.tcl, and screenshot the GTKWave window to <out.png>.
#   T0=0 T1=7300000 grab.sh dump.vcd save.gtkw out.png
set -euo pipefail
[ $# -eq 3 ] || { sed -n 2,4p "$0"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
DUMP=$1 SAVE=$2 OUT=$3
: "${T0:?}" "${T1:?}"
# The Xvfb screen takes the window size the save file asks for.
read -r W H < <(sed -n "s/^\[size\] //p" "$SAVE")
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
# GTK3 prefers Wayland when WAYLAND_DISPLAY is set and would draw on the
# desktop, leaving the Xvfb screen white.
xvfb-run -a -s "-screen 0 ${W}x${H}x24" bash -c '
    env -u WAYLAND_DISPLAY GDK_BACKEND=x11 gtkwave -a "$1" -S "$2/zoom.tcl" "$3" >"$4/gtkwave.log" 2>&1 &
    pid=$!
    xdotool search --sync --onlyvisible --class gtkwave >/dev/null
    sleep "${SETTLE:-5}"
    xwd -root -silent -out "$4/shot.xwd"
    kill $pid
' _ "$SAVE" "$HERE" "$DUMP" "$TMP"
ffmpeg -loglevel error -y -i "$TMP/shot.xwd" "$OUT"
echo "wrote $OUT"
