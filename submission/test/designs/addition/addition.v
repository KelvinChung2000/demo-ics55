// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/addition.v on
// this harness's pad interface, narrowed from 4 + 4 -> 5 to 3 + 3 -> 4 bits to
// fit ten pads.
`default_nettype none

module addition (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire [2:0] a = io_in[2:0];
    wire [2:0] b = io_in[5:3];
    wire [3:0] c;

    assign c = a + b;

    assign io_out = {c, 6'b0};
    // Input pads: 2:0 (a), 5:3 (b).
    assign io_oeb = 10'h03F;
endmodule

`default_nettype wire
