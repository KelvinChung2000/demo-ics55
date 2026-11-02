# KLayout batch render of the eFPGA_top placement GDS that ECC writes.
#   klayout -b -rd gds=<eFPGA_top_place.gds> -rd out=<png> -r floorplan_klayout.py
# Hierarchy depth 0..1 draws each instance's master outline (layer 0/0) and
# labels the instance frame with its master name; the other layers (pins,
# obstructions, rows) are hidden so the tile array and the standard-cell
# west channel and south strip read at report scale.
import pya

W, H = 2400, 2200

lv = pya.LayoutView()
lv.load_layout(gds, True)
lv.set_config("background-color", "#ffffff")
lv.set_config("grid-visible", "false")
lv.set_config("cell-box-color", "#202020")
lv.set_config("default-text-size", "1.5")
lv.min_hier_levels = 0
lv.max_hier_levels = 1
lv.add_missing_layers()
it = lv.begin_layers()
while not it.at_end():
    lp = it.current().dup()
    lp.visible = lp.source_layer == 0 and lp.source_datatype in (0, 2)
    lp.frame_color = 0x1f4e79
    lp.dither_pattern = 1  # hollow: layer 0/0 also carries the DIEAREA box
    lv.set_layer_properties(it, lp)
    it.next()
lv.zoom_fit()
lv.save_image(out, W, H)
print(f"wrote {out}")
