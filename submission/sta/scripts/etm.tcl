# Extracted timing model of eFPGA_top for chip-level STA, one corner per run.
# Only the CLK-domain configuration ports carry arcs. User IO, USER_CLK and
# USER_RESET enter the fabric's configurable routing, whose timing depends on the
# bitstream, so they are cut from their nets and stay in the model as bare pins.
# Run in <build>/fullsta after prepare.sh, as full.tcl is.
# env: PDK, LIBC (liberty corner), RC (SPEF corner), PERIOD (config clock ns),
#      TAG (corner name), OUT (liberty path)
set L $::env(PDK)/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
set libc $::env(LIBC); set rc $::env(RC); set T $::env(PERIOD)
read_liberty $L/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_${libc}_nldm.lib
read_liberty $L/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_${libc}_nldm.lib
foreach f [glob tile_*.v] { read_verilog $f }
read_verilog top_full.v
link_design eFPGA_top

set user [get_ports {A_OUT_top_* A_IN_top_* A_EN_top_* USER_CLK USER_RESET}]
if {[llength $user] != 32} { error "expected 32 user-side ports, found [llength $user]" }
foreach port $user {
  set name [get_name $port]
  disconnect_pin $name $port
}
puts "user-side ports cut: [llength $user]"

read_spef spef/eFPGA_top_${rc}.spef
foreach c [get_cells Tile_*] {
  read_spef -path [get_name $c] spef/[get_property $c ref_name]_${rc}.spef
}

create_clock -name CLK -period $T [get_ports CLK]
set_propagated_clock [all_clocks]
write_timing_model -library_name eFPGA_top_$::env(TAG) -cell_name eFPGA_top $::env(OUT)
puts "wrote $::env(OUT)"
