# Full-chip STA of eFPGA_top: hierarchical tile netlists with per-instance SPEF.
# env: LIBC (liberty corner), RC (SPEF corner), PERIOD (config clock ns)
set L /home/kelvin/side-project/demo-ics55/pdk/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
set TOPSPEF /home/kelvin/side-project/demo-ics55/build/nobram/top/default/RCX_ecc/output
set libc $::env(LIBC); set rc $::env(RC); set T $::env(PERIOD)
read_liberty $L/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_${libc}_nldm.lib
read_liberty $L/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_${libc}_nldm.lib
foreach f [glob tile_*.v] { read_verilog $f }
read_verilog top_full.v
link_design eFPGA_top
read_spef spef/eFPGA_top_${rc}.spef
set ntile 0
foreach c [get_cells Tile_*] {
  set ref [get_property $c ref_name]
  read_spef -path [get_name $c] spef/${ref}_${rc}.spef
  incr ntile
}
puts "tiles annotated: $ntile"
report_parasitic_annotation

create_clock -name CLK -period $T [get_ports CLK]
# One user clock on GBUF A; every tile's GCLK mux can select it.
if {[info exists ::env(IDEAL_GBUF)]} {
  # Diagnostic: the clock starts at every tile's GBUF-select mux with the XOR's net removed.
  set gpins [concat [get_pins -hierarchical *inst_cus_mux41_GCLK_BEG0/A] [get_pins -hierarchical *inst_cus_mux41_A_CLK/A] [get_pins -hierarchical *MACC_bot_switch_matrix.inst_cus_mux41_CLK/A]]
  puts "ideal GBUF sinks: [llength $gpins]"
  create_clock -name uclk -period 10 $gpins
  set_clock_transition 0.1 [get_clocks uclk]
} else {
  create_clock -name uclk -period 10 [get_pins Tile_X0Y11_SW_term/GBUF_A_OUT_XOR2X0P5H7L_Y/B]
}
set_case_analysis 0 [get_pins Tile_X0Y11_SW_term/Inst_GBUF_A_GBUF.ConfigBits_0__DOL__DLATCH_P__Q/Q]
set clkinv [get_pins -hierarchical *MACC_bot_ConfigMem.Inst_frame13_bit30.Q__DOL__DLATCH_P__Q/Q]
puts "MACC CLK_INV bits: [llength $clkinv]"
set_case_analysis $::env(CLKINV) $clkinv
set_propagated_clock [all_clocks]
set_clock_groups -asynchronous -group CLK -group uclk

set latD [get_pins -hierarchical *_DLATCH_P__Q/D]
set latG [get_pins -hierarchical *_DLATCH_P__Q/G]
puts "latches: [llength $latD] D, [llength $latG] G"
set fdata [get_cells frame_data_*_reg_p]
set fstrobe [get_cells loader.frame_strobe_reg_p]
set fsel [concat [get_cells loader.frame_select_*_reg_p] [get_cells loader.column_select_*_reg_p]]
set_max_delay $T -from $fdata -to $latD
set_min_delay 0 -from $fdata -to $latD
set_max_delay $T -from [concat $fstrobe $fsel] -to $latG
set_min_delay 0 -from [concat $fstrobe $fsel] -to $latG

puts "\n==== hold summary, all clocks (setup is reported per clock below; uclk setup in bound mode is meaningless)"
report_wns -min -digits 3
report_tns -min -digits 3

puts "\n==== CLK register-to-register (loader and front-ends)"
set clkregs [all_registers -clock CLK -clock_pins]
report_checks -path_delay max -from $clkregs -to [all_registers -clock CLK -data_pins] -group_path_count 1 -digits 3 -format end
report_checks -path_delay min -from $clkregs -to [all_registers -clock CLK -data_pins] -group_path_count 3 -digits 3 -format end

puts "\n==== uclk hold from the GBUF source pin (clock used as data, e.g. GBUF A into GSR)"
report_checks -path_delay min -from [get_pins Tile_X0Y11_SW_term/GBUF_A_OUT_XOR2X0P5H7L_Y/B] -group_path_count 1 -format end -digits 3
puts "\n==== uclk hold, bound mode"
set uregs [all_registers -clock uclk -clock_pins]
puts "uclk registers: [llength $uregs]"
foreach {label pat} {LUT *LUT_flop_reg_p/D IO *IOBUF.*_q_reg_p/D MACC *MACC_8x8_20*reg_p/D} {
  set to [get_pins -hierarchical $pat]
  puts "== worst hold into $label ([llength $to] pins)"
  report_checks -path_delay min -from $uregs -to $to -group_path_count 3 -digits 3 -format end
}
report_checks -path_delay min -from $uregs -group_path_count 1000000 -slack_max 0 -format end -digits 3 > hold_violators_$::env(TAG).txt
report_checks -path_delay min -from $uregs -group_path_count 1 -format full_clock_expanded -fields {slew cap fanout} -digits 3
report_clock_skew -hold -clock uclk -digits 3
puts "\n==== uclk spine: insertion delay at every tile's GBUF tap, the clk_buf chain's whole cost"
report_clock_latency -clock uclk -digits 3
report_clock_skew -setup -clock uclk -digits 3

puts "\n==== config write: FrameData into latch D (arrival = T - max slack, = min slack)"
report_checks -path_delay max -to $latD -group_path_count 1 -digits 3 -format end
report_checks -path_delay min -to $latD -group_path_count 1 -digits 3 -format end
puts "\n==== config write: FrameStrobe falling at latch G from frame_strobe"
report_checks -path_delay max -from $fstrobe -fall_to $latG -group_path_count 1 -digits 3 -format end
report_checks -path_delay min -from $fstrobe -fall_to $latG -group_path_count 1 -digits 3 -format end
puts "\n==== config write: frame/column select into latch G (glitch window)"
report_checks -path_delay min -from $fsel -rise_to $latG -group_path_count 1 -digits 3 -format end
report_checks -path_delay max -from $fstrobe -fall_to $latG -group_path_count 1 -digits 3 -format full -digits 3

puts "\n==== design rules"
report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_$::env(TAG).txt
report_pulse_width_checks -digits 3 > mpw_$::env(TAG).txt
puts "\n==== CLK worst setup path"
report_checks -path_delay max -group_path_count 1 -path_group CLK -format full -fields {slew cap fanout} -digits 3
