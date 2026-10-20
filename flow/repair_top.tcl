# Post-legalisation DRV and hold repair of eFPGA_top, run by flow.repair.
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
  # iRT detours the frame-strobe nets through the congested top of the strip,
  # 100 to 1000 um routed against a 3 um placed estimate, which repair_design
  # cannot see. Each NOR2B is upsized and a BUFX12H7L (0.29 pF) goes just
  # under the tile pin, so either half of the net can take the detour.
  set strobe_driver NOR2BX6H7L
  set strobe_buffer BUFX12H7L
  set dbu [[ord::get_db_tech] getDbUnitsPerMicron]
  set block [ord::get_db_block]
  set buffer_master [[ord::get_db] findMaster $strobe_buffer]
  set strobes {}
  foreach net [$block getNets] {
    set pins {}
    set drivers {}
    foreach iterm [$net getITerms] {
      set inst [$iterm getInst]
      if {[[$inst getMaster] isBlock]} {
        if {[$iterm isInputSignal] && [string match FrameStrobe* [[$iterm getMTerm] getName]]} {
          lappend pins $iterm
        }
      } elseif {[$iterm isOutputSignal]} {
        lappend drivers $inst
      }
    }
    if {[llength $pins] == 0} { continue }
    if {[llength $pins] != 1 || [llength $drivers] != 1} {
      error "frame strobe [$net getName] has [llength $pins] tile pins and [llength $drivers] drivers"
    }
    lappend strobes [list [$net getName] [lindex $drivers 0] [lindex $pins 0]]
  }
  if {[llength $strobes] == 0} { error "no top-level frame-strobe net found" }
  foreach strobe $strobes {
    lassign $strobe name driver pin
    set master [[$driver getMaster] getName]
    if {![string match NOR2BX*H7L $master]} {
      error "frame strobe $name is driven by $master, not a NOR2B"
    }
    replace_cell [$driver getName] $strobe_driver
    # insert_buffer segfaults on a macro load pin here, so the buffer is
    # made in odb; detailed_placement legalises it below.
    set tile_net [odb::dbNet_create $block "${name}_tile"]
    if {$tile_net eq "NULL"} { error "net ${name}_tile already exists" }
    set buffer [odb::dbInst_create $block $buffer_master "${name}_tile_buffer"]
    $pin disconnect
    $pin connect $tile_net
    [$buffer findITerm A] connect [$block findNet $name]
    [$buffer findITerm Y] connect $tile_net
    set box [$pin getBBox]
    $buffer setLocation [expr {([$box xMin] + [$box xMax]) / 2}] [expr {[$box yMin] - 3 * $dbu}]
    $buffer setPlacementStatus PLACED
  }
  puts "frame strobes: [llength $strobes] drivers sized to $strobe_driver, each buffered by $strobe_buffer"
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
