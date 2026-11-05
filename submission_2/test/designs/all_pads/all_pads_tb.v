`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN all_pads
`define USER_DESIGN_TB all_pads_tb
`define DESIGN_PADS 30

module all_pads_tb ();
`include "fabric_tb.vh"

    wire [6:0] east = A_IN_top[9:3];
    wire [9:0] west = A_IN_top[19:10];
    wire [9:0] north = A_IN_top[29:20];

    // Drives value on the input side and checks it one clock later on the output side.
    task automatic transfer(input west_in, input invert, input [9:0] value);
        reg [9:0] held, inverted;
        begin
            pad_in = 0;
            pad_in[0] = west_in;
            pad_in[1] = invert;
            pad_in[2] = 1'b1;
            if (west_in) pad_in[19:10] = value;
            else pad_in[29:20] = value;
            held = value ^ {10{invert}};
            // Inverted at this width: check's wider argument would extend first.
            inverted = ~held;
            compare;
            if (west_in) check(north, inverted);
            else check(west, held);
            check(east, held[6:0]);
        end
    endtask

    task automatic stimulus;
        integer side, bit_i;
        begin
            pad_in[2] = 1'b1;
            user_reset = 1'b1;
            repeat (2) @(negedge CLK);
            user_reset = 1'b0;
            for (side = 0; side < 2; side = side + 1) begin
                // Walking ones and zeros reach every pad at both levels.
                for (bit_i = 0; bit_i < 10; bit_i = bit_i + 1) begin
                    transfer(side[0], 1'b0, 10'd1 << bit_i);
                    transfer(side[0], 1'b0, ~(10'd1 << bit_i));
                end
                transfer(side[0], 1'b1, 10'h155);
                for (i = 0; i < 8; i = i + 1) transfer(side[0], $random(seed), $random(seed));
            end
        end
    endtask

endmodule
`default_nettype wire
