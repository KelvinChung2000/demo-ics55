# Figure capture

Screenshots of GTKWave 3.3.121 (headless, Xvfb) and a KLayout 0.30.7 batch render; nothing here draws a waveform or a floorplan itself. `grab.sh` also needs `xdotool`, `xwd` and `ffmpeg`.

Rerun from the repository root: `flow/submission/capture/sim_bitstream.sh`, then `uv run --no-project --with 'cocotb>=2' --with pytest python flow/submission/capture/sim_spi.py`, then `flow/submission/capture/capture_all.sh`. Dumps go to `build/figures/`; needs the `build/nobram/top/` ECC run.
