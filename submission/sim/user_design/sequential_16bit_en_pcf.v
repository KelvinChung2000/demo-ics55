`default_nettype none

// sequential_16bit_en with its pads as top-level ports, placed by
// sequential_16bit_en_pcf.pcf instead of IOBUF instances in a wrapper. pad[i]
// is the bit eFPGA_top exposes as A_*_top[i], so the same testbench applies.
module sequential_16bit_en_pcf (
    inout wire [9:0] pad
);
    wire [9:0] io_out, io_oeb;
    wire clk_pad, clk;

    // The clock enters on the SYS_RESET pad, whose only fabric connection is
    // the SW_term global buffers. GBUF A is pinned because a counter clocked
    // through GBUF C stays X in simulation; the other GBUFs are untested.
    (* keep, BEL="X0Y11.E" *) SYS_RESET clk_pad_i (
        .RESET(clk_pad)
    );
    (* keep, BEL="X0Y11.A" *) GBUF clk_buf_i (
        .IN (clk_pad),
        .OUT(clk)
    );

    sequential_16bit_en top_i (
        .clk   (clk),
        .io_in (pad),
        .io_out(io_out),
        .io_oeb(io_oeb)
    );

    genvar i;
    for (i = 0; i < 10; i = i + 1) begin : g_pad
        assign pad[i] = io_oeb[i] ? 1'bz : io_out[i];
    end
endmodule

`default_nettype wire
