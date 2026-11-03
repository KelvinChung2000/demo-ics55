`default_nettype none

// The synthesis top of every design in designs/. Its pads are top-level ports,
// placed by pads.pcf: pad[i] is the bit eFPGA_top exposes as A_*_top[i], so
// the testbench compares the same pads the design drives.
module pcf_top (
    inout wire [9:0] pad
);
    wire [9:0] io_in, io_out, io_oeb;
    wire clk_pad, clk, reset_pad, reset;

    // No UserCLK in this fabric: the USER_CLK and USER_RESET pads reach it only
    // through the SW_term global buffers, the clock into each tile's GCLK and
    // the reset into each tile's GSR. GBUF A and B carry them, or C and D with
    // -D GBUF_CD, so a test can cover all four global nets.
`ifdef GBUF_CD
    `define CLK_GBUF_BEL "X0Y11.C"
    `define RESET_GBUF_BEL "X0Y11.D"
`else
    `define CLK_GBUF_BEL "X0Y11.A"
    `define RESET_GBUF_BEL "X0Y11.B"
`endif
    (* keep, BEL="X0Y11.F" *) USER_CLK clk_pad_i (
        .CLOCK(clk_pad)
    );
    (* keep, BEL=`CLK_GBUF_BEL *) GBUF clk_buf_i (
        .IN (clk_pad),
        .OUT(clk)
    );
    (* keep, BEL="X0Y11.E" *) SYS_RESET reset_pad_i (
        .RESET(reset_pad)
    );
    (* keep, BEL=`RESET_GBUF_BEL *) GBUF reset_buf_i (
        .IN (reset_pad),
        .OUT(reset)
    );

    // USER_DESIGN names the design; run-yosys passes -D USER_DESIGN=<DESIGN>.
    `USER_DESIGN top_i (
        .clk       (clk),
        .user_reset(reset),
        .io_in     (io_in),
        .io_out    (io_out),
        .io_oeb    (io_oeb)
    );

    // One IOBUF per pad rather than an inferred tristate: a design wiring one
    // pad straight to another aliases the two inout bits, and Yosys then picks
    // the pad directions from the alias instead of io_oeb. IOBUF.EN is an
    // active-high output enable.
    genvar i;
    for (i = 0; i < 10; i = i + 1) begin : g_pad
        IOBUF io_i (
            .PAD(pad[i]),
            .OUT(io_in[i]),
            .IN (io_out[i]),
            .EN (~io_oeb[i])
        );
    end
endmodule

`default_nettype wire
