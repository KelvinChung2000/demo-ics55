"""Draw the eFPGA_top floorplan from the abutment plan.

Tile rectangles come from build/<variant>/fabric_plan.json (nm), shifted by the
array origin the integrate run fixes inside the eFPGA_top die.

    python3 submission/images/floorplan.py build/nobram/fabric_plan.json submission/images/floorplan.png
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

# eFPGA_top die and array origin from the integrate run, in µm.
DIE_W, DIE_H = 999.0, 912.6
ORIGIN_X, ORIGIN_Y = 50.0, 24.6

INK = "#0b0b0b"
MUTED = "#52514e"
SURFACE = "#fcfcfb"
CONTROL = "#e4e3df"
CLASSES = {
    "LUT4x8_ha": ("logic, LUT4x8_ha", "#2a78d6"),
    "MACC": ("multiply-accumulate, MACC", "#eb6834"),
    "IO": ("IO, W/E/N/S_IO", "#1baf7a"),
    "term": ("terminator", "#eda100"),
}
LABEL = {"LUT4x8_ha": "LUT", "MACC": "MACC", "W_IO": "W", "E_IO": "E", "N_IO": "N", "S_IO": "S"}


def tile_class(tile_type: str) -> str:
    if tile_type in ("LUT4x8_ha", "MACC"):
        return tile_type
    if tile_type.endswith("_IO"):
        return "IO"
    if "term" in tile_type:
        return "term"
    raise ValueError(f"unclassified tile type {tile_type}")


def main(plan_path: Path, out: Path) -> None:
    plan = json.loads(plan_path.read_text())
    size = plan["tile_size"]
    fig, ax = plt.subplots(figsize=(8, 7.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.add_patch(Rectangle((0, 0), DIE_W, DIE_H, fc=CONTROL, ec=INK, lw=1))
    ax.text(ORIGIN_X / 2, DIE_H / 2, "configuration logic, west channel", rotation=90,
            ha="center", va="center", fontsize=8, color=MUTED)
    ax.text(DIE_W / 2, ORIGIN_Y / 2, "configuration logic, south strip", ha="center",
            va="center", fontsize=8, color=MUTED)
    for p in plan["placements"]:
        w, h = (v / 1000 for v in size[p["tile_type"]])
        x = ORIGIN_X + p["x"] / 1000
        y = ORIGIN_Y + p["y"] / 1000
        _, colour = CLASSES[tile_class(p["tile_type"])]
        ax.add_patch(Rectangle((x, y), w, h, fc=colour, ec=SURFACE, lw=0.8))
        text = LABEL.get(p["tile_type"])
        if text:
            ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=6,
                    color=SURFACE if p["tile_type"] in ("LUT4x8_ha", "MACC") else INK)
    ax.set_xlim(-10, DIE_W + 10)
    ax.set_ylim(-10, DIE_H + 10)
    ax.set_aspect("equal")
    ax.set_xlabel("x (µm)", fontsize=9, color=INK)
    ax.set_ylabel("y (µm)", fontsize=9, color=INK)
    ax.tick_params(labelsize=8, colors=INK)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(handles=[Patch(fc=c, label=l) for l, c in CLASSES.values()]
              + [Patch(fc=CONTROL, ec=INK, lw=0.5, label="standard cells, configuration logic")],
              loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=8, frameon=False)
    ax.set_title(f"eFPGA_top {DIE_W} × {DIE_H} µm, array {plan['width'] / 1000} × "
                 f"{plan['height'] / 1000} µm at ({ORIGIN_X}, {ORIGIN_Y}) µm, "
                 f"{len(plan['placements'])} tiles", fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
