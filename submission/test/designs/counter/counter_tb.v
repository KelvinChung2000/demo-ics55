// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_counter in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py, plus a
// reset-with-enable-low case it lacks.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN counter
`define USER_DESIGN_TB counter_tb

module counter_tb ();
`include "fabric_tb.vh"

    wire [7:0] d = A_IN_top[9:2];

    // pad_in[0] is rst, pad_in[1] is ena.
    task automatic stimulus;
        begin
            pad_in[1:0] = 2'b11;
            repeat (5) compare;
            check(d, 0);
            pad_in[1:0] = 2'b00;
            repeat (5) compare;
            check(d, 0);
            // cocotb reads d on the 17th edge and so sees 16; this compare
            // samples half a cycle after it.
            pad_in[1:0] = 2'b10;
            repeat (17) compare;
            check(d, 17);
            // rst must win over a low ena. ff_map.v maps only enable-over-reset
            // flops, onto a cell whose SR wins over EN, so reset-over-enable
            // reaches it legalised (E = ena | rst).
            pad_in[1:0] = 2'b01;
            repeat (3) compare;
            check(d, 0);
        end
    endtask

endmodule
`default_nettype wire
