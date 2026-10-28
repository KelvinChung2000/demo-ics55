`default_nettype none

// sequential_16bit_en with its pads as top-level ports, placed by
// sequential_16bit_en_pcf.pcf instead of IOBUF instances in a wrapper. pad[i]
// is the bit eFPGA_top exposes as A_*_top[i], so the same testbench applies.
module sequential_16bit_en_pcf (
    inout wire [9:0] pad
);
    wire [9:0] io_out, io_oeb;
    wire clk_pad, clk, reset_pad, reset;

    // The USER_CLK and USER_RESET pads reach the fabric only through the
    // SW_term global buffers. GBUF A is pinned for the clock because a counter
    // clocked through GBUF C stays X in simulation; B and D are untested as clocks.
    (* keep, BEL="X0Y11.F" *) USER_CLK clk_pad_i (
        .CLOCK(clk_pad)
    );
    (* keep, BEL="X0Y11.A" *) GBUF clk_buf_i (
        .IN (clk_pad),
        .OUT(clk)
    );
    (* keep, BEL="X0Y11.E" *) SYS_RESET reset_pad_i (
        .RESET(reset_pad)
    );
    (* keep, BEL="X0Y11.B" *) GBUF reset_buf_i (
        .IN (reset_pad),
        .OUT(reset)
    );

    sequential_16bit_en top_i (
        .clk   (clk),
        .user_reset(reset),
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
