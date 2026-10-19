`default_nettype none

module sequential_16bit_en (
    input wire clk,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    wire rst = io_in[0];
    wire en = io_in[1];
    reg [15:0] ctr;

    always @(posedge clk)
        if (en)
            if (rst) ctr <= 0;
            else ctr <= ctr + 1'b1;
        else ctr <= ctr;

    // Ten pads leave room for the low eight counter bits only.
    assign io_out = {ctr[7:0], 2'b0};
    // Input pads: 0 (rst), 1 (en).
    assign io_oeb = 10'h003;
endmodule
`default_nettype wire
