#!/usr/bin/env python3
"""Convert a binary file to hex format for memory initialization.

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.
"""

from pathlib import Path
from sys import argv

binfile = argv[1]
nbytes = int(argv[2])
outfile = argv[3]

with Path(binfile).open("rb") as f:
    bindata = f.read()

assert len(bindata) <= nbytes

# No padding to nbytes: the testbench shifts every byte in the file.
with Path(outfile).open("w") as f:
    for byte in bindata:
        print(f"{byte:02x}", file=f)
