// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/multiplication.v
// on this harness's pad interface, narrowed from 3 x 3 -> 6 to 3 x 2 -> 5 bits
// to fit ten pads.
`default_nettype none

module multiplication (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire [2:0] mult_a = io_in[2:0];
    wire [1:0] mult_b = io_in[4:3];
    wire [4:0] product;

    assign product = mult_a * mult_b;

    assign io_out = {product, 5'b0};
    // Input pads: 2:0 (mult_a), 4:3 (mult_b).
    assign io_oeb = 10'h01F;
endmodule

`default_nettype wire
