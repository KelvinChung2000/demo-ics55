// The user clock pad. Its only fabric connection is the SW_term global-buffer
// input muxes, so a user design reaches it through a GBUF.

module USER_CLK (
    // Fabric side
    output CLK,

    // External side
    (* FABulous, EXTERNAL *) input  CLK_top
);

    assign CLK = CLK_top;

endmodule
