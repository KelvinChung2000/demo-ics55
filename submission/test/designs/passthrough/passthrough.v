// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/passthrough.v
// on this harness's pad interface.
`default_nettype none

module passthrough (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire [3:0] a = io_in[3:0];
    wire [3:0] b;

    assign b = a;

    assign io_out = {2'b0, b, 4'b0};
    // Input pads: 3:0 (a), 9:8 (unused).
    assign io_oeb = 10'h30F;
endmodule

`default_nettype wire
