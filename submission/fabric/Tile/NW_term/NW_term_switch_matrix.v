 // NumberOfConfigBits: 4
module NW_term_switch_matrix
    #(
        parameter NoConfigBits=4
    )
    (
        input  N_GBUF_END0,
        input  N_GBUF_END1,
        input  N_GBUF_END2,
        input  N_GBUF_END3,
        output  S_GBUF_FEED_BEG0,
        output  S_GBUF_FEED_BEG1,
        output  S_GBUF_FEED_BEG2,
        output  S_GBUF_FEED_BEG3,
 //global
        input  [NoConfigBits-1:0] ConfigBits,
        input  [NoConfigBits-1:0] ConfigBits_N
);
parameter GND0 = 1'b0;
parameter GND = 1'b0;
parameter VCC0 = 1'b1;
parameter VCC = 1'b1;
parameter VDD0 = 1'b1;
parameter VDD = 1'b1;

wire[2-1:0] S_GBUF_FEED_BEG0_input;
wire[2-1:0] S_GBUF_FEED_BEG1_input;
wire[2-1:0] S_GBUF_FEED_BEG2_input;
wire[2-1:0] S_GBUF_FEED_BEG3_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer S_GBUF_FEED_BEG0 MUX-2
assign S_GBUF_FEED_BEG0_input = {VCC0,GND0};
cus_mux21 inst_cus_mux21_S_GBUF_FEED_BEG0 (
    .A0(S_GBUF_FEED_BEG0_input[0]),
    .A1(S_GBUF_FEED_BEG0_input[1]),
    .S(ConfigBits[0+0]),
    .X(S_GBUF_FEED_BEG0)
);

 //switch matrix multiplexer S_GBUF_FEED_BEG1 MUX-2
assign S_GBUF_FEED_BEG1_input = {VCC0,GND0};
cus_mux21 inst_cus_mux21_S_GBUF_FEED_BEG1 (
    .A0(S_GBUF_FEED_BEG1_input[0]),
    .A1(S_GBUF_FEED_BEG1_input[1]),
    .S(ConfigBits[1+0]),
    .X(S_GBUF_FEED_BEG1)
);

 //switch matrix multiplexer S_GBUF_FEED_BEG2 MUX-2
assign S_GBUF_FEED_BEG2_input = {VCC0,GND0};
cus_mux21 inst_cus_mux21_S_GBUF_FEED_BEG2 (
    .A0(S_GBUF_FEED_BEG2_input[0]),
    .A1(S_GBUF_FEED_BEG2_input[1]),
    .S(ConfigBits[2+0]),
    .X(S_GBUF_FEED_BEG2)
);

 //switch matrix multiplexer S_GBUF_FEED_BEG3 MUX-2
assign S_GBUF_FEED_BEG3_input = {VCC0,GND0};
cus_mux21 inst_cus_mux21_S_GBUF_FEED_BEG3 (
    .A0(S_GBUF_FEED_BEG3_input[0]),
    .A1(S_GBUF_FEED_BEG3_input[1]),
    .S(ConfigBits[3+0]),
    .X(S_GBUF_FEED_BEG3)
);

endmodule