// SPDX-FileCopyrightText: © 2026 FABulous Contributors
// SPDX-License-Identifier: Apache-2.0

// FABulous tests/fabric_gen_test/integration_test/user_designs/sys_reset.v on
// this harness's pad interface, clocked from the wrapper's GBUF A in place of a
// Global_Clock, which this fabric lacks. rst is a pad, not USER_RESET.
`default_nettype none

module sys_reset (
    input wire clk,
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire rst = io_in[0];
    wire [3:0] a = io_in[4:1];
    wire [3:0] b;

    reg [3:0] data;

    always @(posedge clk) begin
        if (rst) begin
            data <= 4'h7;
        end else begin
            data <= a;
        end
    end

    assign b = data;

    assign io_out = {1'b0, b, 5'b0};
    // Input pads: 0 (rst), 4:1 (a), 9 (unused).
    assign io_oeb = 10'h21F;
endmodule

`default_nettype wire
