"""Render the report's timing figures from the simulation VCDs.

The bitstream simulation VCD is 1 GB, so the reader streams it once and keeps
only the top-scope signals each figure names.

    python3 submission/images/waveforms.py <bitstream.vcd> <spi.vcd> <out_dir>

<bitstream.vcd> comes from `task VARIANT=nobram WAVEFORM_TYPE=vcd
build-test-design run-simulation` in Test/; <spi.vcd> from the cocotb
`test_stream/port=SPI` case run with waves and converted by fst2vcd.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK = "#2b2b2b"
ACCENT = "#1f6fb2"  # configuration signals
USER = "#b5531f"  # user-mode signals
GRID = "#d9d9d9"


@dataclass
class Trace:
    width: int
    times: list[int] = field(default_factory=list)
    values: list[str] = field(default_factory=list)

    def at(self, t: int) -> str:
        """Value in force at time t; raises if t precedes the first change."""
        lo, hi = 0, len(self.times) - 1
        if hi < 0 or t < self.times[0]:
            raise ValueError(f"no value before t={t}")
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.times[mid] <= t:
                lo = mid
            else:
                hi = mid - 1
        return self.values[lo]


def read_vcd(path: Path, scope: str, names: set[str]) -> dict[str, Trace]:
    """Stream a VCD and return the traces of `names` declared directly in `scope`."""
    ids: dict[str, str] = {}
    traces: dict[str, Trace] = {}
    depth_path: list[str] = []
    t = 0
    with path.open() as f:
        for line in f:
            if line.startswith("$scope"):
                depth_path.append(line.split()[2])
            elif line.startswith("$upscope"):
                depth_path.pop()
            elif line.startswith("$var") and depth_path == [scope]:
                _, _, width, ident, name, *_ = line.split()
                if name in names and name not in traces:
                    ids[ident] = name
                    traces[name] = Trace(int(width))
            elif line.startswith("$enddefinitions"):
                missing = names - traces.keys()
                if missing:
                    raise KeyError(f"{path}: {sorted(missing)} not in scope {scope}")
                break
        for line in f:
            c = line[0]
            if c == "#":
                t = int(line[1:])
            elif c in "01xzXZ":
                name = ids.get(line[1:].rstrip("\n"))
                if name:
                    traces[name].times.append(t)
                    traces[name].values.append(c.lower())
            elif c in "bB":
                value, ident = line[1:].split()
                name = ids.get(ident)
                if name:
                    traces[name].times.append(t)
                    traces[name].values.append(value.lower())
    return traces


def to_int(value: str) -> int | None:
    return None if any(ch in "xz" for ch in value) else int(value, 2)


def plot(
    *,
    rows: list[tuple[str, Trace, str, int | None]],
    t0: int,
    t1: int,
    unit: float,
    unit_name: str,
    out: Path,
    title: str,
    marks: list[tuple[int, str]] = (),
) -> None:
    """Draw one digital timing diagram, one row per (label, trace, colour, bit mask)."""
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(rows) + 1.0), dpi=200)
    for k, (label, tr, colour, mask) in enumerate(rows):
        y = len(rows) - 1 - k
        pts = [(t0, tr.at(t0))] + [
            (t, v) for t, v in zip(tr.times, tr.values) if t0 < t < t1
        ]
        pts.append((t1, pts[-1][1]))
        if tr.width == 1 and mask is None:
            xs, ys = [], []
            for (ta, va), (tb, _) in zip(pts, pts[1:]):
                level = y + (0.7 if va == "1" else 0.1)
                xs += [ta / unit, tb / unit]
                ys += [level, level]
            ax.plot(xs, ys, color=colour, lw=1.2, drawstyle="default")
        else:
            prev = None
            segs = []
            for (ta, va), (tb, _) in zip(pts, pts[1:]):
                n = to_int(va)
                n = None if n is None else (n & mask if mask else n)
                if segs and n == prev:
                    segs[-1][1] = tb
                else:
                    segs.append([ta, tb, n])
                prev = n
            for ta, tb, n in segs:
                xa, xb = ta / unit, tb / unit
                ax.fill_between([xa, xb], y + 0.1, y + 0.7, color=colour, alpha=0.08, lw=0)
                ax.plot([xa, xb], [y + 0.1] * 2, color=colour, lw=1)
                ax.plot([xa, xb], [y + 0.7] * 2, color=colour, lw=1)
                ax.plot([xa, xa], [y + 0.1, y + 0.7], color=colour, lw=1)
                span = (t1 - t0) / unit
                if (xb - xa) > span * 0.035:
                    text = "x" if n is None else f"{n:X}"
                    ax.text((xa + xb) / 2, y + 0.4, text, ha="center", va="center",
                            fontsize=7, color=INK)
        ax.text(t0 / unit - (t1 - t0) / unit * 0.01, y + 0.4, label, ha="right",
                va="center", fontsize=9, color=INK)
    for t, text in marks:
        ax.axvline(t / unit, color=GRID, lw=1, zorder=0)
        ax.text(t / unit, len(rows) + 0.05, text, ha="center", va="bottom",
                fontsize=8, color=INK)
    ax.set_xlim(t0 / unit, t1 / unit)
    ax.set_ylim(-0.2, len(rows) + 0.5)
    ax.set_yticks([])
    ax.set_xlabel(unit_name, fontsize=9, color=INK)
    ax.tick_params(axis="x", labelsize=8, colors=INK)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out}")


def first_rise(tr: Trace, after: int = 0) -> int:
    for t, v in zip(tr.times, tr.values):
        if t >= after and v == "1":
            return t
    raise ValueError("signal never rises")


def first_change(tr: Trace, after: int) -> int:
    for t in tr.times:
        if t > after:
            return t
    raise ValueError("signal never changes")


def last_fall(tr: Trace) -> int:
    falls = [t for t, v in zip(tr.times, tr.values) if v == "0"]
    if not falls:
        raise ValueError("signal never falls")
    return falls[-1]


def main(bit_vcd: Path, spi_vcd: Path, out: Path) -> None:
    us = 1_000_000  # ps per µs
    s = read_vcd(bit_vcd, "sequential_16bit_en_tb", {
        "CLK", "resetn", "self_write_strobe", "self_write_data", "config_busy",
        "configured", "pad_in", "A_IN_top", "A_IN_top_gold", "A_EN_top",
    })
    busy_on = first_rise(s["config_busy"])
    cfg_on = first_rise(s["configured"])
    busy_off = last_fall(s["config_busy"])
    end = s["CLK"].times[-1]
    print(f"ConfigBusy {busy_on / us:.1f} µs to {busy_off / us:.1f} µs, "
          f"Configured at {cfg_on / us:.1f} µs, end {end / us:.1f} µs")

    # Figure 2-4: reset release, the whole load, then user mode.
    plot(rows=[
        ("resetn", s["resetn"], ACCENT, None),
        ("SelfWriteStrobe (4,096 words)", s["self_write_strobe"], ACCENT, None),
        ("ConfigBusy", s["config_busy"], ACCENT, None),
        ("Configured", s["configured"], ACCENT, None),
        ("pad_in[1:0] (en, rst)", s["pad_in"], USER, 0b11),
        ("A_IN_top[15:0]", s["A_IN_top"], USER, 0xFFFF),
    ], t0=0, t1=end, unit=us * 1000, unit_name="time (ms), CLK = 1 MHz in simulation",
        out=out / "clock_reset_timing.png",
        title="resetn release, parallel-port configuration load and user mode",
        marks=[(busy_on, "load starts"), (cfg_on, "Configured")])

    # Figure 5-2: user mode, fabric against the reference design.
    u0 = first_change(s["pad_in"], after=cfg_on) - 3 * us
    plot(rows=[
        ("CLK (user clock on pad 16)", s["CLK"], INK, None),
        ("pad_in[1:0] (en, rst)", s["pad_in"], USER, 0b11),
        ("fabric A_IN_top[15:0]", s["A_IN_top"], USER, 0xFFFF),
        ("gold A_IN_top[15:0]", s["A_IN_top_gold"], INK, 0xFFFF),
        ("fabric A_EN_top", s["A_EN_top"], USER, None),
    ], t0=u0, t1=u0 + 24 * us, unit=us, unit_name="time (µs)",
        out=out / "simulation_waveform.png",
        title="sequential_16bit_en on eFPGA_top after configuration, fabric against reference")

    # Figure 2-3: one SPI word into config_frontend.
    p = read_vcd(spi_vcd, "config_frontend", {
        "CLK", "spi_cs_n", "spi_sck", "spi_mosi", "spi_strobe", "bitstream_valid",
        "bitstream_data",
    })
    ns = 1000
    cs_fall = next(t for t, v in zip(p["spi_cs_n"].times, p["spi_cs_n"].values) if v == "0" and t > 0)
    strobe = first_rise(p["bitstream_valid"], after=cs_fall)
    plot(rows=[
        ("spi_cs_n", p["spi_cs_n"], ACCENT, None),
        ("spi_sck", p["spi_sck"], ACCENT, None),
        ("spi_mosi", p["spi_mosi"], ACCENT, None),
        ("bitstream_valid", p["bitstream_valid"], INK, None),
        ("bitstream_data", p["bitstream_data"], INK, None),
    ], t0=cs_fall - 200 * ns, t1=strobe + 400 * ns, unit=ns * 1000, unit_name="time (µs), CLK = 25 MHz",
        out=out / "interface_timing.png",
        title="SPI mode 0, MSB first: a 7-bit fragment cut by spi_cs_n yields no word; the next 32 bits yield 0x00AAFF01")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
