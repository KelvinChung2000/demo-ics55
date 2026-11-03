// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_multiplication in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN multiplication
`define USER_DESIGN_TB multiplication_tb

module multiplication_tb ();
`include "fabric_tb.vh"

    wire [2:0] mult_a = pad_in[2:0];
    wire [1:0] mult_b = pad_in[4:3];
    wire [4:0] product = A_IN_top[9:5];

    task automatic stimulus;
        begin
            for (i = 0; i < 32; i = i + 1) begin
                pad_in[4:0] = $random(seed);
                compare;
                check(product, mult_a * mult_b);
            end
        end
    endtask

endmodule
`default_nettype wire
