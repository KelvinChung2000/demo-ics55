// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// Stimulus of cocotb_test_passthrough in FABulous
// tests/fabric_gen_test/integration_test/test_designs_pattern.py.
`timescale 1ps / 1ps
`default_nettype none
`define USER_DESIGN passthrough
`define USER_DESIGN_TB passthrough_tb

module passthrough_tb ();
`include "fabric_tb.vh"

    wire [3:0] b = A_IN_top[7:4];

    task automatic stimulus;
        integer bit_i, value;
        begin
            // Walking ones and zeros: one bit of a set, the rest clear.
            for (bit_i = 0; bit_i < 4; bit_i = bit_i + 1)
                for (value = 0; value < 2; value = value + 1) begin
                    pad_in[3:0] = value[0] << bit_i;
                    compare;
                    check(b, pad_in[3:0]);
                end
            for (i = 0; i < 16; i = i + 1) begin
                pad_in[3:0] = $random(seed);
                compare;
                check(b, pad_in[3:0]);
            end
        end
    endtask

endmodule
`default_nettype wire
