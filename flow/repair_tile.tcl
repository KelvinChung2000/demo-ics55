# Post-legalisation slew and capacitance repair of one tile, run by flow.repair.
# Signoff is at the slow corner, so that is the only one read. Reports land in
# the cwd. env: PDK, DEF_IN, DEF_OUT, MARGIN (percent inside the limits)
if {[catch {
  set S $::env(PDK)/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
  read_lef $::env(PDK)/prtech/techLEF/N551P6M_ecos.lef
  read_lef $S/ics55_LLSC_H7CR/lef/ics55_LLSC_H7CR_ecos.lef
  read_lef $S/ics55_LLSC_H7CL/lef/ics55_LLSC_H7CL_ecos.lef
  foreach v {R L} {
    read_liberty $S/ics55_LLSC_H7C$v/liberty/ics55_LLSC_H7C${v}_ss_rcworst_1p08_125_nldm.lib
  }
  read_def $::env(DEF_IN)
  set_wire_rc -signal -layer MET3
  set_wire_rc -clock -layer MET3
  set_dont_use [list *X0P5H7* *X0P7H7* FILL* *X16H7* *X20H7*]
  estimate_parasitics -placement
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_before.txt
  repair_design -slew_margin $::env(MARGIN) -cap_margin $::env(MARGIN)
  detailed_placement
  check_placement -verbose
  estimate_parasitics -placement
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_after.txt
  report_design_area
  write_def $::env(DEF_OUT)
} message]} {
  puts "repair failed: $message"
  exit 1
}
exit 0
