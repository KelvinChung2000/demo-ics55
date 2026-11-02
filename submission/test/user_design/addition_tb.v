// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_addition in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN addition
`define USER_DESIGN_TB addition_tb

module addition_tb ();
`include "fabric_tb.vh"

    wire [2:0] a = pad_in[2:0];
    wire [2:0] b_in = pad_in[5:3];
    wire [3:0] c = A_IN_top[9:6];

    task automatic stimulus;
        begin
            for (i = 0; i < 32; i = i + 1) begin
                pad_in[5:0] = $random(seed);
                compare;
                check(c, a + b_in);
            end
        end
    endtask

endmodule
`default_nettype wire
