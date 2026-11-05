# Chip-level constraints for `top`, written by `flow cli chip-top`.
# Load eFPGA_top from the timing model flow/sta/etm.tcl extracts, not from ECC's
# eFPGA_top_Harden.lib, which has no arcs.
create_clock -name CLK -period 10.0 [get_ports PAD_CLK]
# USER_CLK reaches the fabric only through the SW_term global-buffer muxes and has
# no phase relationship with CLK.
create_clock -name USER_CLK -period 10.0 [get_ports PAD_USER_CLK]
set_clock_groups -asynchronous -group CLK -group USER_CLK
# Each clock tree is one pad and a wire, so the pad delay counts from the start.
set_propagated_clock [all_clocks]
set_clock_uncertainty -hold 0.05 [all_clocks]

# Board: a 10 pF load on every driven pad and a 1.0 ns edge into every pad.
set_load 10.0 [all_outputs]
set_input_transition 1.0 [all_inputs]

# Configuration logic: zero board delay, so each path is the pad plus the macro's
# own arc and must fit one CLK period. The host's own delay comes out of the slack.
set_input_delay 0 -clock CLK [get_ports {PAD_UART_RX PAD_RSTN PAD_SPI_CSN PAD_SPI_MOSI PAD_SPI_SCK}]
set_output_delay 0 -clock CLK [get_ports {PAD_UART_ACTIVE PAD_CFG_BUSY PAD_CFG_DONE PAD_CFG_LED}]
# The inputs come from a host on its own clock into synchronisers (SPI a 4-flop
# sampler, Rx one flop, resetn an asynchronous clear), so a hold check against CLK
# describes no real transfer; setup still bounds the pad-to-sampler delay.
set_false_path -hold -from [get_ports {PAD_UART_RX PAD_RSTN PAD_SPI_CSN PAD_SPI_MOSI PAD_SPI_SCK}]

# User IO and the user reset pass through configurable routing, whose timing
# depends on the bitstream, so nothing at chip level times them.
set_input_delay 0 -clock USER_CLK [get_ports {PAD_USER_RESET}]
set_input_delay 0 -clock USER_CLK [get_ports {PAD_IO[*]}]
set_output_delay 0 -clock USER_CLK [get_ports {PAD_IO[*]}]
set_false_path -from [get_ports {PAD_USER_RESET}]
set_false_path -from [get_ports {PAD_IO[*]}]
set_false_path -to [get_ports {PAD_IO[*]}]
