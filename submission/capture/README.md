# Figure capture

Screenshots of GTKWave 3.3.121 (headless, Xvfb) and a KLayout 0.30.7 batch render; nothing here draws a waveform or a floorplan itself.

Rerun from the repository root: `submission/capture/sim_bitstream.sh`, then `uv run --no-project --with 'cocotb>=2' --with pytest python submission/capture/sim_spi.py`, then `submission/capture/capture_all.sh`. Dumps go to `build/figures/`; needs `Test/build/sequential_16bit_en.hex` and the `build/nobram/top/` ECC run.
