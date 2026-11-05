// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/all_zeros.v on
// this harness's pad interface.
`default_nettype none

module all_zeros (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire [3:0] all;

    assign all = '0;

    assign io_out = {6'b0, all};
    // Input pads: 9:4 (unused).
    assign io_oeb = 10'h3F0;
endmodule

`default_nettype wire
