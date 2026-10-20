"""Rerun the cocotb config_frontend test_stream/port=SPI case with waves on.

    uv run --with 'cocotb>=2' --with pytest python submission/capture/sim_spi.py

Icarus under cocotb writes FST; fst2vcd turns it into build/figures/spi/config_frontend.vcd.
"""

import subprocess
import sys
from pathlib import Path

from cocotb_tools.runner import get_runner

ROOT = Path(__file__).resolve().parents[2]
TB = ROOT / "Test" / "config"
OUT = ROOT / "build" / "figures" / "spi"
sys.path.insert(0, str(TB))

from config_frontend_tb import COM_RATE  # noqa: E402
from test_config_frontend import SOURCES, TOPLEVEL  # noqa: E402

runner = get_runner("icarus")
runner.build(
    sources=SOURCES,
    hdl_toplevel=TOPLEVEL,
    parameters={"ComRate": COM_RATE},
    # cocotb's Icarus dump module declares a `string`, so waves need -g2012 (the test uses -g2005).
    build_args=["-g2012"],
    timescale=("1ns", "1ps"),
    build_dir=OUT,
    always=True,
    waves=True,
)
runner.test(
    hdl_toplevel=TOPLEVEL,
    hdl_toplevel_lang="verilog",
    test_module="config_frontend_tb",
    test_filter=r"\.test_stream/port=SPI$",
    test_dir=TB,
    build_dir=OUT,
    waves=True,
)
fst = OUT / f"{TOPLEVEL}.fst"
subprocess.run(["fst2vcd", "-f", str(fst), "-o", str(OUT / f"{TOPLEVEL}.vcd")], check=True)
print(f"wrote {OUT / f'{TOPLEVEL}.vcd'}")
