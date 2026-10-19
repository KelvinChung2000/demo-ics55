 // NumberOfConfigBits: 117
module E_IO_switch_matrix
    #(
        parameter NoConfigBits=117
    )
    (
        input  N_GBUF_END0,
        input  N_GBUF_END1,
        input  N_GBUF_END2,
        input  N_GBUF_END3,
        input  E1END0,
        input  E1END1,
        input  E1END2,
        input  E1END3,
        input  E2MID0,
        input  E2MID1,
        input  E2MID2,
        input  E2MID3,
        input  E2MID4,
        input  E2MID5,
        input  E2MID6,
        input  E2MID7,
        input  E2END0,
        input  E2END1,
        input  E2END2,
        input  E2END3,
        input  E2END4,
        input  E2END5,
        input  E2END6,
        input  E2END7,
        input  EE4END0,
        input  EE4END1,
        input  EE4END2,
        input  EE4END3,
        input  EE4END4,
        input  EE4END5,
        input  EE4END6,
        input  EE4END7,
        input  EE4END8,
        input  EE4END9,
        input  EE4END10,
        input  EE4END11,
        input  EE4END12,
        input  EE4END13,
        input  EE4END14,
        input  EE4END15,
        input  E6END0,
        input  E6END1,
        input  E6END2,
        input  E6END3,
        input  E6END4,
        input  E6END5,
        input  E6END6,
        input  E6END7,
        input  E6END8,
        input  E6END9,
        input  E6END10,
        input  E6END11,
        input  A_OUT,
        output  N_GBUF_BEG0,
        output  N_GBUF_BEG1,
        output  N_GBUF_BEG2,
        output  N_GBUF_BEG3,
        output  W1BEG0,
        output  W1BEG1,
        output  W1BEG2,
        output  W1BEG3,
        output  W2BEG0,
        output  W2BEG1,
        output  W2BEG2,
        output  W2BEG3,
        output  W2BEG4,
        output  W2BEG5,
        output  W2BEG6,
        output  W2BEG7,
        output  W2BEGb0,
        output  W2BEGb1,
        output  W2BEGb2,
        output  W2BEGb3,
        output  W2BEGb4,
        output  W2BEGb5,
        output  W2BEGb6,
        output  W2BEGb7,
        output  WW4BEG0,
        output  WW4BEG1,
        output  WW4BEG2,
        output  WW4BEG3,
        output  WW4BEG4,
        output  WW4BEG5,
        output  WW4BEG6,
        output  WW4BEG7,
        output  WW4BEG8,
        output  WW4BEG9,
        output  WW4BEG10,
        output  WW4BEG11,
        output  WW4BEG12,
        output  WW4BEG13,
        output  WW4BEG14,
        output  WW4BEG15,
        output  W6BEG0,
        output  W6BEG1,
        output  W6BEG2,
        output  W6BEG3,
        output  W6BEG4,
        output  W6BEG5,
        output  W6BEG6,
        output  W6BEG7,
        output  W6BEG8,
        output  W6BEG9,
        output  W6BEG10,
        output  W6BEG11,
        output  A_CLK,
        output  A_IN,
        output  A_EN,
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

wire[2-1:0] W1BEG0_input;
wire[2-1:0] W1BEG1_input;
wire[2-1:0] W1BEG2_input;
wire[2-1:0] W1BEG3_input;
wire[5-1:0] W2BEG0_input;
wire[5-1:0] W2BEG1_input;
wire[5-1:0] W2BEG2_input;
wire[5-1:0] W2BEG3_input;
wire[5-1:0] W2BEG4_input;
wire[5-1:0] W2BEG5_input;
wire[5-1:0] W2BEG6_input;
wire[5-1:0] W2BEG7_input;
wire[5-1:0] W2BEGb0_input;
wire[5-1:0] W2BEGb1_input;
wire[5-1:0] W2BEGb2_input;
wire[5-1:0] W2BEGb3_input;
wire[5-1:0] W2BEGb4_input;
wire[5-1:0] W2BEGb5_input;
wire[5-1:0] W2BEGb6_input;
wire[5-1:0] W2BEGb7_input;
wire[4-1:0] WW4BEG0_input;
wire[4-1:0] WW4BEG1_input;
wire[4-1:0] WW4BEG2_input;
wire[4-1:0] WW4BEG3_input;
wire[4-1:0] WW4BEG4_input;
wire[4-1:0] WW4BEG5_input;
wire[4-1:0] WW4BEG6_input;
wire[4-1:0] WW4BEG7_input;
wire[4-1:0] WW4BEG8_input;
wire[4-1:0] WW4BEG9_input;
wire[4-1:0] WW4BEG10_input;
wire[4-1:0] WW4BEG11_input;
wire[4-1:0] WW4BEG12_input;
wire[4-1:0] WW4BEG13_input;
wire[4-1:0] WW4BEG14_input;
wire[4-1:0] WW4BEG15_input;
wire[4-1:0] W6BEG0_input;
wire[4-1:0] W6BEG1_input;
wire[4-1:0] W6BEG2_input;
wire[4-1:0] W6BEG3_input;
wire[4-1:0] W6BEG4_input;
wire[4-1:0] W6BEG5_input;
wire[4-1:0] W6BEG6_input;
wire[4-1:0] W6BEG7_input;
wire[4-1:0] W6BEG8_input;
wire[4-1:0] W6BEG9_input;
wire[4-1:0] W6BEG10_input;
wire[4-1:0] W6BEG11_input;
wire[4-1:0] A_CLK_input;
wire[16-1:0] A_IN_input;
wire[8-1:0] A_EN_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer N_GBUF_BEG0 MUX-1
assign N_GBUF_BEG0 = N_GBUF_END0;

 //switch matrix multiplexer N_GBUF_BEG1 MUX-1
assign N_GBUF_BEG1 = N_GBUF_END1;

 //switch matrix multiplexer N_GBUF_BEG2 MUX-1
assign N_GBUF_BEG2 = N_GBUF_END2;

 //switch matrix multiplexer N_GBUF_BEG3 MUX-1
assign N_GBUF_BEG3 = N_GBUF_END3;

 //switch matrix multiplexer W1BEG0 MUX-2
assign W1BEG0_input = {A_OUT,E1END3};
cus_mux21 inst_cus_mux21_W1BEG0 (
    .A0(W1BEG0_input[0]),
    .A1(W1BEG0_input[1]),
    .S(ConfigBits[0+0]),
    .X(W1BEG0)
);

 //switch matrix multiplexer W1BEG1 MUX-2
assign W1BEG1_input = {A_OUT,E1END2};
cus_mux21 inst_cus_mux21_W1BEG1 (
    .A0(W1BEG1_input[0]),
    .A1(W1BEG1_input[1]),
    .S(ConfigBits[1+0]),
    .X(W1BEG1)
);

 //switch matrix multiplexer W1BEG2 MUX-2
assign W1BEG2_input = {A_OUT,E1END1};
cus_mux21 inst_cus_mux21_W1BEG2 (
    .A0(W1BEG2_input[0]),
    .A1(W1BEG2_input[1]),
    .S(ConfigBits[2+0]),
    .X(W1BEG2)
);

 //switch matrix multiplexer W1BEG3 MUX-2
assign W1BEG3_input = {A_OUT,E1END0};
cus_mux21 inst_cus_mux21_W1BEG3 (
    .A0(W1BEG3_input[0]),
    .A1(W1BEG3_input[1]),
    .S(ConfigBits[3+0]),
    .X(W1BEG3)
);

 //switch matrix multiplexer W2BEG0 MUX-5
assign W2BEG0_input = {A_OUT,E6END7,EE4END15,EE4END7,E2MID7};
cus_mux81 inst_cus_mux81_W2BEG0 (
    .A0(W2BEG0_input[0]),
    .A1(W2BEG0_input[1]),
    .A2(W2BEG0_input[2]),
    .A3(W2BEG0_input[3]),
    .A4(W2BEG0_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[4+0]),
    .S0N(ConfigBits_N[4+0]),
    .S1(ConfigBits[4+1]),
    .S1N(ConfigBits_N[4+1]),
    .S2(ConfigBits[4+2]),
    .S2N(ConfigBits_N[4+2]),
    .X(W2BEG0)
);

 //switch matrix multiplexer W2BEG1 MUX-5
assign W2BEG1_input = {A_OUT,E6END6,EE4END14,EE4END6,E2MID6};
cus_mux81 inst_cus_mux81_W2BEG1 (
    .A0(W2BEG1_input[0]),
    .A1(W2BEG1_input[1]),
    .A2(W2BEG1_input[2]),
    .A3(W2BEG1_input[3]),
    .A4(W2BEG1_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[7+0]),
    .S0N(ConfigBits_N[7+0]),
    .S1(ConfigBits[7+1]),
    .S1N(ConfigBits_N[7+1]),
    .S2(ConfigBits[7+2]),
    .S2N(ConfigBits_N[7+2]),
    .X(W2BEG1)
);

 //switch matrix multiplexer W2BEG2 MUX-5
assign W2BEG2_input = {A_OUT,E6END5,EE4END13,EE4END5,E2MID5};
cus_mux81 inst_cus_mux81_W2BEG2 (
    .A0(W2BEG2_input[0]),
    .A1(W2BEG2_input[1]),
    .A2(W2BEG2_input[2]),
    .A3(W2BEG2_input[3]),
    .A4(W2BEG2_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[10+0]),
    .S0N(ConfigBits_N[10+0]),
    .S1(ConfigBits[10+1]),
    .S1N(ConfigBits_N[10+1]),
    .S2(ConfigBits[10+2]),
    .S2N(ConfigBits_N[10+2]),
    .X(W2BEG2)
);

 //switch matrix multiplexer W2BEG3 MUX-5
assign W2BEG3_input = {A_OUT,E6END4,EE4END12,EE4END4,E2MID4};
cus_mux81 inst_cus_mux81_W2BEG3 (
    .A0(W2BEG3_input[0]),
    .A1(W2BEG3_input[1]),
    .A2(W2BEG3_input[2]),
    .A3(W2BEG3_input[3]),
    .A4(W2BEG3_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[13+0]),
    .S0N(ConfigBits_N[13+0]),
    .S1(ConfigBits[13+1]),
    .S1N(ConfigBits_N[13+1]),
    .S2(ConfigBits[13+2]),
    .S2N(ConfigBits_N[13+2]),
    .X(W2BEG3)
);

 //switch matrix multiplexer W2BEG4 MUX-5
assign W2BEG4_input = {A_OUT,E6END3,EE4END11,EE4END3,E2MID3};
cus_mux81 inst_cus_mux81_W2BEG4 (
    .A0(W2BEG4_input[0]),
    .A1(W2BEG4_input[1]),
    .A2(W2BEG4_input[2]),
    .A3(W2BEG4_input[3]),
    .A4(W2BEG4_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[16+0]),
    .S0N(ConfigBits_N[16+0]),
    .S1(ConfigBits[16+1]),
    .S1N(ConfigBits_N[16+1]),
    .S2(ConfigBits[16+2]),
    .S2N(ConfigBits_N[16+2]),
    .X(W2BEG4)
);

 //switch matrix multiplexer W2BEG5 MUX-5
assign W2BEG5_input = {A_OUT,E6END2,EE4END10,EE4END2,E2MID2};
cus_mux81 inst_cus_mux81_W2BEG5 (
    .A0(W2BEG5_input[0]),
    .A1(W2BEG5_input[1]),
    .A2(W2BEG5_input[2]),
    .A3(W2BEG5_input[3]),
    .A4(W2BEG5_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[19+0]),
    .S0N(ConfigBits_N[19+0]),
    .S1(ConfigBits[19+1]),
    .S1N(ConfigBits_N[19+1]),
    .S2(ConfigBits[19+2]),
    .S2N(ConfigBits_N[19+2]),
    .X(W2BEG5)
);

 //switch matrix multiplexer W2BEG6 MUX-5
assign W2BEG6_input = {A_OUT,E6END1,EE4END9,EE4END1,E2MID1};
cus_mux81 inst_cus_mux81_W2BEG6 (
    .A0(W2BEG6_input[0]),
    .A1(W2BEG6_input[1]),
    .A2(W2BEG6_input[2]),
    .A3(W2BEG6_input[3]),
    .A4(W2BEG6_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[22+0]),
    .S0N(ConfigBits_N[22+0]),
    .S1(ConfigBits[22+1]),
    .S1N(ConfigBits_N[22+1]),
    .S2(ConfigBits[22+2]),
    .S2N(ConfigBits_N[22+2]),
    .X(W2BEG6)
);

 //switch matrix multiplexer W2BEG7 MUX-5
assign W2BEG7_input = {A_OUT,E6END0,EE4END8,EE4END0,E2MID0};
cus_mux81 inst_cus_mux81_W2BEG7 (
    .A0(W2BEG7_input[0]),
    .A1(W2BEG7_input[1]),
    .A2(W2BEG7_input[2]),
    .A3(W2BEG7_input[3]),
    .A4(W2BEG7_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[25+0]),
    .S0N(ConfigBits_N[25+0]),
    .S1(ConfigBits[25+1]),
    .S1N(ConfigBits_N[25+1]),
    .S2(ConfigBits[25+2]),
    .S2N(ConfigBits_N[25+2]),
    .X(W2BEG7)
);

 //switch matrix multiplexer W2BEGb0 MUX-5
assign W2BEGb0_input = {A_OUT,E6END7,EE4END15,EE4END7,E2END7};
cus_mux81 inst_cus_mux81_W2BEGb0 (
    .A0(W2BEGb0_input[0]),
    .A1(W2BEGb0_input[1]),
    .A2(W2BEGb0_input[2]),
    .A3(W2BEGb0_input[3]),
    .A4(W2BEGb0_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[28+0]),
    .S0N(ConfigBits_N[28+0]),
    .S1(ConfigBits[28+1]),
    .S1N(ConfigBits_N[28+1]),
    .S2(ConfigBits[28+2]),
    .S2N(ConfigBits_N[28+2]),
    .X(W2BEGb0)
);

 //switch matrix multiplexer W2BEGb1 MUX-5
assign W2BEGb1_input = {A_OUT,E6END6,EE4END14,EE4END6,E2END6};
cus_mux81 inst_cus_mux81_W2BEGb1 (
    .A0(W2BEGb1_input[0]),
    .A1(W2BEGb1_input[1]),
    .A2(W2BEGb1_input[2]),
    .A3(W2BEGb1_input[3]),
    .A4(W2BEGb1_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[31+0]),
    .S0N(ConfigBits_N[31+0]),
    .S1(ConfigBits[31+1]),
    .S1N(ConfigBits_N[31+1]),
    .S2(ConfigBits[31+2]),
    .S2N(ConfigBits_N[31+2]),
    .X(W2BEGb1)
);

 //switch matrix multiplexer W2BEGb2 MUX-5
assign W2BEGb2_input = {A_OUT,E6END5,EE4END13,EE4END5,E2END5};
cus_mux81 inst_cus_mux81_W2BEGb2 (
    .A0(W2BEGb2_input[0]),
    .A1(W2BEGb2_input[1]),
    .A2(W2BEGb2_input[2]),
    .A3(W2BEGb2_input[3]),
    .A4(W2BEGb2_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[34+0]),
    .S0N(ConfigBits_N[34+0]),
    .S1(ConfigBits[34+1]),
    .S1N(ConfigBits_N[34+1]),
    .S2(ConfigBits[34+2]),
    .S2N(ConfigBits_N[34+2]),
    .X(W2BEGb2)
);

 //switch matrix multiplexer W2BEGb3 MUX-5
assign W2BEGb3_input = {A_OUT,E6END4,EE4END12,EE4END4,E2END4};
cus_mux81 inst_cus_mux81_W2BEGb3 (
    .A0(W2BEGb3_input[0]),
    .A1(W2BEGb3_input[1]),
    .A2(W2BEGb3_input[2]),
    .A3(W2BEGb3_input[3]),
    .A4(W2BEGb3_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[37+0]),
    .S0N(ConfigBits_N[37+0]),
    .S1(ConfigBits[37+1]),
    .S1N(ConfigBits_N[37+1]),
    .S2(ConfigBits[37+2]),
    .S2N(ConfigBits_N[37+2]),
    .X(W2BEGb3)
);

 //switch matrix multiplexer W2BEGb4 MUX-5
assign W2BEGb4_input = {A_OUT,E6END3,EE4END11,EE4END3,E2END3};
cus_mux81 inst_cus_mux81_W2BEGb4 (
    .A0(W2BEGb4_input[0]),
    .A1(W2BEGb4_input[1]),
    .A2(W2BEGb4_input[2]),
    .A3(W2BEGb4_input[3]),
    .A4(W2BEGb4_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[40+0]),
    .S0N(ConfigBits_N[40+0]),
    .S1(ConfigBits[40+1]),
    .S1N(ConfigBits_N[40+1]),
    .S2(ConfigBits[40+2]),
    .S2N(ConfigBits_N[40+2]),
    .X(W2BEGb4)
);

 //switch matrix multiplexer W2BEGb5 MUX-5
assign W2BEGb5_input = {A_OUT,E6END2,EE4END10,EE4END2,E2END2};
cus_mux81 inst_cus_mux81_W2BEGb5 (
    .A0(W2BEGb5_input[0]),
    .A1(W2BEGb5_input[1]),
    .A2(W2BEGb5_input[2]),
    .A3(W2BEGb5_input[3]),
    .A4(W2BEGb5_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[43+0]),
    .S0N(ConfigBits_N[43+0]),
    .S1(ConfigBits[43+1]),
    .S1N(ConfigBits_N[43+1]),
    .S2(ConfigBits[43+2]),
    .S2N(ConfigBits_N[43+2]),
    .X(W2BEGb5)
);

 //switch matrix multiplexer W2BEGb6 MUX-5
assign W2BEGb6_input = {A_OUT,E6END1,EE4END9,EE4END1,E2END1};
cus_mux81 inst_cus_mux81_W2BEGb6 (
    .A0(W2BEGb6_input[0]),
    .A1(W2BEGb6_input[1]),
    .A2(W2BEGb6_input[2]),
    .A3(W2BEGb6_input[3]),
    .A4(W2BEGb6_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[46+0]),
    .S0N(ConfigBits_N[46+0]),
    .S1(ConfigBits[46+1]),
    .S1N(ConfigBits_N[46+1]),
    .S2(ConfigBits[46+2]),
    .S2N(ConfigBits_N[46+2]),
    .X(W2BEGb6)
);

 //switch matrix multiplexer W2BEGb7 MUX-5
assign W2BEGb7_input = {A_OUT,E6END0,EE4END8,EE4END0,E2END0};
cus_mux81 inst_cus_mux81_W2BEGb7 (
    .A0(W2BEGb7_input[0]),
    .A1(W2BEGb7_input[1]),
    .A2(W2BEGb7_input[2]),
    .A3(W2BEGb7_input[3]),
    .A4(W2BEGb7_input[4]),
    .A5(GND0),
    .A6(GND0),
    .A7(GND0),
    .S0(ConfigBits[49+0]),
    .S0N(ConfigBits_N[49+0]),
    .S1(ConfigBits[49+1]),
    .S1N(ConfigBits_N[49+1]),
    .S2(ConfigBits[49+2]),
    .S2N(ConfigBits_N[49+2]),
    .X(W2BEGb7)
);

 //switch matrix multiplexer WW4BEG0 MUX-4
assign WW4BEG0_input = {A_OUT,E6END4,E6END2,E6END0};
cus_mux41 inst_cus_mux41_WW4BEG0 (
    .A0(WW4BEG0_input[0]),
    .A1(WW4BEG0_input[1]),
    .A2(WW4BEG0_input[2]),
    .A3(WW4BEG0_input[3]),
    .S0(ConfigBits[52+0]),
    .S0N(ConfigBits_N[52+0]),
    .S1(ConfigBits[52+1]),
    .S1N(ConfigBits_N[52+1]),
    .X(WW4BEG0)
);

 //switch matrix multiplexer WW4BEG1 MUX-4
assign WW4BEG1_input = {A_OUT,E6END10,E6END8,E6END6};
cus_mux41 inst_cus_mux41_WW4BEG1 (
    .A0(WW4BEG1_input[0]),
    .A1(WW4BEG1_input[1]),
    .A2(WW4BEG1_input[2]),
    .A3(WW4BEG1_input[3]),
    .S0(ConfigBits[54+0]),
    .S0N(ConfigBits_N[54+0]),
    .S1(ConfigBits[54+1]),
    .S1N(ConfigBits_N[54+1]),
    .X(WW4BEG1)
);

 //switch matrix multiplexer WW4BEG2 MUX-4
assign WW4BEG2_input = {A_OUT,E6END5,E6END3,E6END1};
cus_mux41 inst_cus_mux41_WW4BEG2 (
    .A0(WW4BEG2_input[0]),
    .A1(WW4BEG2_input[1]),
    .A2(WW4BEG2_input[2]),
    .A3(WW4BEG2_input[3]),
    .S0(ConfigBits[56+0]),
    .S0N(ConfigBits_N[56+0]),
    .S1(ConfigBits[56+1]),
    .S1N(ConfigBits_N[56+1]),
    .X(WW4BEG2)
);

 //switch matrix multiplexer WW4BEG3 MUX-4
assign WW4BEG3_input = {A_OUT,E6END11,E6END9,E6END7};
cus_mux41 inst_cus_mux41_WW4BEG3 (
    .A0(WW4BEG3_input[0]),
    .A1(WW4BEG3_input[1]),
    .A2(WW4BEG3_input[2]),
    .A3(WW4BEG3_input[3]),
    .S0(ConfigBits[58+0]),
    .S0N(ConfigBits_N[58+0]),
    .S1(ConfigBits[58+1]),
    .S1N(ConfigBits_N[58+1]),
    .X(WW4BEG3)
);

 //switch matrix multiplexer WW4BEG4 MUX-4
assign WW4BEG4_input = {E2END6,E2END4,E2END2,E2END0};
cus_mux41 inst_cus_mux41_WW4BEG4 (
    .A0(WW4BEG4_input[0]),
    .A1(WW4BEG4_input[1]),
    .A2(WW4BEG4_input[2]),
    .A3(WW4BEG4_input[3]),
    .S0(ConfigBits[60+0]),
    .S0N(ConfigBits_N[60+0]),
    .S1(ConfigBits[60+1]),
    .S1N(ConfigBits_N[60+1]),
    .X(WW4BEG4)
);

 //switch matrix multiplexer WW4BEG5 MUX-4
assign WW4BEG5_input = {E2END7,E2END5,E2END3,E2END1};
cus_mux41 inst_cus_mux41_WW4BEG5 (
    .A0(WW4BEG5_input[0]),
    .A1(WW4BEG5_input[1]),
    .A2(WW4BEG5_input[2]),
    .A3(WW4BEG5_input[3]),
    .S0(ConfigBits[62+0]),
    .S0N(ConfigBits_N[62+0]),
    .S1(ConfigBits[62+1]),
    .S1N(ConfigBits_N[62+1]),
    .X(WW4BEG5)
);

 //switch matrix multiplexer WW4BEG6 MUX-4
assign WW4BEG6_input = {E2MID6,E2MID4,E2MID2,E2MID0};
cus_mux41 inst_cus_mux41_WW4BEG6 (
    .A0(WW4BEG6_input[0]),
    .A1(WW4BEG6_input[1]),
    .A2(WW4BEG6_input[2]),
    .A3(WW4BEG6_input[3]),
    .S0(ConfigBits[64+0]),
    .S0N(ConfigBits_N[64+0]),
    .S1(ConfigBits[64+1]),
    .S1N(ConfigBits_N[64+1]),
    .X(WW4BEG6)
);

 //switch matrix multiplexer WW4BEG7 MUX-4
assign WW4BEG7_input = {E2MID7,E2MID5,E2MID3,E2MID1};
cus_mux41 inst_cus_mux41_WW4BEG7 (
    .A0(WW4BEG7_input[0]),
    .A1(WW4BEG7_input[1]),
    .A2(WW4BEG7_input[2]),
    .A3(WW4BEG7_input[3]),
    .S0(ConfigBits[66+0]),
    .S0N(ConfigBits_N[66+0]),
    .S1(ConfigBits[66+1]),
    .S1N(ConfigBits_N[66+1]),
    .X(WW4BEG7)
);

 //switch matrix multiplexer WW4BEG8 MUX-4
assign WW4BEG8_input = {E6END10,E6END8,E6END6,E6END4};
cus_mux41 inst_cus_mux41_WW4BEG8 (
    .A0(WW4BEG8_input[0]),
    .A1(WW4BEG8_input[1]),
    .A2(WW4BEG8_input[2]),
    .A3(WW4BEG8_input[3]),
    .S0(ConfigBits[68+0]),
    .S0N(ConfigBits_N[68+0]),
    .S1(ConfigBits[68+1]),
    .S1N(ConfigBits_N[68+1]),
    .X(WW4BEG8)
);

 //switch matrix multiplexer WW4BEG9 MUX-4
assign WW4BEG9_input = {E6END7,E6END5,E6END3,E6END1};
cus_mux41 inst_cus_mux41_WW4BEG9 (
    .A0(WW4BEG9_input[0]),
    .A1(WW4BEG9_input[1]),
    .A2(WW4BEG9_input[2]),
    .A3(WW4BEG9_input[3]),
    .S0(ConfigBits[70+0]),
    .S0N(ConfigBits_N[70+0]),
    .S1(ConfigBits[70+1]),
    .S1N(ConfigBits_N[70+1]),
    .X(WW4BEG9)
);

 //switch matrix multiplexer WW4BEG10 MUX-4
assign WW4BEG10_input = {A_OUT,E6END4,E6END2,E6END0};
cus_mux41 inst_cus_mux41_WW4BEG10 (
    .A0(WW4BEG10_input[0]),
    .A1(WW4BEG10_input[1]),
    .A2(WW4BEG10_input[2]),
    .A3(WW4BEG10_input[3]),
    .S0(ConfigBits[72+0]),
    .S0N(ConfigBits_N[72+0]),
    .S1(ConfigBits[72+1]),
    .S1N(ConfigBits_N[72+1]),
    .X(WW4BEG10)
);

 //switch matrix multiplexer WW4BEG11 MUX-4
assign WW4BEG11_input = {A_OUT,E6END10,E6END8,E6END6};
cus_mux41 inst_cus_mux41_WW4BEG11 (
    .A0(WW4BEG11_input[0]),
    .A1(WW4BEG11_input[1]),
    .A2(WW4BEG11_input[2]),
    .A3(WW4BEG11_input[3]),
    .S0(ConfigBits[74+0]),
    .S0N(ConfigBits_N[74+0]),
    .S1(ConfigBits[74+1]),
    .S1N(ConfigBits_N[74+1]),
    .X(WW4BEG11)
);

 //switch matrix multiplexer WW4BEG12 MUX-4
assign WW4BEG12_input = {A_OUT,E6END5,E6END3,E6END1};
cus_mux41 inst_cus_mux41_WW4BEG12 (
    .A0(WW4BEG12_input[0]),
    .A1(WW4BEG12_input[1]),
    .A2(WW4BEG12_input[2]),
    .A3(WW4BEG12_input[3]),
    .S0(ConfigBits[76+0]),
    .S0N(ConfigBits_N[76+0]),
    .S1(ConfigBits[76+1]),
    .S1N(ConfigBits_N[76+1]),
    .X(WW4BEG12)
);

 //switch matrix multiplexer WW4BEG13 MUX-4
assign WW4BEG13_input = {A_OUT,E6END11,E6END9,E6END7};
cus_mux41 inst_cus_mux41_WW4BEG13 (
    .A0(WW4BEG13_input[0]),
    .A1(WW4BEG13_input[1]),
    .A2(WW4BEG13_input[2]),
    .A3(WW4BEG13_input[3]),
    .S0(ConfigBits[78+0]),
    .S0N(ConfigBits_N[78+0]),
    .S1(ConfigBits[78+1]),
    .S1N(ConfigBits_N[78+1]),
    .X(WW4BEG13)
);

 //switch matrix multiplexer WW4BEG14 MUX-4
assign WW4BEG14_input = {E2MID6,E2MID4,E2MID2,E2MID0};
cus_mux41 inst_cus_mux41_WW4BEG14 (
    .A0(WW4BEG14_input[0]),
    .A1(WW4BEG14_input[1]),
    .A2(WW4BEG14_input[2]),
    .A3(WW4BEG14_input[3]),
    .S0(ConfigBits[80+0]),
    .S0N(ConfigBits_N[80+0]),
    .S1(ConfigBits[80+1]),
    .S1N(ConfigBits_N[80+1]),
    .X(WW4BEG14)
);

 //switch matrix multiplexer WW4BEG15 MUX-4
assign WW4BEG15_input = {E2MID7,E2MID5,E2MID3,E2MID1};
cus_mux41 inst_cus_mux41_WW4BEG15 (
    .A0(WW4BEG15_input[0]),
    .A1(WW4BEG15_input[1]),
    .A2(WW4BEG15_input[2]),
    .A3(WW4BEG15_input[3]),
    .S0(ConfigBits[82+0]),
    .S0N(ConfigBits_N[82+0]),
    .S1(ConfigBits[82+1]),
    .S1N(ConfigBits_N[82+1]),
    .X(WW4BEG15)
);

 //switch matrix multiplexer W6BEG0 MUX-4
assign W6BEG0_input = {A_OUT,E6END11,EE4END11,E1END2};
cus_mux41 inst_cus_mux41_W6BEG0 (
    .A0(W6BEG0_input[0]),
    .A1(W6BEG0_input[1]),
    .A2(W6BEG0_input[2]),
    .A3(W6BEG0_input[3]),
    .S0(ConfigBits[84+0]),
    .S0N(ConfigBits_N[84+0]),
    .S1(ConfigBits[84+1]),
    .S1N(ConfigBits_N[84+1]),
    .X(W6BEG0)
);

 //switch matrix multiplexer W6BEG1 MUX-4
assign W6BEG1_input = {A_OUT,E6END10,EE4END10,E1END3};
cus_mux41 inst_cus_mux41_W6BEG1 (
    .A0(W6BEG1_input[0]),
    .A1(W6BEG1_input[1]),
    .A2(W6BEG1_input[2]),
    .A3(W6BEG1_input[3]),
    .S0(ConfigBits[86+0]),
    .S0N(ConfigBits_N[86+0]),
    .S1(ConfigBits[86+1]),
    .S1N(ConfigBits_N[86+1]),
    .X(W6BEG1)
);

 //switch matrix multiplexer W6BEG2 MUX-4
assign W6BEG2_input = {A_OUT,E6END7,EE4END15,EE4END7};
cus_mux41 inst_cus_mux41_W6BEG2 (
    .A0(W6BEG2_input[0]),
    .A1(W6BEG2_input[1]),
    .A2(W6BEG2_input[2]),
    .A3(W6BEG2_input[3]),
    .S0(ConfigBits[88+0]),
    .S0N(ConfigBits_N[88+0]),
    .S1(ConfigBits[88+1]),
    .S1N(ConfigBits_N[88+1]),
    .X(W6BEG2)
);

 //switch matrix multiplexer W6BEG3 MUX-4
assign W6BEG3_input = {A_OUT,E6END6,EE4END14,EE4END6};
cus_mux41 inst_cus_mux41_W6BEG3 (
    .A0(W6BEG3_input[0]),
    .A1(W6BEG3_input[1]),
    .A2(W6BEG3_input[2]),
    .A3(W6BEG3_input[3]),
    .S0(ConfigBits[90+0]),
    .S0N(ConfigBits_N[90+0]),
    .S1(ConfigBits[90+1]),
    .S1N(ConfigBits_N[90+1]),
    .X(W6BEG3)
);

 //switch matrix multiplexer W6BEG4 MUX-4
assign W6BEG4_input = {A_OUT,E6END3,EE4END3,E1END2};
cus_mux41 inst_cus_mux41_W6BEG4 (
    .A0(W6BEG4_input[0]),
    .A1(W6BEG4_input[1]),
    .A2(W6BEG4_input[2]),
    .A3(W6BEG4_input[3]),
    .S0(ConfigBits[92+0]),
    .S0N(ConfigBits_N[92+0]),
    .S1(ConfigBits[92+1]),
    .S1N(ConfigBits_N[92+1]),
    .X(W6BEG4)
);

 //switch matrix multiplexer W6BEG5 MUX-4
assign W6BEG5_input = {A_OUT,E6END2,EE4END2,E1END3};
cus_mux41 inst_cus_mux41_W6BEG5 (
    .A0(W6BEG5_input[0]),
    .A1(W6BEG5_input[1]),
    .A2(W6BEG5_input[2]),
    .A3(W6BEG5_input[3]),
    .S0(ConfigBits[94+0]),
    .S0N(ConfigBits_N[94+0]),
    .S1(ConfigBits[94+1]),
    .S1N(ConfigBits_N[94+1]),
    .X(W6BEG5)
);

 //switch matrix multiplexer W6BEG6 MUX-4
assign W6BEG6_input = {A_OUT,E6END9,EE4END9,E1END1};
cus_mux41 inst_cus_mux41_W6BEG6 (
    .A0(W6BEG6_input[0]),
    .A1(W6BEG6_input[1]),
    .A2(W6BEG6_input[2]),
    .A3(W6BEG6_input[3]),
    .S0(ConfigBits[96+0]),
    .S0N(ConfigBits_N[96+0]),
    .S1(ConfigBits[96+1]),
    .S1N(ConfigBits_N[96+1]),
    .X(W6BEG6)
);

 //switch matrix multiplexer W6BEG7 MUX-4
assign W6BEG7_input = {A_OUT,E6END8,EE4END8,E1END0};
cus_mux41 inst_cus_mux41_W6BEG7 (
    .A0(W6BEG7_input[0]),
    .A1(W6BEG7_input[1]),
    .A2(W6BEG7_input[2]),
    .A3(W6BEG7_input[3]),
    .S0(ConfigBits[98+0]),
    .S0N(ConfigBits_N[98+0]),
    .S1(ConfigBits[98+1]),
    .S1N(ConfigBits_N[98+1]),
    .X(W6BEG7)
);

 //switch matrix multiplexer W6BEG8 MUX-4
assign W6BEG8_input = {A_OUT,E6END5,EE4END13,EE4END5};
cus_mux41 inst_cus_mux41_W6BEG8 (
    .A0(W6BEG8_input[0]),
    .A1(W6BEG8_input[1]),
    .A2(W6BEG8_input[2]),
    .A3(W6BEG8_input[3]),
    .S0(ConfigBits[100+0]),
    .S0N(ConfigBits_N[100+0]),
    .S1(ConfigBits[100+1]),
    .S1N(ConfigBits_N[100+1]),
    .X(W6BEG8)
);

 //switch matrix multiplexer W6BEG9 MUX-4
assign W6BEG9_input = {A_OUT,E6END4,EE4END12,EE4END4};
cus_mux41 inst_cus_mux41_W6BEG9 (
    .A0(W6BEG9_input[0]),
    .A1(W6BEG9_input[1]),
    .A2(W6BEG9_input[2]),
    .A3(W6BEG9_input[3]),
    .S0(ConfigBits[102+0]),
    .S0N(ConfigBits_N[102+0]),
    .S1(ConfigBits[102+1]),
    .S1N(ConfigBits_N[102+1]),
    .X(W6BEG9)
);

 //switch matrix multiplexer W6BEG10 MUX-4
assign W6BEG10_input = {A_OUT,E6END1,EE4END1,E1END1};
cus_mux41 inst_cus_mux41_W6BEG10 (
    .A0(W6BEG10_input[0]),
    .A1(W6BEG10_input[1]),
    .A2(W6BEG10_input[2]),
    .A3(W6BEG10_input[3]),
    .S0(ConfigBits[104+0]),
    .S0N(ConfigBits_N[104+0]),
    .S1(ConfigBits[104+1]),
    .S1N(ConfigBits_N[104+1]),
    .X(W6BEG10)
);

 //switch matrix multiplexer W6BEG11 MUX-4
assign W6BEG11_input = {A_OUT,E6END0,EE4END0,E1END0};
cus_mux41 inst_cus_mux41_W6BEG11 (
    .A0(W6BEG11_input[0]),
    .A1(W6BEG11_input[1]),
    .A2(W6BEG11_input[2]),
    .A3(W6BEG11_input[3]),
    .S0(ConfigBits[106+0]),
    .S0N(ConfigBits_N[106+0]),
    .S1(ConfigBits[106+1]),
    .S1N(ConfigBits_N[106+1]),
    .X(W6BEG11)
);

 //switch matrix multiplexer A_CLK MUX-4
assign A_CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_A_CLK (
    .A0(A_CLK_input[0]),
    .A1(A_CLK_input[1]),
    .A2(A_CLK_input[2]),
    .A3(A_CLK_input[3]),
    .S0(ConfigBits[108+0]),
    .S0N(ConfigBits_N[108+0]),
    .S1(ConfigBits[108+1]),
    .S1N(ConfigBits_N[108+1]),
    .X(A_CLK)
);

 //switch matrix multiplexer A_IN MUX-16
assign A_IN_input = {E2END7,E2END6,E2END5,E2END4,E2END3,E2END2,E2END1,E2END0,E2MID7,E2MID6,E2MID5,E2MID4,E2MID3,E2MID2,E2MID1,E2MID0};
cus_mux161 inst_cus_mux161_A_IN (
    .A0(A_IN_input[0]),
    .A1(A_IN_input[1]),
    .A2(A_IN_input[2]),
    .A3(A_IN_input[3]),
    .A4(A_IN_input[4]),
    .A5(A_IN_input[5]),
    .A6(A_IN_input[6]),
    .A7(A_IN_input[7]),
    .A8(A_IN_input[8]),
    .A9(A_IN_input[9]),
    .A10(A_IN_input[10]),
    .A11(A_IN_input[11]),
    .A12(A_IN_input[12]),
    .A13(A_IN_input[13]),
    .A14(A_IN_input[14]),
    .A15(A_IN_input[15]),
    .S0(ConfigBits[110+0]),
    .S0N(ConfigBits_N[110+0]),
    .S1(ConfigBits[110+1]),
    .S1N(ConfigBits_N[110+1]),
    .S2(ConfigBits[110+2]),
    .S2N(ConfigBits_N[110+2]),
    .S3(ConfigBits[110+3]),
    .S3N(ConfigBits_N[110+3]),
    .X(A_IN)
);

 //switch matrix multiplexer A_EN MUX-8
assign A_EN_input = {VCC0,GND0,E2END4,E2END3,E2END2,E2END1,E2END0,E2MID7};
cus_mux81 inst_cus_mux81_A_EN (
    .A0(A_EN_input[0]),
    .A1(A_EN_input[1]),
    .A2(A_EN_input[2]),
    .A3(A_EN_input[3]),
    .A4(A_EN_input[4]),
    .A5(A_EN_input[5]),
    .A6(A_EN_input[6]),
    .A7(A_EN_input[7]),
    .S0(ConfigBits[114+0]),
    .S0N(ConfigBits_N[114+0]),
    .S1(ConfigBits[114+1]),
    .S1N(ConfigBits_N[114+1]),
    .S2(ConfigBits[114+2]),
    .S2N(ConfigBits_N[114+2]),
    .X(A_EN)
);

endmodule