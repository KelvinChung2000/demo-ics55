`default_nettype none

module sequential_16bit_en (
    input wire clk,
    // Synchronous; the fabric takes it from the USER_RESET pad.
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire rst = io_in[0];
    wire en = io_in[1];
    reg [15:0] ctr;

    // A GBUF reaches a cell only on its CLK, SR (through GSR) or EN pin, never a
    // LUT input, so user_reset must map alone onto SR. synth_fabulous -complex-dff
    // maps only enable-over-reset flops, hence user_reset under en and rst as a
    // mask. The cell itself gives SR priority over EN, so the fabric clears even
    // with en low; the testbench holds en high across the reset.
    always @(posedge clk)
        if (en)
            if (user_reset) ctr <= 0;
            else ctr <= (ctr + 1'b1) & {16{~rst}};

    // Ten pads leave room for the low eight counter bits only.
    assign io_out = {ctr[7:0], 2'b0};
    // Input pads: 0 (rst), 1 (en).
    assign io_oeb = 10'h003;
endmodule
`default_nettype wire
