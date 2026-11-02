// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_all_zeros in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py.
// At gate level gen_gl_top.py forces every logic cell with a constant config
// to that constant, and here those are all the used cells, so the GL runs
// test only the routing and the pads.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN all_zeros
`define USER_DESIGN_TB all_zeros_tb

module all_zeros_tb ();
`include "fabric_tb.vh"

    wire [3:0] all = A_IN_top[3:0];

    task automatic stimulus;
        begin
            for (i = 0; i < 4; i = i + 1) begin
                compare;
                check(all, 4'h0);
            end
        end
    endtask

endmodule
`default_nettype wire
