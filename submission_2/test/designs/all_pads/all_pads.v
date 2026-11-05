`default_nettype none

// Carries every N_IO and W_IO pad through the fabric in both directions, so a
// dead input, output or output enable on any of the 20 pads fails the compare.
// Pad 0 picks the direction: 1 takes the west pads in and drives the north pads,
// 0 the reverse. The opposite polarity on the two sides tells a pad stuck at the
// level of the other side from one that passes it. An output pad's C pin feeds
// the unselected side of the mux, so at gate level held needs a reset: an X in it
// returns through that pad and the gate-level LUT cannot mask it.
module all_pads (
    input wire clk,
    input wire user_reset,
    input wire [29:0] io_in,
    output wire [29:0] io_out,
    output wire [29:0] io_oeb
);
    wire west_in = io_in[0];
    wire invert = io_in[1];
    wire en = io_in[2];
    wire [9:0] west = io_in[19:10];
    wire [9:0] north = io_in[29:20];
    reg [9:0] held;

    // Enable over reset, the only form that puts user_reset on SR alone; see sequential_16bit_en.
    always @(posedge clk)
        if (en)
            if (user_reset) held <= 0;
            else held <= (west_in ? west : north) ^ {10{invert}};

    assign io_out = {~held, held, held[6:0], 3'b0};
    assign io_oeb = {{10{~west_in}}, {10{west_in}}, 7'b0, 3'b111};
endmodule

`default_nettype wire
