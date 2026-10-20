# Post-legalisation DRV and hold repair of eFPGA_top, run by flow.integrate.
# ECC skips TimingOpt (no Sizer here), so nothing else sizes or buffers the
# loader and front-ends against their placed wire. Reports land in the cwd.
# env: PDK, MACROS (dir of <tile>/<tile>_Harden.{lef,lib}), DEF_IN, DEF_OUT,
#      SDC, HOLD_UNCERTAINTY, HOLD_MARGIN
if {[catch {
  set S $::env(PDK)/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
  read_lef $::env(PDK)/prtech/techLEF/N551P6M_ecos.lef
  read_lef $S/ics55_LLSC_H7CR/lef/ics55_LLSC_H7CR_ecos.lef
  read_lef $S/ics55_LLSC_H7CL/lef/ics55_LLSC_H7CL_ecos.lef
  foreach f [glob $::env(MACROS)/*/*_Harden.lef] { read_lef $f }
  # Slew and capacitance are repaired at the slow corner, hold at the fast one.
  define_corners ss ff
  foreach v {R L} {
    read_liberty -corner ss $S/ics55_LLSC_H7C$v/liberty/ics55_LLSC_H7C${v}_ss_rcworst_1p08_125_nldm.lib
    read_liberty -corner ff $S/ics55_LLSC_H7C$v/liberty/ics55_LLSC_H7C${v}_ff_rcbest_1p32_m40_nldm.lib
  }
  # A tile's Harden .lib is its ss_125 abstract; it stands in at both corners.
  foreach f [glob $::env(MACROS)/*/*_Harden.lib] {
    read_liberty -corner ss $f
    read_liberty -corner ff $f
  }
  read_def $::env(DEF_IN)
  read_sdc $::env(SDC)
  set_clock_uncertainty -hold $::env(HOLD_UNCERTAINTY) [all_clocks]
  set_wire_rc -signal -layer MET3
  set_wire_rc -clock -layer MET3
  set_dont_use [list *X0P5H7* *X0P7H7* FILL* *X16H7* *X20H7*]
  estimate_parasitics -placement
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_before.txt
  puts "hold before: [sta::worst_slack -min]"
  repair_design -slew_margin 20 -cap_margin 20
  estimate_parasitics -placement
  repair_timing -hold -hold_margin $::env(HOLD_MARGIN) -allow_setup_violations
  detailed_placement
  check_placement -verbose
  estimate_parasitics -placement
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_after.txt
  puts "hold after: [sta::worst_slack -min]"
  puts "setup after: [sta::worst_slack -max]"
  report_design_area
  write_def $::env(DEF_OUT)
} message]} {
  puts "repair failed: $message"
  exit 1
}
exit 0
