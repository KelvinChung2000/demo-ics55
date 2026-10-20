# Post-legalisation slew and capacitance repair of one tile, run by flow.repair.
# Signoff is at the slow corner, so that is the only one read. Reports land in
# the cwd. env: PDK, DEF_IN, DEF_OUT, and one or both of MARGIN (percent inside
# the limits that repair_design buffers and sizes to) and UPSIZE_WIRE_SCALE (wire
# capacitance multiplier for the upsizing pass)
set dont_use [list *X0P5H7* *X0P7H7* FILL* *X16H7* *X20H7*]

# Nets carrying a slew or capacitance violation under the current parasitics.
proc violating_nets {} {
  report_check_types -max_slew -max_capacitance -violators -digits 3 > drv_scan.txt
  set fh [open drv_scan.txt]
  set nets [dict create]
  while {[gets $fh line] >= 0} {
    if {[string match "*VIOLATED*" $line]} {
      set pin [get_pins -quiet [lindex $line 0]]
      if {$pin ne ""} { dict set nets [get_full_name [get_nets -of_objects $pin]] 1 }
    }
  }
  close $fh
  return [dict keys $nets]
}

proc drive_of {name} {
  if {![regexp {X(\d+)(?:P(\d+))?H7[RL]$} $name -> whole frac]} {
    error "no drive strength in cell name $name"
  }
  return [expr {$whole + ($frac eq "" ? 0 : "0.$frac")}]
}

# Give each violating net's driver the least-area stronger cell of the same
# function and threshold flavour that clears it. Adds no net, so the router sees
# the same connectivity; a net no such cell clears keeps its driver.
proc upsize_drivers {dont_use} {
  set changed 0
  foreach net [violating_nets] {
    set drivers [get_pins -quiet -of_objects [get_nets $net] -filter "direction==output"]
    if {[llength $drivers] != 1} continue
    set inst [get_cells -of_objects $drivers]
    set cell [get_property $inst ref_name]
    set own [lindex [get_lib_cells */$cell] 0]
    set area [get_property $own area]
    set candidates {}
    foreach lib_cell [get_lib_cells *] {
      set name [get_name $lib_cell]
      if {[string range $name end-2 end] ne [string range $cell end-2 end]} continue
      set banned 0
      foreach pattern $dont_use { if {[string match $pattern $name]} { set banned 1 } }
      if {$banned || ![sta::equiv_cells $own $lib_cell]} continue
      if {[drive_of $name] <= [drive_of $cell]} continue
      lappend candidates [list [get_property $lib_cell area] [drive_of $name] $name]
    }
    set fixed ""
    foreach candidate [lsort -real -index 0 [lsort -real -index 1 $candidates]] {
      replace_cell $inst [lindex $candidate 2]
      if {[lsearch -exact [violating_nets] $net] < 0} {
        set fixed [lindex $candidate 2]
        break
      }
    }
    if {$fixed eq ""} {
      replace_cell $inst $cell
      puts "upsize: no stronger $cell clears $net"
    } else {
      puts "upsize: [get_full_name $inst] $cell -> $fixed"
      incr changed
    }
  }
  return $changed
}

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
  set_dont_use $dont_use
  estimate_parasitics -placement
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_before.txt
  if {[info exists ::env(MARGIN)]} {
    repair_design -slew_margin $::env(MARGIN) -cap_margin $::env(MARGIN)
    detailed_placement
    check_placement -verbose
    estimate_parasitics -placement
  }
  report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_after.txt
  if {[info exists ::env(UPSIZE_WIRE_SCALE)]} {
    # The MET3 estimate falls short of the routed Cworst extraction, by a median
    # 12% and up to 54% on a detoured net, so the pass sizes against a heavier
    # wire. Upsizing adds no net, so the router's problem stays the one placed.
    set corner [sta::cmd_corner]
    set r [est::wire_signal_resistance $corner]
    set c [expr {[est::wire_signal_capacitance $corner] * $::env(UPSIZE_WIRE_SCALE)}]
    # SI per metre to kohm and pF per micron, read back to prove the units.
    set_wire_rc -resistance [expr {$r * 1e-9}] -capacitance [expr {$c * 1e6}]
    if {abs([est::wire_signal_capacitance $corner] / $c - 1) > 1e-6
        || abs([est::wire_signal_resistance $corner] / $r - 1) > 1e-6} {
      error "set_wire_rc did not take the scaled MET3 values"
    }
    estimate_parasitics -placement
    # Legalising a wider cell can lengthen another net, so size again after it.
    for {set round 0} {$round < 3 && [upsize_drivers $dont_use] > 0} {incr round} {
      detailed_placement
      estimate_parasitics -placement
    }
    check_placement -verbose
    report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3 > drv_upsized.txt
  }
  report_design_area
  write_def $::env(DEF_OUT)
} message]} {
  puts "repair failed: $message"
  exit 1
}
exit 0
