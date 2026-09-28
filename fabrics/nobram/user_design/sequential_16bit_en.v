`default_nettype none

module sequential_16bit_en (
    input wire clk,
    input wire [39:0] io_in,
    output wire [39:0] io_out,
    output wire [39:0] io_oeb
);
    wire rst = io_in[0];
    wire en = io_in[1];
    reg [15:0] ctr;

    always @(posedge clk)
        if (en)
            if (rst) ctr <= 0;
            else ctr <= ctr + 1'b1;
        else ctr <= ctr;

    assign io_out = {24'b0, ctr};
    // Input pads: 0 (rst), 1 (en), 16 (clk, routed to the GBUF in top_wrapper).
    assign io_oeb = 40'h00_0001_0003;
endmodule
`default_nettype wire
