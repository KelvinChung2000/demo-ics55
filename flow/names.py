"""Resolve one name out of a chip-viewer snapshot, for pasting into its search box.

The viewer matches a whole name and nothing else: `SearchMode::query_shape_ids`
bottoms out in `NameIndex::query`, which is a single `HashMap` lookup, and
`regex` is absent from the viewer's `Cargo.lock`, so no pattern can be evaluated
inside it. A pattern is therefore resolved here instead, against the TSV side
files the snapshot writes beside its manifest, and the one winning name is
handed back through the clipboard.

`single_line_query_text` collapses the search box to one line, so a list of
names pasted together matches nothing. Exactly one name reaches the clipboard.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

CLIPBOARD = ("xclip", "-selection", "clipboard")


@dataclass(frozen=True)
class Table:
    """One TSV side file, and how a searchable name is built from a row."""

    key: str
    """The manifest key naming the file, so a rebuilt epoch is followed automatically."""
    columns: tuple[int, ...]
    """Column indices joined by `/` to form the name, matching the viewer's pin form."""
    where: tuple[int, str] | None = None
    """An optional column and the value it must hold for the row to count."""


class Kind(str, Enum):
    """What to search, mirroring the viewer's own scope selector.

    The members carry their spelling rather than their table so that typer
    offers `--kind signal` instead of a dumped dataclass.
    """

    NET = "net"
    SIGNAL = "signal"
    CLOCK = "clock"
    INSTANCE = "instance"
    PIN = "pin"
    IO = "io"
    MASTER = "master"


TABLES: dict[Kind, Table] = {
    Kind.NET: Table(key="nets", columns=(0,)),
    Kind.SIGNAL: Table(key="nets", columns=(0,), where=(1, "signal")),
    Kind.CLOCK: Table(key="nets", columns=(0,), where=(1, "clock")),
    Kind.INSTANCE: Table(key="connectivity", columns=(3,), where=(2, "instance")),
    Kind.PIN: Table(key="connectivity", columns=(3, 4), where=(2, "instance")),
    Kind.IO: Table(key="connectivity", columns=(4,), where=(2, "io")),
    Kind.MASTER: Table(key="masters", columns=(0,)),
}


def side_files(manifest: Path) -> dict[str, Path]:
    """Return every side file the manifest names, resolved against its own directory."""
    entries: dict[str, Path] = {}
    for line in manifest.read_text().splitlines():
        key, separator, value = line.partition("=")
        if separator and value.endswith((".txt", ".bin")):
            entries[key] = manifest.parent / value
    return entries


def search(manifest: Path, pattern: str, kind: Kind) -> list[str]:
    """Return every distinct name of `kind` whose text the pattern finds, in file order.

    The pattern is unanchored, so `Tile_X4Y7_` finds names containing it. Anchor
    it with `^` for a prefix. Names repeat across connectivity rows, one per
    endpoint, so duplicates are dropped while their first order is kept.
    """
    table = TABLES[kind]
    path = side_files(manifest)[table.key]
    if not path.exists():
        raise FileNotFoundError(f"the snapshot names {path}, which does not exist")
    expression = re.compile(pattern)
    seen: dict[str, None] = {}
    with path.open() as handle:
        next(handle)  # the header row names the columns
        for line in handle:
            row = line.rstrip("\n").split("\t")
            if table.where is not None and row[table.where[0]] != table.where[1]:
                continue
            name = "/".join(row[column] for column in table.columns)
            if expression.search(name):
                seen[name] = None
    return list(seen)


def copy(text: str) -> None:
    """Put `text` on the X11 clipboard, failing loudly when no tool can hold it.

    An X11 selection lives in the process that owns it, so `xclip` stays running
    until another client takes the clipboard. Its inherited stdout is detached
    here, since anything reading downstream of this command would otherwise
    block on a pipe the surviving `xclip` still holds open.
    """
    try:
        process = subprocess.Popen(
            CLIPBOARD,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            f"{CLIPBOARD[0]} is not installed, so nothing can reach the clipboard. "
            f"Install it, or read the name off the listing and copy it by hand."
        ) from error
    process.stdin.write(text)
    process.stdin.close()
