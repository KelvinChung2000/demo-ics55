// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_sys_reset in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN sys_reset
`define USER_DESIGN_TB sys_reset_tb

module sys_reset_tb ();
`include "fabric_tb.vh"

    wire [3:0] b = A_IN_top[8:5];

    // pad_in[0] is rst, pad_in[4:1] is a.
    task automatic stimulus;
        begin
            pad_in[4:0] = {4'h3, 1'b1};
            repeat (5) compare;
            check(b, 4'h7);
            pad_in[4:0] = {4'h5, 1'b0};
            repeat (3) compare;
            check(b, 4'h5);
        end
    endtask

endmodule
`default_nettype wire
