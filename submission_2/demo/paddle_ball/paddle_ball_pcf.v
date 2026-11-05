`default_nettype none

// paddle_ball with its pads as named top-level ports, placed by
// paddle_ball.pcf. synth_fabulous inserts a pad cell on each port and
// iobuf_map.v turns it into this fabric's IOBUF.
module paddle_ball_pcf (
    output wire hsync_n,
    output wire vsync_n,
    output wire red,
    output wire green,
    output wire blue,
    input wire p1_up,
    input wire p1_down,
    input wire p2_up,
    input wire p2_down,
    output wire sound
);
    // The USER_CLK and USER_RESET pads reach the fabric only through the
    // SW_term global buffers, the clock on GBUF A into each tile's GCLK and the
    // reset on GBUF B into each tile's GSR.
    wire clk_pad, clk, reset_pad, reset;
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

    wire [9:0] io_out;
    paddle_ball game_i (
        .clk(clk),
        .user_reset(reset),
        .io_in({1'b0, p2_down, p2_up, p1_down, p1_up, 5'b00000}),
        .io_out(io_out),
        .io_oeb()
    );
    assign {sound, blue, green, red, vsync_n, hsync_n} = {io_out[9], io_out[4:0]};
endmodule

`default_nettype wire
