// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/counter.v on
// this harness's pad interface, clocked from the wrapper's GBUF A in place of a
// Global_Clock, which this fabric lacks.
`default_nettype none

module counter (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire rst = io_in[0];
    wire ena = io_in[1];
    wire [7:0] d;

    reg [7:0] ctr;

    always @(posedge clk) begin
        if (rst) begin
            ctr <= '0;
        end else if (ena) begin
            ctr <= ctr + 1'b1;
        end
    end

    assign d = ctr;

    assign io_out = {d, 2'b0};
    // Input pads: 0 (rst), 1 (ena).
    assign io_oeb = 10'h003;
endmodule

`default_nettype wire
