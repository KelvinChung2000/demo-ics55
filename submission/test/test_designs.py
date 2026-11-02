"""Every user design built, loaded into the fabric over SPI and checked against
its reference model at RTL, at the hardened eFPGA_top and from the chip pads.

The designs other than sequential_16bit_en are FABulous's integration-test
designs (tests/fabric_gen_test/integration_test/user_designs). Each case loads
the whole bitstream: about 4 to 6 min at RTL and 3.5 min at gate level, so run the
suite in parallel (pytest -n). The gate-level cases need GL_PDK_ROOT.
"""

import os
import re
import subprocess
from enum import StrEnum
from pathlib import Path

import pytest

HERE = Path(__file__).parent


class Level(StrEnum):
    RTL = "rtl"
    GL_TOP = "gl_top"
    GL_CHIP = "gl_chip"


TASK: dict[Level, str] = {
    Level.RTL: "run-simulation",
    Level.GL_TOP: "run-gl-top",
    Level.GL_CHIP: "run-gl-chip",
}
LOG: dict[Level, str] = {
    Level.RTL: "bitstream_sim.log",
    Level.GL_TOP: "gl_top_sim.log",
    Level.GL_CHIP: "gl_chip_sim.log",
}
# Simulated from its submitted bitstream/, never rebuilt.
SUBMITTED = "sequential_16bit_en"
DESIGNS = [
    SUBMITTED,
    "passthrough",
    "addition",
    "multiplication",
    "all_ones",
    "all_zeros",
    "counter",
    "sys_reset",
]


def task(*args: str) -> None:
    subprocess.run(["task", *args], cwd=HERE, check=True)


@pytest.mark.parametrize("level", list(Level), ids=str)
@pytest.mark.parametrize("design", DESIGNS)
def test_design(design: str, level: Level) -> None:
    # One BUILD_DIR per case, so cases can run concurrently.
    build_dir = f"build/{design}-{level}"
    design_args = [f"DESIGN={design}", f"BUILD_DIR={build_dir}"]
    if design == SUBMITTED:
        hex_file = f"bitstream/{design}.hex"
    else:
        hex_file = f"{build_dir}/{design}.hex"
        task("build-test-design", *design_args)
    sim_args = [*design_args, f"BITSTREAM_HEX={hex_file}"]
    if level is Level.RTL:
        # A depth-0 dump of the SPI load fills the disk.
        sim_args += ["WAVEFORM_TYPE=vcd", "VVP_ARGS=+waveform_depth=1"]
    else:
        sim_args.append(f"GL_PDK_ROOT={os.environ['GL_PDK_ROOT']}")
    task(TASK[level], *sim_args)

    log = (HERE / build_dir / LOG[level]).read_text()
    total = re.search(r"^total: (\d+) of (\d+) compares match$", log, re.MULTILINE)
    checks = re.search(r"^checks: (\d+) of (\d+) pass$", log, re.MULTILINE)
    assert total is not None and checks is not None, (
        f"no summary in {build_dir}/{LOG[level]}"
    )
    assert int(total[2]) > 0 and total[1] == total[2], total[0]
    assert checks[1] == checks[2], checks[0]
    assert "$finish called" in log.splitlines()[-1]
