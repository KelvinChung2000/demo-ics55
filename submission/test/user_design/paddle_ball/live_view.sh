#!/usr/bin/env bash
# Plays the VGA output of a paddle_ball Verilator binary live in ffplay.
# Task's shell reports $! as a goroutine id, not a PID, so the process
# handling lives here in bash.
# Usage: live_view.sh <binary> <live dir> <frames>
set -euo pipefail

binary=$1
live_dir=$2
frames=$3
fifo=$live_dir/vga.fifo

rm -rf "$live_dir"
mkdir -p "$live_dir/frames"
mkfifo "$fifo"

ffplay -loglevel error -f image2pipe -vcodec ppm -framerate 60 \
    -vf scale=640:480:flags=neighbor -i "$fifo" &
player=$!
# A stride past the last frame leaves frame 0 as the only file written.
"$binary" +stream="$fifo" +frames="$frames" +frame_stride=$((frames + 1)) +out_dir="$live_dir/frames" &
sim=$!

rc=0
wait -n -p first "$player" "$sim" || rc=$?
if [ "$first" = "$sim" ]; then
    # ffplay never exits at end of stream on its own.
    kill "$player"
    wait "$player" || true
    exit "$rc"
fi
# ffplay ended first: rc 0 when the window was closed, else ffplay failed.
echo "ffplay exited with $rc; stopping the simulation" >&2
kill "$sim"
wait "$sim" || true
exit "$rc"
