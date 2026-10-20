# The routed eFPGA_top as a Verilog netlist for OpenSTA. env: PDK, MACROS, DEF
set S $::env(PDK)/IP/STD_cell/ics55_LLSC_H7C_V1p10C100
read_lef $::env(PDK)/prtech/techLEF/N551P6M_ecos.lef
read_lef $S/ics55_LLSC_H7CR/lef/ics55_LLSC_H7CR_ecos.lef
read_lef $S/ics55_LLSC_H7CL/lef/ics55_LLSC_H7CL_ecos.lef
foreach f [glob $::env(MACROS)/*/*_Harden.lef] { read_lef $f }
read_def $::env(DEF)
write_verilog top_full.v
exit
