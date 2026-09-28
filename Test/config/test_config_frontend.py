from pathlib import Path
from xml.etree import ElementTree

import pytest
from cocotb_tools.runner import get_runner

from config_frontend_tb import COM_RATE, Port

HERE = Path(__file__).parent
FABRIC = HERE.parents[1] / "Fabric"
SOURCES = [
    FABRIC / name
    for name in ("config_frontend.v", "config_UART.v", "bitbang.v", "config_spi.v")
]
TOPLEVEL = "config_frontend"


@pytest.fixture(scope="module")
def build_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("config_frontend")
    get_runner("icarus").build(
        sources=SOURCES,
        hdl_toplevel=TOPLEVEL,
        parameters={"ComRate": COM_RATE},
        build_args=["-g2005"],
        timescale=("1ns", "1ps"),
        build_dir=path,
        always=True,
    )
    return path


@pytest.mark.parametrize("port", list(Port), ids=lambda port: port.name)
def test_stream(port: Port, build_dir: Path) -> None:
    name = f"test_stream/port={port.name}"
    results = get_runner("icarus").test(
        hdl_toplevel=TOPLEVEL,
        hdl_toplevel_lang="verilog",
        test_module="config_frontend_tb",
        test_filter=f"\\.{name}$",
        build_dir=build_dir,
        results_xml=str(build_dir / f"results_{port.name}.xml"),
    )
    # cocotb only warns when a filter matches nothing, so check what actually ran.
    ran = [
        (case.get("name"), case.find("failure") is None)
        for case in ElementTree.parse(results).iter("testcase")
        if case.find("skipped") is None
    ]
    assert ran == [(name, True)]
