# Chip-level STA of top.v: the ICS55 IO pads around the eFPGA_top model that
# etm.tcl extracts, constrained by top.sdc. Run in <build>/chip after
# `flow cli chip-top` and etm.tcl.
# env: PDK, IOC (IO liberty corner), LIBC (standard-cell corner, for the buffers
#      and tie cells of a foundry top.v), TAG (corner name of the model)
set IO $::env(PDK)/IP/IO/ICsprout_55LLULP1233_IO_251013
set L $::env(PDK)/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
read_liberty $IO/liberty/ICSIOA_N55_3P3_$::env(IOC).lib
read_liberty $L/ics55_LLSC_H7CR/liberty/ics55_LLSC_H7CR_$::env(LIBC)_nldm.lib
read_liberty $L/ics55_LLSC_H7CL/liberty/ics55_LLSC_H7CL_$::env(LIBC)_nldm.lib
read_liberty etm/eFPGA_top_$::env(TAG).lib
read_verilog top.v
link_design top
read_sdc top.sdc
check_setup -verbose
report_checks -path_delay max -group_path_count 9 -endpoint_path_count 1 -format end -digits 3
report_checks -path_delay min -group_path_count 9 -endpoint_path_count 1 -format end -digits 3
report_checks -path_delay max -to [get_ports PAD_CFG_DONE] -format full_clock_expanded -digits 3
report_checks -path_delay max -from [get_ports PAD_SPI_MOSI] -format full_clock_expanded -digits 3
report_check_types -max_slew -max_capacitance -max_fanout -violators
