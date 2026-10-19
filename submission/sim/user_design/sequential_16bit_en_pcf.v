`default_nettype none

// sequential_16bit_en with its pads as top-level ports, placed by
// sequential_16bit_en_pcf.pcf instead of IOBUF instances in a wrapper. pad[i]
// is the bit eFPGA_top exposes as A_*_top[i], so the same testbench applies.
module sequential_16bit_en_pcf (
    inout wire [39:0] pad
);
    wire [39:0] io_out, io_oeb;
    wire clk;

    // The clock enters on pad 16 and reaches the fabric only through a GBUF.
    // GBUF A is pinned because a counter clocked through GBUF C stays X in
    // simulation; the other GBUFs are untested.
    (* keep, BEL="X0Y11.A" *) GBUF clk_buf_i (
        .IN (pad[16]),
        .OUT(clk)
    );

    sequential_16bit_en top_i (
        .clk   (clk),
        .io_in (pad),
        .io_out(io_out),
        .io_oeb(io_oeb)
    );

    genvar i;
    for (i = 0; i < 40; i = i + 1) begin : g_pad
        assign pad[i] = io_oeb[i] ? 1'bz : io_out[i];
    end
endmodule

`default_nettype wire
