// The user clock pad. Its only fabric connection is the SW_term global-buffer
// input muxes, so a user design reaches it through a GBUF. FABulous's bit_gen
// drops every FASM feature whose name contains "CLK", so neither these ports nor
// the BEL prefix may spell it, or the mux selecting this pad is never written.

module USER_CLK (
    // Fabric side
    output CLOCK,

    // External side
    (* FABulous, EXTERNAL *) input  CLOCK_top
);

    assign CLOCK = CLOCK_top;

endmodule
