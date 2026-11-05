`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN sequential_16bit_en
`define USER_DESIGN_TB sequential_16bit_en_tb

module sequential_16bit_en_tb ();
`include "fabric_tb.vh"

    // The counter's low eight bits on pads 9:2, as one value for a waveform
    // viewer. At the chip pads A_IN_top[1:0] reads back en and rst instead.
    wire [7:0] count      = A_IN_top[9:2];
    wire [7:0] count_gold = A_IN_top_gold[9:2];

    task automatic stimulus;
        begin
            // Enable and reset the counter
            pad_in[1:0] = 2'b11;
            repeat (5) @(negedge CLK);
            // Deassert reset while keeping the counter enabled
            pad_in[1:0] = 2'b10;
            for (i = 0; i < 100; i = i + 1) compare;
            $display("count: %0d of %0d compares match", compares - mismatches, compares);
            // USER_RESET clears the counter through GBUF B and GSR while it counts.
            user_reset = 1'b1;
            for (i = 0; i < 3; i = i + 1) compare;
            if (A_IN_top_gold[9:2] !== 8'd0) begin
                $display("Error: the reference counter did not clear under USER_RESET");
                have_errors = 1'b1;
            end
            user_reset = 1'b0;
            for (i = 0; i < 20; i = i + 1) compare;
        end
    endtask

endmodule
`default_nettype wire
