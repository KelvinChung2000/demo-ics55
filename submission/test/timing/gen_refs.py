"""Write refs.vh naming the fabric flop whose CLK pin times the testbench checks.

    python gen_refs.py <routed.json> <net> <refs.vh>
"""

import json
import sys
from pathlib import Path


def main(routed: Path, net: str, out: Path) -> None:
    (module,) = json.loads(routed.read_text())["modules"].values()
    (bit,) = module["netnames"][net]["bits"]
    drivers = [
        name
        for name, cell in module["cells"].items()
        if cell["type"] == "FABULOUS_LC" and cell["connections"].get("Q") == [bit]
    ]
    if len(drivers) != 1:
        raise ValueError(f"Expected one FABULOUS_LC driving {net} from Q, found {drivers}")
    out.write_text(f"`define REF_CLK dut.{drivers[0]}.CLK\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
