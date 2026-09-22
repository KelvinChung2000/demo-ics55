 // NumberOfConfigBits: 172
module E_BRAM_bot_switch_matrix
    #(
        parameter NoConfigBits=172
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
        input  top2bot_DIN0,
        input  top2bot_DIN1,
        input  top2bot_DIN2,
        input  top2bot_DIN3,
        input  top2bot_DIN4,
        input  top2bot_DIN5,
        input  top2bot_DIN6,
        input  top2bot_DIN7,
        input  top2bot_DIN8,
        input  top2bot_DIN9,
        input  top2bot_DIN10,
        input  top2bot_DIN11,
        input  top2bot_DIN12,
        input  top2bot_DIN13,
        input  top2bot_DIN14,
        input  top2bot_DIN15,
        input  top2bot_BM0,
        input  top2bot_BM1,
        input  top2bot_BM2,
        input  top2bot_BM3,
        input  top2bot_BM4,
        input  top2bot_BM5,
        input  top2bot_BM6,
        input  top2bot_BM7,
        input  top2bot_BM8,
        input  top2bot_BM9,
        input  top2bot_BM10,
        input  top2bot_BM11,
        input  top2bot_BM12,
        input  top2bot_BM13,
        input  top2bot_BM14,
        input  top2bot_BM15,
        input  top2bot_ADDR0,
        input  top2bot_ADDR1,
        input  top2bot_ADDR2,
        input  top2bot_ADDR3,
        input  top2bot_ADDR4,
        input  DOUT0,
        input  DOUT1,
        input  DOUT2,
        input  DOUT3,
        input  DOUT4,
        input  DOUT5,
        input  DOUT6,
        input  DOUT7,
        input  DOUT8,
        input  DOUT9,
        input  DOUT10,
        input  DOUT11,
        input  DOUT12,
        input  DOUT13,
        input  DOUT14,
        input  DOUT15,
        input  DOUT16,
        input  DOUT17,
        input  DOUT18,
        input  DOUT19,
        input  DOUT20,
        input  DOUT21,
        input  DOUT22,
        input  DOUT23,
        input  DOUT24,
        input  DOUT25,
        input  DOUT26,
        input  DOUT27,
        input  DOUT28,
        input  DOUT29,
        input  DOUT30,
        input  DOUT31,
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
        output  bot2top_DOUT0,
        output  bot2top_DOUT1,
        output  bot2top_DOUT2,
        output  bot2top_DOUT3,
        output  bot2top_DOUT4,
        output  bot2top_DOUT5,
        output  bot2top_DOUT6,
        output  bot2top_DOUT7,
        output  bot2top_DOUT8,
        output  bot2top_DOUT9,
        output  bot2top_DOUT10,
        output  bot2top_DOUT11,
        output  bot2top_DOUT12,
        output  bot2top_DOUT13,
        output  bot2top_DOUT14,
        output  bot2top_DOUT15,
        output  CLK,
        output  ADDR0,
        output  ADDR1,
        output  ADDR2,
        output  ADDR3,
        output  ADDR4,
        output  ADDR5,
        output  ADDR6,
        output  ADDR7,
        output  ADDR8,
        output  ADDR9,
        output  DIN0,
        output  DIN1,
        output  DIN2,
        output  DIN3,
        output  DIN4,
        output  DIN5,
        output  DIN6,
        output  DIN7,
        output  DIN8,
        output  DIN9,
        output  DIN10,
        output  DIN11,
        output  DIN12,
        output  DIN13,
        output  DIN14,
        output  DIN15,
        output  DIN16,
        output  DIN17,
        output  DIN18,
        output  DIN19,
        output  DIN20,
        output  DIN21,
        output  DIN22,
        output  DIN23,
        output  DIN24,
        output  DIN25,
        output  DIN26,
        output  DIN27,
        output  DIN28,
        output  DIN29,
        output  DIN30,
        output  DIN31,
        output  BM0,
        output  BM1,
        output  BM2,
        output  BM3,
        output  BM4,
        output  BM5,
        output  BM6,
        output  BM7,
        output  BM8,
        output  BM9,
        output  BM10,
        output  BM11,
        output  BM12,
        output  BM13,
        output  BM14,
        output  BM15,
        output  BM16,
        output  BM17,
        output  BM18,
        output  BM19,
        output  BM20,
        output  BM21,
        output  BM22,
        output  BM23,
        output  BM24,
        output  BM25,
        output  BM26,
        output  BM27,
        output  BM28,
        output  BM29,
        output  BM30,
        output  BM31,
        output  WEN,
        output  MEN,
        output  REN,
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

wire[4-1:0] W1BEG0_input;
wire[4-1:0] W1BEG1_input;
wire[4-1:0] W1BEG2_input;
wire[4-1:0] W1BEG3_input;
wire[4-1:0] W2BEG0_input;
wire[4-1:0] W2BEG1_input;
wire[4-1:0] W2BEG2_input;
wire[4-1:0] W2BEG3_input;
wire[4-1:0] W2BEG4_input;
wire[4-1:0] W2BEG5_input;
wire[4-1:0] W2BEG6_input;
wire[4-1:0] W2BEG7_input;
wire[4-1:0] W2BEGb0_input;
wire[4-1:0] W2BEGb1_input;
wire[4-1:0] W2BEGb2_input;
wire[4-1:0] W2BEGb3_input;
wire[4-1:0] W2BEGb4_input;
wire[4-1:0] W2BEGb5_input;
wire[4-1:0] W2BEGb6_input;
wire[4-1:0] W2BEGb7_input;
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
wire[2-1:0] W6BEG0_input;
wire[2-1:0] W6BEG1_input;
wire[2-1:0] W6BEG2_input;
wire[2-1:0] W6BEG3_input;
wire[2-1:0] W6BEG4_input;
wire[2-1:0] W6BEG5_input;
wire[2-1:0] W6BEG6_input;
wire[2-1:0] W6BEG7_input;
wire[2-1:0] W6BEG8_input;
wire[2-1:0] W6BEG9_input;
wire[2-1:0] W6BEG10_input;
wire[2-1:0] W6BEG11_input;
wire[4-1:0] CLK_input;
wire[4-1:0] ADDR0_input;
wire[4-1:0] ADDR1_input;
wire[4-1:0] ADDR2_input;
wire[4-1:0] ADDR3_input;
wire[4-1:0] ADDR4_input;
wire[4-1:0] DIN0_input;
wire[4-1:0] DIN1_input;
wire[4-1:0] DIN2_input;
wire[4-1:0] DIN3_input;
wire[4-1:0] DIN4_input;
wire[4-1:0] DIN5_input;
wire[4-1:0] DIN6_input;
wire[4-1:0] DIN7_input;
wire[4-1:0] DIN8_input;
wire[4-1:0] DIN9_input;
wire[4-1:0] DIN10_input;
wire[4-1:0] DIN11_input;
wire[4-1:0] DIN12_input;
wire[4-1:0] DIN13_input;
wire[4-1:0] DIN14_input;
wire[4-1:0] DIN15_input;
wire[4-1:0] BM0_input;
wire[4-1:0] BM1_input;
wire[4-1:0] BM2_input;
wire[4-1:0] BM3_input;
wire[4-1:0] BM4_input;
wire[4-1:0] BM5_input;
wire[4-1:0] BM6_input;
wire[4-1:0] BM7_input;
wire[4-1:0] BM8_input;
wire[4-1:0] BM9_input;
wire[4-1:0] BM10_input;
wire[4-1:0] BM11_input;
wire[4-1:0] BM12_input;
wire[4-1:0] BM13_input;
wire[4-1:0] BM14_input;
wire[4-1:0] BM15_input;
wire[15-1:0] WEN_input;
wire[15-1:0] MEN_input;
wire[15-1:0] REN_input;
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

 //switch matrix multiplexer W1BEG0 MUX-4
assign W1BEG0_input = {DOUT7,DOUT2,E2END0,E1END3};
cus_mux41 inst_cus_mux41_W1BEG0 (
    .A0(W1BEG0_input[0]),
    .A1(W1BEG0_input[1]),
    .A2(W1BEG0_input[2]),
    .A3(W1BEG0_input[3]),
    .S0(ConfigBits[0+0]),
    .S0N(ConfigBits_N[0+0]),
    .S1(ConfigBits[0+1]),
    .S1N(ConfigBits_N[0+1]),
    .X(W1BEG0)
);

 //switch matrix multiplexer W1BEG1 MUX-4
assign W1BEG1_input = {DOUT6,DOUT3,E2END1,E1END2};
cus_mux41 inst_cus_mux41_W1BEG1 (
    .A0(W1BEG1_input[0]),
    .A1(W1BEG1_input[1]),
    .A2(W1BEG1_input[2]),
    .A3(W1BEG1_input[3]),
    .S0(ConfigBits[2+0]),
    .S0N(ConfigBits_N[2+0]),
    .S1(ConfigBits[2+1]),
    .S1N(ConfigBits_N[2+1]),
    .X(W1BEG1)
);

 //switch matrix multiplexer W1BEG2 MUX-4
assign W1BEG2_input = {DOUT5,DOUT0,E2END2,E1END1};
cus_mux41 inst_cus_mux41_W1BEG2 (
    .A0(W1BEG2_input[0]),
    .A1(W1BEG2_input[1]),
    .A2(W1BEG2_input[2]),
    .A3(W1BEG2_input[3]),
    .S0(ConfigBits[4+0]),
    .S0N(ConfigBits_N[4+0]),
    .S1(ConfigBits[4+1]),
    .S1N(ConfigBits_N[4+1]),
    .X(W1BEG2)
);

 //switch matrix multiplexer W1BEG3 MUX-4
assign W1BEG3_input = {DOUT4,DOUT1,E2END3,E1END0};
cus_mux41 inst_cus_mux41_W1BEG3 (
    .A0(W1BEG3_input[0]),
    .A1(W1BEG3_input[1]),
    .A2(W1BEG3_input[2]),
    .A3(W1BEG3_input[3]),
    .S0(ConfigBits[6+0]),
    .S0N(ConfigBits_N[6+0]),
    .S1(ConfigBits[6+1]),
    .S1N(ConfigBits_N[6+1]),
    .X(W1BEG3)
);

 //switch matrix multiplexer W2BEG0 MUX-4
assign W2BEG0_input = {DOUT8,DOUT0,E6END3,EE4END0};
cus_mux41 inst_cus_mux41_W2BEG0 (
    .A0(W2BEG0_input[0]),
    .A1(W2BEG0_input[1]),
    .A2(W2BEG0_input[2]),
    .A3(W2BEG0_input[3]),
    .S0(ConfigBits[8+0]),
    .S0N(ConfigBits_N[8+0]),
    .S1(ConfigBits[8+1]),
    .S1N(ConfigBits_N[8+1]),
    .X(W2BEG0)
);

 //switch matrix multiplexer W2BEG1 MUX-4
assign W2BEG1_input = {DOUT9,DOUT1,E6END2,EE4END1};
cus_mux41 inst_cus_mux41_W2BEG1 (
    .A0(W2BEG1_input[0]),
    .A1(W2BEG1_input[1]),
    .A2(W2BEG1_input[2]),
    .A3(W2BEG1_input[3]),
    .S0(ConfigBits[10+0]),
    .S0N(ConfigBits_N[10+0]),
    .S1(ConfigBits[10+1]),
    .S1N(ConfigBits_N[10+1]),
    .X(W2BEG1)
);

 //switch matrix multiplexer W2BEG2 MUX-4
assign W2BEG2_input = {DOUT10,DOUT2,E6END1,EE4END2};
cus_mux41 inst_cus_mux41_W2BEG2 (
    .A0(W2BEG2_input[0]),
    .A1(W2BEG2_input[1]),
    .A2(W2BEG2_input[2]),
    .A3(W2BEG2_input[3]),
    .S0(ConfigBits[12+0]),
    .S0N(ConfigBits_N[12+0]),
    .S1(ConfigBits[12+1]),
    .S1N(ConfigBits_N[12+1]),
    .X(W2BEG2)
);

 //switch matrix multiplexer W2BEG3 MUX-4
assign W2BEG3_input = {DOUT11,DOUT3,E6END0,EE4END3};
cus_mux41 inst_cus_mux41_W2BEG3 (
    .A0(W2BEG3_input[0]),
    .A1(W2BEG3_input[1]),
    .A2(W2BEG3_input[2]),
    .A3(W2BEG3_input[3]),
    .S0(ConfigBits[14+0]),
    .S0N(ConfigBits_N[14+0]),
    .S1(ConfigBits[14+1]),
    .S1N(ConfigBits_N[14+1]),
    .X(W2BEG3)
);

 //switch matrix multiplexer W2BEG4 MUX-4
assign W2BEG4_input = {DOUT12,DOUT4,EE4END4,E2END7};
cus_mux41 inst_cus_mux41_W2BEG4 (
    .A0(W2BEG4_input[0]),
    .A1(W2BEG4_input[1]),
    .A2(W2BEG4_input[2]),
    .A3(W2BEG4_input[3]),
    .S0(ConfigBits[16+0]),
    .S0N(ConfigBits_N[16+0]),
    .S1(ConfigBits[16+1]),
    .S1N(ConfigBits_N[16+1]),
    .X(W2BEG4)
);

 //switch matrix multiplexer W2BEG5 MUX-4
assign W2BEG5_input = {DOUT13,DOUT5,EE4END5,E2END6};
cus_mux41 inst_cus_mux41_W2BEG5 (
    .A0(W2BEG5_input[0]),
    .A1(W2BEG5_input[1]),
    .A2(W2BEG5_input[2]),
    .A3(W2BEG5_input[3]),
    .S0(ConfigBits[18+0]),
    .S0N(ConfigBits_N[18+0]),
    .S1(ConfigBits[18+1]),
    .S1N(ConfigBits_N[18+1]),
    .X(W2BEG5)
);

 //switch matrix multiplexer W2BEG6 MUX-4
assign W2BEG6_input = {DOUT14,DOUT6,EE4END6,E2END5};
cus_mux41 inst_cus_mux41_W2BEG6 (
    .A0(W2BEG6_input[0]),
    .A1(W2BEG6_input[1]),
    .A2(W2BEG6_input[2]),
    .A3(W2BEG6_input[3]),
    .S0(ConfigBits[20+0]),
    .S0N(ConfigBits_N[20+0]),
    .S1(ConfigBits[20+1]),
    .S1N(ConfigBits_N[20+1]),
    .X(W2BEG6)
);

 //switch matrix multiplexer W2BEG7 MUX-4
assign W2BEG7_input = {DOUT15,DOUT7,EE4END7,E2END4};
cus_mux41 inst_cus_mux41_W2BEG7 (
    .A0(W2BEG7_input[0]),
    .A1(W2BEG7_input[1]),
    .A2(W2BEG7_input[2]),
    .A3(W2BEG7_input[3]),
    .S0(ConfigBits[22+0]),
    .S0N(ConfigBits_N[22+0]),
    .S1(ConfigBits[22+1]),
    .S1N(ConfigBits_N[22+1]),
    .X(W2BEG7)
);

 //switch matrix multiplexer W2BEGb0 MUX-4
assign W2BEGb0_input = {DOUT8,DOUT0,EE4END8,E2END3};
cus_mux41 inst_cus_mux41_W2BEGb0 (
    .A0(W2BEGb0_input[0]),
    .A1(W2BEGb0_input[1]),
    .A2(W2BEGb0_input[2]),
    .A3(W2BEGb0_input[3]),
    .S0(ConfigBits[24+0]),
    .S0N(ConfigBits_N[24+0]),
    .S1(ConfigBits[24+1]),
    .S1N(ConfigBits_N[24+1]),
    .X(W2BEGb0)
);

 //switch matrix multiplexer W2BEGb1 MUX-4
assign W2BEGb1_input = {DOUT9,DOUT1,EE4END9,E2END2};
cus_mux41 inst_cus_mux41_W2BEGb1 (
    .A0(W2BEGb1_input[0]),
    .A1(W2BEGb1_input[1]),
    .A2(W2BEGb1_input[2]),
    .A3(W2BEGb1_input[3]),
    .S0(ConfigBits[26+0]),
    .S0N(ConfigBits_N[26+0]),
    .S1(ConfigBits[26+1]),
    .S1N(ConfigBits_N[26+1]),
    .X(W2BEGb1)
);

 //switch matrix multiplexer W2BEGb2 MUX-4
assign W2BEGb2_input = {DOUT10,DOUT2,EE4END10,E2END1};
cus_mux41 inst_cus_mux41_W2BEGb2 (
    .A0(W2BEGb2_input[0]),
    .A1(W2BEGb2_input[1]),
    .A2(W2BEGb2_input[2]),
    .A3(W2BEGb2_input[3]),
    .S0(ConfigBits[28+0]),
    .S0N(ConfigBits_N[28+0]),
    .S1(ConfigBits[28+1]),
    .S1N(ConfigBits_N[28+1]),
    .X(W2BEGb2)
);

 //switch matrix multiplexer W2BEGb3 MUX-4
assign W2BEGb3_input = {DOUT11,DOUT3,EE4END11,E2END0};
cus_mux41 inst_cus_mux41_W2BEGb3 (
    .A0(W2BEGb3_input[0]),
    .A1(W2BEGb3_input[1]),
    .A2(W2BEGb3_input[2]),
    .A3(W2BEGb3_input[3]),
    .S0(ConfigBits[30+0]),
    .S0N(ConfigBits_N[30+0]),
    .S1(ConfigBits[30+1]),
    .S1N(ConfigBits_N[30+1]),
    .X(W2BEGb3)
);

 //switch matrix multiplexer W2BEGb4 MUX-4
assign W2BEGb4_input = {DOUT12,DOUT4,E6END6,EE4END12};
cus_mux41 inst_cus_mux41_W2BEGb4 (
    .A0(W2BEGb4_input[0]),
    .A1(W2BEGb4_input[1]),
    .A2(W2BEGb4_input[2]),
    .A3(W2BEGb4_input[3]),
    .S0(ConfigBits[32+0]),
    .S0N(ConfigBits_N[32+0]),
    .S1(ConfigBits[32+1]),
    .S1N(ConfigBits_N[32+1]),
    .X(W2BEGb4)
);

 //switch matrix multiplexer W2BEGb5 MUX-4
assign W2BEGb5_input = {DOUT13,DOUT5,E6END7,EE4END13};
cus_mux41 inst_cus_mux41_W2BEGb5 (
    .A0(W2BEGb5_input[0]),
    .A1(W2BEGb5_input[1]),
    .A2(W2BEGb5_input[2]),
    .A3(W2BEGb5_input[3]),
    .S0(ConfigBits[34+0]),
    .S0N(ConfigBits_N[34+0]),
    .S1(ConfigBits[34+1]),
    .S1N(ConfigBits_N[34+1]),
    .X(W2BEGb5)
);

 //switch matrix multiplexer W2BEGb6 MUX-4
assign W2BEGb6_input = {DOUT14,DOUT6,E6END8,EE4END14};
cus_mux41 inst_cus_mux41_W2BEGb6 (
    .A0(W2BEGb6_input[0]),
    .A1(W2BEGb6_input[1]),
    .A2(W2BEGb6_input[2]),
    .A3(W2BEGb6_input[3]),
    .S0(ConfigBits[36+0]),
    .S0N(ConfigBits_N[36+0]),
    .S1(ConfigBits[36+1]),
    .S1N(ConfigBits_N[36+1]),
    .X(W2BEGb6)
);

 //switch matrix multiplexer W2BEGb7 MUX-4
assign W2BEGb7_input = {DOUT15,DOUT7,E6END9,EE4END15};
cus_mux41 inst_cus_mux41_W2BEGb7 (
    .A0(W2BEGb7_input[0]),
    .A1(W2BEGb7_input[1]),
    .A2(W2BEGb7_input[2]),
    .A3(W2BEGb7_input[3]),
    .S0(ConfigBits[38+0]),
    .S0N(ConfigBits_N[38+0]),
    .S1(ConfigBits[38+1]),
    .S1N(ConfigBits_N[38+1]),
    .X(W2BEGb7)
);

 //switch matrix multiplexer WW4BEG0 MUX-4
assign WW4BEG0_input = {DOUT12,DOUT0,EE4END15,E1END3};
cus_mux41 inst_cus_mux41_WW4BEG0 (
    .A0(WW4BEG0_input[0]),
    .A1(WW4BEG0_input[1]),
    .A2(WW4BEG0_input[2]),
    .A3(WW4BEG0_input[3]),
    .S0(ConfigBits[40+0]),
    .S0N(ConfigBits_N[40+0]),
    .S1(ConfigBits[40+1]),
    .S1N(ConfigBits_N[40+1]),
    .X(WW4BEG0)
);

 //switch matrix multiplexer WW4BEG1 MUX-4
assign WW4BEG1_input = {DOUT13,DOUT1,EE4END14,E1END2};
cus_mux41 inst_cus_mux41_WW4BEG1 (
    .A0(WW4BEG1_input[0]),
    .A1(WW4BEG1_input[1]),
    .A2(WW4BEG1_input[2]),
    .A3(WW4BEG1_input[3]),
    .S0(ConfigBits[42+0]),
    .S0N(ConfigBits_N[42+0]),
    .S1(ConfigBits[42+1]),
    .S1N(ConfigBits_N[42+1]),
    .X(WW4BEG1)
);

 //switch matrix multiplexer WW4BEG2 MUX-4
assign WW4BEG2_input = {DOUT14,DOUT2,EE4END13,E2END0};
cus_mux41 inst_cus_mux41_WW4BEG2 (
    .A0(WW4BEG2_input[0]),
    .A1(WW4BEG2_input[1]),
    .A2(WW4BEG2_input[2]),
    .A3(WW4BEG2_input[3]),
    .S0(ConfigBits[44+0]),
    .S0N(ConfigBits_N[44+0]),
    .S1(ConfigBits[44+1]),
    .S1N(ConfigBits_N[44+1]),
    .X(WW4BEG2)
);

 //switch matrix multiplexer WW4BEG3 MUX-4
assign WW4BEG3_input = {DOUT15,DOUT3,EE4END12,E2END1};
cus_mux41 inst_cus_mux41_WW4BEG3 (
    .A0(WW4BEG3_input[0]),
    .A1(WW4BEG3_input[1]),
    .A2(WW4BEG3_input[2]),
    .A3(WW4BEG3_input[3]),
    .S0(ConfigBits[46+0]),
    .S0N(ConfigBits_N[46+0]),
    .S1(ConfigBits[46+1]),
    .S1N(ConfigBits_N[46+1]),
    .X(WW4BEG3)
);

 //switch matrix multiplexer WW4BEG4 MUX-4
assign WW4BEG4_input = {DOUT8,DOUT4,EE4END11,E2END2};
cus_mux41 inst_cus_mux41_WW4BEG4 (
    .A0(WW4BEG4_input[0]),
    .A1(WW4BEG4_input[1]),
    .A2(WW4BEG4_input[2]),
    .A3(WW4BEG4_input[3]),
    .S0(ConfigBits[48+0]),
    .S0N(ConfigBits_N[48+0]),
    .S1(ConfigBits[48+1]),
    .S1N(ConfigBits_N[48+1]),
    .X(WW4BEG4)
);

 //switch matrix multiplexer WW4BEG5 MUX-4
assign WW4BEG5_input = {DOUT9,DOUT5,EE4END10,E2END3};
cus_mux41 inst_cus_mux41_WW4BEG5 (
    .A0(WW4BEG5_input[0]),
    .A1(WW4BEG5_input[1]),
    .A2(WW4BEG5_input[2]),
    .A3(WW4BEG5_input[3]),
    .S0(ConfigBits[50+0]),
    .S0N(ConfigBits_N[50+0]),
    .S1(ConfigBits[50+1]),
    .S1N(ConfigBits_N[50+1]),
    .X(WW4BEG5)
);

 //switch matrix multiplexer WW4BEG6 MUX-4
assign WW4BEG6_input = {DOUT10,DOUT6,E6END0,EE4END9};
cus_mux41 inst_cus_mux41_WW4BEG6 (
    .A0(WW4BEG6_input[0]),
    .A1(WW4BEG6_input[1]),
    .A2(WW4BEG6_input[2]),
    .A3(WW4BEG6_input[3]),
    .S0(ConfigBits[52+0]),
    .S0N(ConfigBits_N[52+0]),
    .S1(ConfigBits[52+1]),
    .S1N(ConfigBits_N[52+1]),
    .X(WW4BEG6)
);

 //switch matrix multiplexer WW4BEG7 MUX-4
assign WW4BEG7_input = {DOUT11,DOUT7,E6END4,EE4END8};
cus_mux41 inst_cus_mux41_WW4BEG7 (
    .A0(WW4BEG7_input[0]),
    .A1(WW4BEG7_input[1]),
    .A2(WW4BEG7_input[2]),
    .A3(WW4BEG7_input[3]),
    .S0(ConfigBits[54+0]),
    .S0N(ConfigBits_N[54+0]),
    .S1(ConfigBits[54+1]),
    .S1N(ConfigBits_N[54+1]),
    .X(WW4BEG7)
);

 //switch matrix multiplexer WW4BEG8 MUX-4
assign WW4BEG8_input = {DOUT8,DOUT4,E6END8,EE4END0};
cus_mux41 inst_cus_mux41_WW4BEG8 (
    .A0(WW4BEG8_input[0]),
    .A1(WW4BEG8_input[1]),
    .A2(WW4BEG8_input[2]),
    .A3(WW4BEG8_input[3]),
    .S0(ConfigBits[56+0]),
    .S0N(ConfigBits_N[56+0]),
    .S1(ConfigBits[56+1]),
    .S1N(ConfigBits_N[56+1]),
    .X(WW4BEG8)
);

 //switch matrix multiplexer WW4BEG9 MUX-4
assign WW4BEG9_input = {DOUT9,DOUT5,E6END11,EE4END1};
cus_mux41 inst_cus_mux41_WW4BEG9 (
    .A0(WW4BEG9_input[0]),
    .A1(WW4BEG9_input[1]),
    .A2(WW4BEG9_input[2]),
    .A3(WW4BEG9_input[3]),
    .S0(ConfigBits[58+0]),
    .S0N(ConfigBits_N[58+0]),
    .S1(ConfigBits[58+1]),
    .S1N(ConfigBits_N[58+1]),
    .X(WW4BEG9)
);

 //switch matrix multiplexer WW4BEG10 MUX-4
assign WW4BEG10_input = {DOUT10,DOUT6,EE4END2,E2END4};
cus_mux41 inst_cus_mux41_WW4BEG10 (
    .A0(WW4BEG10_input[0]),
    .A1(WW4BEG10_input[1]),
    .A2(WW4BEG10_input[2]),
    .A3(WW4BEG10_input[3]),
    .S0(ConfigBits[60+0]),
    .S0N(ConfigBits_N[60+0]),
    .S1(ConfigBits[60+1]),
    .S1N(ConfigBits_N[60+1]),
    .X(WW4BEG10)
);

 //switch matrix multiplexer WW4BEG11 MUX-4
assign WW4BEG11_input = {DOUT11,DOUT7,EE4END3,E2END5};
cus_mux41 inst_cus_mux41_WW4BEG11 (
    .A0(WW4BEG11_input[0]),
    .A1(WW4BEG11_input[1]),
    .A2(WW4BEG11_input[2]),
    .A3(WW4BEG11_input[3]),
    .S0(ConfigBits[62+0]),
    .S0N(ConfigBits_N[62+0]),
    .S1(ConfigBits[62+1]),
    .S1N(ConfigBits_N[62+1]),
    .X(WW4BEG11)
);

 //switch matrix multiplexer WW4BEG12 MUX-4
assign WW4BEG12_input = {DOUT12,DOUT0,EE4END4,E2END6};
cus_mux41 inst_cus_mux41_WW4BEG12 (
    .A0(WW4BEG12_input[0]),
    .A1(WW4BEG12_input[1]),
    .A2(WW4BEG12_input[2]),
    .A3(WW4BEG12_input[3]),
    .S0(ConfigBits[64+0]),
    .S0N(ConfigBits_N[64+0]),
    .S1(ConfigBits[64+1]),
    .S1N(ConfigBits_N[64+1]),
    .X(WW4BEG12)
);

 //switch matrix multiplexer WW4BEG13 MUX-4
assign WW4BEG13_input = {DOUT13,DOUT1,EE4END5,E2END7};
cus_mux41 inst_cus_mux41_WW4BEG13 (
    .A0(WW4BEG13_input[0]),
    .A1(WW4BEG13_input[1]),
    .A2(WW4BEG13_input[2]),
    .A3(WW4BEG13_input[3]),
    .S0(ConfigBits[66+0]),
    .S0N(ConfigBits_N[66+0]),
    .S1(ConfigBits[66+1]),
    .S1N(ConfigBits_N[66+1]),
    .X(WW4BEG13)
);

 //switch matrix multiplexer WW4BEG14 MUX-4
assign WW4BEG14_input = {DOUT14,DOUT2,EE4END6,E1END1};
cus_mux41 inst_cus_mux41_WW4BEG14 (
    .A0(WW4BEG14_input[0]),
    .A1(WW4BEG14_input[1]),
    .A2(WW4BEG14_input[2]),
    .A3(WW4BEG14_input[3]),
    .S0(ConfigBits[68+0]),
    .S0N(ConfigBits_N[68+0]),
    .S1(ConfigBits[68+1]),
    .S1N(ConfigBits_N[68+1]),
    .X(WW4BEG14)
);

 //switch matrix multiplexer WW4BEG15 MUX-4
assign WW4BEG15_input = {DOUT15,DOUT3,EE4END7,E1END0};
cus_mux41 inst_cus_mux41_WW4BEG15 (
    .A0(WW4BEG15_input[0]),
    .A1(WW4BEG15_input[1]),
    .A2(WW4BEG15_input[2]),
    .A3(WW4BEG15_input[3]),
    .S0(ConfigBits[70+0]),
    .S0N(ConfigBits_N[70+0]),
    .S1(ConfigBits[70+1]),
    .S1N(ConfigBits_N[70+1]),
    .X(WW4BEG15)
);

 //switch matrix multiplexer W6BEG0 MUX-2
assign W6BEG0_input = {DOUT8,EE4END0};
cus_mux21 inst_cus_mux21_W6BEG0 (
    .A0(W6BEG0_input[0]),
    .A1(W6BEG0_input[1]),
    .S(ConfigBits[72+0]),
    .X(W6BEG0)
);

 //switch matrix multiplexer W6BEG1 MUX-2
assign W6BEG1_input = {DOUT9,EE4END1};
cus_mux21 inst_cus_mux21_W6BEG1 (
    .A0(W6BEG1_input[0]),
    .A1(W6BEG1_input[1]),
    .S(ConfigBits[73+0]),
    .X(W6BEG1)
);

 //switch matrix multiplexer W6BEG2 MUX-2
assign W6BEG2_input = {DOUT10,EE4END2};
cus_mux21 inst_cus_mux21_W6BEG2 (
    .A0(W6BEG2_input[0]),
    .A1(W6BEG2_input[1]),
    .S(ConfigBits[74+0]),
    .X(W6BEG2)
);

 //switch matrix multiplexer W6BEG3 MUX-2
assign W6BEG3_input = {DOUT11,EE4END3};
cus_mux21 inst_cus_mux21_W6BEG3 (
    .A0(W6BEG3_input[0]),
    .A1(W6BEG3_input[1]),
    .S(ConfigBits[75+0]),
    .X(W6BEG3)
);

 //switch matrix multiplexer W6BEG4 MUX-2
assign W6BEG4_input = {DOUT12,DOUT4};
cus_mux21 inst_cus_mux21_W6BEG4 (
    .A0(W6BEG4_input[0]),
    .A1(W6BEG4_input[1]),
    .S(ConfigBits[76+0]),
    .X(W6BEG4)
);

 //switch matrix multiplexer W6BEG5 MUX-2
assign W6BEG5_input = {DOUT13,DOUT5};
cus_mux21 inst_cus_mux21_W6BEG5 (
    .A0(W6BEG5_input[0]),
    .A1(W6BEG5_input[1]),
    .S(ConfigBits[77+0]),
    .X(W6BEG5)
);

 //switch matrix multiplexer W6BEG6 MUX-2
assign W6BEG6_input = {DOUT14,DOUT6};
cus_mux21 inst_cus_mux21_W6BEG6 (
    .A0(W6BEG6_input[0]),
    .A1(W6BEG6_input[1]),
    .S(ConfigBits[78+0]),
    .X(W6BEG6)
);

 //switch matrix multiplexer W6BEG7 MUX-2
assign W6BEG7_input = {DOUT15,DOUT7};
cus_mux21 inst_cus_mux21_W6BEG7 (
    .A0(W6BEG7_input[0]),
    .A1(W6BEG7_input[1]),
    .S(ConfigBits[79+0]),
    .X(W6BEG7)
);

 //switch matrix multiplexer W6BEG8 MUX-2
assign W6BEG8_input = {DOUT0,E6END0};
cus_mux21 inst_cus_mux21_W6BEG8 (
    .A0(W6BEG8_input[0]),
    .A1(W6BEG8_input[1]),
    .S(ConfigBits[80+0]),
    .X(W6BEG8)
);

 //switch matrix multiplexer W6BEG9 MUX-2
assign W6BEG9_input = {DOUT1,E6END4};
cus_mux21 inst_cus_mux21_W6BEG9 (
    .A0(W6BEG9_input[0]),
    .A1(W6BEG9_input[1]),
    .S(ConfigBits[81+0]),
    .X(W6BEG9)
);

 //switch matrix multiplexer W6BEG10 MUX-2
assign W6BEG10_input = {DOUT2,E6END8};
cus_mux21 inst_cus_mux21_W6BEG10 (
    .A0(W6BEG10_input[0]),
    .A1(W6BEG10_input[1]),
    .S(ConfigBits[82+0]),
    .X(W6BEG10)
);

 //switch matrix multiplexer W6BEG11 MUX-2
assign W6BEG11_input = {DOUT3,E6END11};
cus_mux21 inst_cus_mux21_W6BEG11 (
    .A0(W6BEG11_input[0]),
    .A1(W6BEG11_input[1]),
    .S(ConfigBits[83+0]),
    .X(W6BEG11)
);

 //switch matrix multiplexer bot2top_DOUT0 MUX-1
assign bot2top_DOUT0 = DOUT16;

 //switch matrix multiplexer bot2top_DOUT1 MUX-1
assign bot2top_DOUT1 = DOUT17;

 //switch matrix multiplexer bot2top_DOUT2 MUX-1
assign bot2top_DOUT2 = DOUT18;

 //switch matrix multiplexer bot2top_DOUT3 MUX-1
assign bot2top_DOUT3 = DOUT19;

 //switch matrix multiplexer bot2top_DOUT4 MUX-1
assign bot2top_DOUT4 = DOUT20;

 //switch matrix multiplexer bot2top_DOUT5 MUX-1
assign bot2top_DOUT5 = DOUT21;

 //switch matrix multiplexer bot2top_DOUT6 MUX-1
assign bot2top_DOUT6 = DOUT22;

 //switch matrix multiplexer bot2top_DOUT7 MUX-1
assign bot2top_DOUT7 = DOUT23;

 //switch matrix multiplexer bot2top_DOUT8 MUX-1
assign bot2top_DOUT8 = DOUT24;

 //switch matrix multiplexer bot2top_DOUT9 MUX-1
assign bot2top_DOUT9 = DOUT25;

 //switch matrix multiplexer bot2top_DOUT10 MUX-1
assign bot2top_DOUT10 = DOUT26;

 //switch matrix multiplexer bot2top_DOUT11 MUX-1
assign bot2top_DOUT11 = DOUT27;

 //switch matrix multiplexer bot2top_DOUT12 MUX-1
assign bot2top_DOUT12 = DOUT28;

 //switch matrix multiplexer bot2top_DOUT13 MUX-1
assign bot2top_DOUT13 = DOUT29;

 //switch matrix multiplexer bot2top_DOUT14 MUX-1
assign bot2top_DOUT14 = DOUT30;

 //switch matrix multiplexer bot2top_DOUT15 MUX-1
assign bot2top_DOUT15 = DOUT31;

 //switch matrix multiplexer CLK MUX-4
assign CLK_input = {N_GBUF_END3,N_GBUF_END2,N_GBUF_END1,N_GBUF_END0};
cus_mux41 inst_cus_mux41_CLK (
    .A0(CLK_input[0]),
    .A1(CLK_input[1]),
    .A2(CLK_input[2]),
    .A3(CLK_input[3]),
    .S0(ConfigBits[84+0]),
    .S0N(ConfigBits_N[84+0]),
    .S1(ConfigBits[84+1]),
    .S1N(ConfigBits_N[84+1]),
    .X(CLK)
);

 //switch matrix multiplexer ADDR0 MUX-4
assign ADDR0_input = {GND0,E2END0,E2MID0,E1END0};
cus_mux41 inst_cus_mux41_ADDR0 (
    .A0(ADDR0_input[0]),
    .A1(ADDR0_input[1]),
    .A2(ADDR0_input[2]),
    .A3(ADDR0_input[3]),
    .S0(ConfigBits[86+0]),
    .S0N(ConfigBits_N[86+0]),
    .S1(ConfigBits[86+1]),
    .S1N(ConfigBits_N[86+1]),
    .X(ADDR0)
);

 //switch matrix multiplexer ADDR1 MUX-4
assign ADDR1_input = {GND0,E2END1,E2MID1,E1END1};
cus_mux41 inst_cus_mux41_ADDR1 (
    .A0(ADDR1_input[0]),
    .A1(ADDR1_input[1]),
    .A2(ADDR1_input[2]),
    .A3(ADDR1_input[3]),
    .S0(ConfigBits[88+0]),
    .S0N(ConfigBits_N[88+0]),
    .S1(ConfigBits[88+1]),
    .S1N(ConfigBits_N[88+1]),
    .X(ADDR1)
);

 //switch matrix multiplexer ADDR2 MUX-4
assign ADDR2_input = {GND0,E2END2,E2MID2,E1END2};
cus_mux41 inst_cus_mux41_ADDR2 (
    .A0(ADDR2_input[0]),
    .A1(ADDR2_input[1]),
    .A2(ADDR2_input[2]),
    .A3(ADDR2_input[3]),
    .S0(ConfigBits[90+0]),
    .S0N(ConfigBits_N[90+0]),
    .S1(ConfigBits[90+1]),
    .S1N(ConfigBits_N[90+1]),
    .X(ADDR2)
);

 //switch matrix multiplexer ADDR3 MUX-4
assign ADDR3_input = {GND0,E2END3,E2MID3,E1END3};
cus_mux41 inst_cus_mux41_ADDR3 (
    .A0(ADDR3_input[0]),
    .A1(ADDR3_input[1]),
    .A2(ADDR3_input[2]),
    .A3(ADDR3_input[3]),
    .S0(ConfigBits[92+0]),
    .S0N(ConfigBits_N[92+0]),
    .S1(ConfigBits[92+1]),
    .S1N(ConfigBits_N[92+1]),
    .X(ADDR3)
);

 //switch matrix multiplexer ADDR4 MUX-4
assign ADDR4_input = {GND0,E2END4,E2MID5,E2MID4};
cus_mux41 inst_cus_mux41_ADDR4 (
    .A0(ADDR4_input[0]),
    .A1(ADDR4_input[1]),
    .A2(ADDR4_input[2]),
    .A3(ADDR4_input[3]),
    .S0(ConfigBits[94+0]),
    .S0N(ConfigBits_N[94+0]),
    .S1(ConfigBits[94+1]),
    .S1N(ConfigBits_N[94+1]),
    .X(ADDR4)
);

 //switch matrix multiplexer ADDR5 MUX-1
assign ADDR5 = top2bot_ADDR0;

 //switch matrix multiplexer ADDR6 MUX-1
assign ADDR6 = top2bot_ADDR1;

 //switch matrix multiplexer ADDR7 MUX-1
assign ADDR7 = top2bot_ADDR2;

 //switch matrix multiplexer ADDR8 MUX-1
assign ADDR8 = top2bot_ADDR3;

 //switch matrix multiplexer ADDR9 MUX-1
assign ADDR9 = top2bot_ADDR4;

 //switch matrix multiplexer DIN0 MUX-4
assign DIN0_input = {E6END0,EE4END8,EE4END0,E2MID0};
cus_mux41 inst_cus_mux41_DIN0 (
    .A0(DIN0_input[0]),
    .A1(DIN0_input[1]),
    .A2(DIN0_input[2]),
    .A3(DIN0_input[3]),
    .S0(ConfigBits[96+0]),
    .S0N(ConfigBits_N[96+0]),
    .S1(ConfigBits[96+1]),
    .S1N(ConfigBits_N[96+1]),
    .X(DIN0)
);

 //switch matrix multiplexer DIN1 MUX-4
assign DIN1_input = {E6END1,EE4END9,EE4END1,E2MID1};
cus_mux41 inst_cus_mux41_DIN1 (
    .A0(DIN1_input[0]),
    .A1(DIN1_input[1]),
    .A2(DIN1_input[2]),
    .A3(DIN1_input[3]),
    .S0(ConfigBits[98+0]),
    .S0N(ConfigBits_N[98+0]),
    .S1(ConfigBits[98+1]),
    .S1N(ConfigBits_N[98+1]),
    .X(DIN1)
);

 //switch matrix multiplexer DIN2 MUX-4
assign DIN2_input = {E6END2,EE4END10,EE4END2,E2MID2};
cus_mux41 inst_cus_mux41_DIN2 (
    .A0(DIN2_input[0]),
    .A1(DIN2_input[1]),
    .A2(DIN2_input[2]),
    .A3(DIN2_input[3]),
    .S0(ConfigBits[100+0]),
    .S0N(ConfigBits_N[100+0]),
    .S1(ConfigBits[100+1]),
    .S1N(ConfigBits_N[100+1]),
    .X(DIN2)
);

 //switch matrix multiplexer DIN3 MUX-4
assign DIN3_input = {E6END3,EE4END11,EE4END3,E2MID3};
cus_mux41 inst_cus_mux41_DIN3 (
    .A0(DIN3_input[0]),
    .A1(DIN3_input[1]),
    .A2(DIN3_input[2]),
    .A3(DIN3_input[3]),
    .S0(ConfigBits[102+0]),
    .S0N(ConfigBits_N[102+0]),
    .S1(ConfigBits[102+1]),
    .S1N(ConfigBits_N[102+1]),
    .X(DIN3)
);

 //switch matrix multiplexer DIN4 MUX-4
assign DIN4_input = {E6END4,EE4END12,EE4END4,E2MID4};
cus_mux41 inst_cus_mux41_DIN4 (
    .A0(DIN4_input[0]),
    .A1(DIN4_input[1]),
    .A2(DIN4_input[2]),
    .A3(DIN4_input[3]),
    .S0(ConfigBits[104+0]),
    .S0N(ConfigBits_N[104+0]),
    .S1(ConfigBits[104+1]),
    .S1N(ConfigBits_N[104+1]),
    .X(DIN4)
);

 //switch matrix multiplexer DIN5 MUX-4
assign DIN5_input = {E6END5,EE4END13,EE4END5,E2MID5};
cus_mux41 inst_cus_mux41_DIN5 (
    .A0(DIN5_input[0]),
    .A1(DIN5_input[1]),
    .A2(DIN5_input[2]),
    .A3(DIN5_input[3]),
    .S0(ConfigBits[106+0]),
    .S0N(ConfigBits_N[106+0]),
    .S1(ConfigBits[106+1]),
    .S1N(ConfigBits_N[106+1]),
    .X(DIN5)
);

 //switch matrix multiplexer DIN6 MUX-4
assign DIN6_input = {E6END6,EE4END14,EE4END6,E2MID6};
cus_mux41 inst_cus_mux41_DIN6 (
    .A0(DIN6_input[0]),
    .A1(DIN6_input[1]),
    .A2(DIN6_input[2]),
    .A3(DIN6_input[3]),
    .S0(ConfigBits[108+0]),
    .S0N(ConfigBits_N[108+0]),
    .S1(ConfigBits[108+1]),
    .S1N(ConfigBits_N[108+1]),
    .X(DIN6)
);

 //switch matrix multiplexer DIN7 MUX-4
assign DIN7_input = {E6END7,EE4END15,EE4END7,E2MID7};
cus_mux41 inst_cus_mux41_DIN7 (
    .A0(DIN7_input[0]),
    .A1(DIN7_input[1]),
    .A2(DIN7_input[2]),
    .A3(DIN7_input[3]),
    .S0(ConfigBits[110+0]),
    .S0N(ConfigBits_N[110+0]),
    .S1(ConfigBits[110+1]),
    .S1N(ConfigBits_N[110+1]),
    .X(DIN7)
);

 //switch matrix multiplexer DIN8 MUX-4
assign DIN8_input = {E6END8,EE4END8,EE4END0,E2END0};
cus_mux41 inst_cus_mux41_DIN8 (
    .A0(DIN8_input[0]),
    .A1(DIN8_input[1]),
    .A2(DIN8_input[2]),
    .A3(DIN8_input[3]),
    .S0(ConfigBits[112+0]),
    .S0N(ConfigBits_N[112+0]),
    .S1(ConfigBits[112+1]),
    .S1N(ConfigBits_N[112+1]),
    .X(DIN8)
);

 //switch matrix multiplexer DIN9 MUX-4
assign DIN9_input = {E6END9,EE4END9,EE4END1,E2END1};
cus_mux41 inst_cus_mux41_DIN9 (
    .A0(DIN9_input[0]),
    .A1(DIN9_input[1]),
    .A2(DIN9_input[2]),
    .A3(DIN9_input[3]),
    .S0(ConfigBits[114+0]),
    .S0N(ConfigBits_N[114+0]),
    .S1(ConfigBits[114+1]),
    .S1N(ConfigBits_N[114+1]),
    .X(DIN9)
);

 //switch matrix multiplexer DIN10 MUX-4
assign DIN10_input = {E6END10,EE4END10,EE4END2,E2END2};
cus_mux41 inst_cus_mux41_DIN10 (
    .A0(DIN10_input[0]),
    .A1(DIN10_input[1]),
    .A2(DIN10_input[2]),
    .A3(DIN10_input[3]),
    .S0(ConfigBits[116+0]),
    .S0N(ConfigBits_N[116+0]),
    .S1(ConfigBits[116+1]),
    .S1N(ConfigBits_N[116+1]),
    .X(DIN10)
);

 //switch matrix multiplexer DIN11 MUX-4
assign DIN11_input = {E6END11,EE4END11,EE4END3,E2END3};
cus_mux41 inst_cus_mux41_DIN11 (
    .A0(DIN11_input[0]),
    .A1(DIN11_input[1]),
    .A2(DIN11_input[2]),
    .A3(DIN11_input[3]),
    .S0(ConfigBits[118+0]),
    .S0N(ConfigBits_N[118+0]),
    .S1(ConfigBits[118+1]),
    .S1N(ConfigBits_N[118+1]),
    .X(DIN11)
);

 //switch matrix multiplexer DIN12 MUX-4
assign DIN12_input = {EE4END12,EE4END4,E2END4,E1END0};
cus_mux41 inst_cus_mux41_DIN12 (
    .A0(DIN12_input[0]),
    .A1(DIN12_input[1]),
    .A2(DIN12_input[2]),
    .A3(DIN12_input[3]),
    .S0(ConfigBits[120+0]),
    .S0N(ConfigBits_N[120+0]),
    .S1(ConfigBits[120+1]),
    .S1N(ConfigBits_N[120+1]),
    .X(DIN12)
);

 //switch matrix multiplexer DIN13 MUX-4
assign DIN13_input = {EE4END13,EE4END5,E2END5,E1END1};
cus_mux41 inst_cus_mux41_DIN13 (
    .A0(DIN13_input[0]),
    .A1(DIN13_input[1]),
    .A2(DIN13_input[2]),
    .A3(DIN13_input[3]),
    .S0(ConfigBits[122+0]),
    .S0N(ConfigBits_N[122+0]),
    .S1(ConfigBits[122+1]),
    .S1N(ConfigBits_N[122+1]),
    .X(DIN13)
);

 //switch matrix multiplexer DIN14 MUX-4
assign DIN14_input = {EE4END14,EE4END6,E2END6,E1END2};
cus_mux41 inst_cus_mux41_DIN14 (
    .A0(DIN14_input[0]),
    .A1(DIN14_input[1]),
    .A2(DIN14_input[2]),
    .A3(DIN14_input[3]),
    .S0(ConfigBits[124+0]),
    .S0N(ConfigBits_N[124+0]),
    .S1(ConfigBits[124+1]),
    .S1N(ConfigBits_N[124+1]),
    .X(DIN14)
);

 //switch matrix multiplexer DIN15 MUX-4
assign DIN15_input = {EE4END15,EE4END7,E2END7,E1END3};
cus_mux41 inst_cus_mux41_DIN15 (
    .A0(DIN15_input[0]),
    .A1(DIN15_input[1]),
    .A2(DIN15_input[2]),
    .A3(DIN15_input[3]),
    .S0(ConfigBits[126+0]),
    .S0N(ConfigBits_N[126+0]),
    .S1(ConfigBits[126+1]),
    .S1N(ConfigBits_N[126+1]),
    .X(DIN15)
);

 //switch matrix multiplexer DIN16 MUX-1
assign DIN16 = top2bot_DIN0;

 //switch matrix multiplexer DIN17 MUX-1
assign DIN17 = top2bot_DIN1;

 //switch matrix multiplexer DIN18 MUX-1
assign DIN18 = top2bot_DIN2;

 //switch matrix multiplexer DIN19 MUX-1
assign DIN19 = top2bot_DIN3;

 //switch matrix multiplexer DIN20 MUX-1
assign DIN20 = top2bot_DIN4;

 //switch matrix multiplexer DIN21 MUX-1
assign DIN21 = top2bot_DIN5;

 //switch matrix multiplexer DIN22 MUX-1
assign DIN22 = top2bot_DIN6;

 //switch matrix multiplexer DIN23 MUX-1
assign DIN23 = top2bot_DIN7;

 //switch matrix multiplexer DIN24 MUX-1
assign DIN24 = top2bot_DIN8;

 //switch matrix multiplexer DIN25 MUX-1
assign DIN25 = top2bot_DIN9;

 //switch matrix multiplexer DIN26 MUX-1
assign DIN26 = top2bot_DIN10;

 //switch matrix multiplexer DIN27 MUX-1
assign DIN27 = top2bot_DIN11;

 //switch matrix multiplexer DIN28 MUX-1
assign DIN28 = top2bot_DIN12;

 //switch matrix multiplexer DIN29 MUX-1
assign DIN29 = top2bot_DIN13;

 //switch matrix multiplexer DIN30 MUX-1
assign DIN30 = top2bot_DIN14;

 //switch matrix multiplexer DIN31 MUX-1
assign DIN31 = top2bot_DIN15;

 //switch matrix multiplexer BM0 MUX-4
assign BM0_input = {E6END0,EE4END8,EE4END0,E2MID7};
cus_mux41 inst_cus_mux41_BM0 (
    .A0(BM0_input[0]),
    .A1(BM0_input[1]),
    .A2(BM0_input[2]),
    .A3(BM0_input[3]),
    .S0(ConfigBits[128+0]),
    .S0N(ConfigBits_N[128+0]),
    .S1(ConfigBits[128+1]),
    .S1N(ConfigBits_N[128+1]),
    .X(BM0)
);

 //switch matrix multiplexer BM1 MUX-4
assign BM1_input = {E6END1,EE4END9,EE4END1,E2MID6};
cus_mux41 inst_cus_mux41_BM1 (
    .A0(BM1_input[0]),
    .A1(BM1_input[1]),
    .A2(BM1_input[2]),
    .A3(BM1_input[3]),
    .S0(ConfigBits[130+0]),
    .S0N(ConfigBits_N[130+0]),
    .S1(ConfigBits[130+1]),
    .S1N(ConfigBits_N[130+1]),
    .X(BM1)
);

 //switch matrix multiplexer BM2 MUX-4
assign BM2_input = {E6END2,EE4END10,EE4END2,E2MID5};
cus_mux41 inst_cus_mux41_BM2 (
    .A0(BM2_input[0]),
    .A1(BM2_input[1]),
    .A2(BM2_input[2]),
    .A3(BM2_input[3]),
    .S0(ConfigBits[132+0]),
    .S0N(ConfigBits_N[132+0]),
    .S1(ConfigBits[132+1]),
    .S1N(ConfigBits_N[132+1]),
    .X(BM2)
);

 //switch matrix multiplexer BM3 MUX-4
assign BM3_input = {E6END3,EE4END11,EE4END3,E2MID4};
cus_mux41 inst_cus_mux41_BM3 (
    .A0(BM3_input[0]),
    .A1(BM3_input[1]),
    .A2(BM3_input[2]),
    .A3(BM3_input[3]),
    .S0(ConfigBits[134+0]),
    .S0N(ConfigBits_N[134+0]),
    .S1(ConfigBits[134+1]),
    .S1N(ConfigBits_N[134+1]),
    .X(BM3)
);

 //switch matrix multiplexer BM4 MUX-4
assign BM4_input = {E6END4,EE4END12,EE4END4,E2MID3};
cus_mux41 inst_cus_mux41_BM4 (
    .A0(BM4_input[0]),
    .A1(BM4_input[1]),
    .A2(BM4_input[2]),
    .A3(BM4_input[3]),
    .S0(ConfigBits[136+0]),
    .S0N(ConfigBits_N[136+0]),
    .S1(ConfigBits[136+1]),
    .S1N(ConfigBits_N[136+1]),
    .X(BM4)
);

 //switch matrix multiplexer BM5 MUX-4
assign BM5_input = {E6END5,EE4END13,EE4END5,E2MID2};
cus_mux41 inst_cus_mux41_BM5 (
    .A0(BM5_input[0]),
    .A1(BM5_input[1]),
    .A2(BM5_input[2]),
    .A3(BM5_input[3]),
    .S0(ConfigBits[138+0]),
    .S0N(ConfigBits_N[138+0]),
    .S1(ConfigBits[138+1]),
    .S1N(ConfigBits_N[138+1]),
    .X(BM5)
);

 //switch matrix multiplexer BM6 MUX-4
assign BM6_input = {E6END6,EE4END14,EE4END6,E2MID1};
cus_mux41 inst_cus_mux41_BM6 (
    .A0(BM6_input[0]),
    .A1(BM6_input[1]),
    .A2(BM6_input[2]),
    .A3(BM6_input[3]),
    .S0(ConfigBits[140+0]),
    .S0N(ConfigBits_N[140+0]),
    .S1(ConfigBits[140+1]),
    .S1N(ConfigBits_N[140+1]),
    .X(BM6)
);

 //switch matrix multiplexer BM7 MUX-4
assign BM7_input = {E6END7,EE4END15,EE4END7,E2MID0};
cus_mux41 inst_cus_mux41_BM7 (
    .A0(BM7_input[0]),
    .A1(BM7_input[1]),
    .A2(BM7_input[2]),
    .A3(BM7_input[3]),
    .S0(ConfigBits[142+0]),
    .S0N(ConfigBits_N[142+0]),
    .S1(ConfigBits[142+1]),
    .S1N(ConfigBits_N[142+1]),
    .X(BM7)
);

 //switch matrix multiplexer BM8 MUX-4
assign BM8_input = {E6END8,EE4END8,EE4END0,E2END7};
cus_mux41 inst_cus_mux41_BM8 (
    .A0(BM8_input[0]),
    .A1(BM8_input[1]),
    .A2(BM8_input[2]),
    .A3(BM8_input[3]),
    .S0(ConfigBits[144+0]),
    .S0N(ConfigBits_N[144+0]),
    .S1(ConfigBits[144+1]),
    .S1N(ConfigBits_N[144+1]),
    .X(BM8)
);

 //switch matrix multiplexer BM9 MUX-4
assign BM9_input = {E6END9,EE4END9,EE4END1,E2END6};
cus_mux41 inst_cus_mux41_BM9 (
    .A0(BM9_input[0]),
    .A1(BM9_input[1]),
    .A2(BM9_input[2]),
    .A3(BM9_input[3]),
    .S0(ConfigBits[146+0]),
    .S0N(ConfigBits_N[146+0]),
    .S1(ConfigBits[146+1]),
    .S1N(ConfigBits_N[146+1]),
    .X(BM9)
);

 //switch matrix multiplexer BM10 MUX-4
assign BM10_input = {E6END10,EE4END10,EE4END2,E2END5};
cus_mux41 inst_cus_mux41_BM10 (
    .A0(BM10_input[0]),
    .A1(BM10_input[1]),
    .A2(BM10_input[2]),
    .A3(BM10_input[3]),
    .S0(ConfigBits[148+0]),
    .S0N(ConfigBits_N[148+0]),
    .S1(ConfigBits[148+1]),
    .S1N(ConfigBits_N[148+1]),
    .X(BM10)
);

 //switch matrix multiplexer BM11 MUX-4
assign BM11_input = {E6END11,EE4END11,EE4END3,E2END4};
cus_mux41 inst_cus_mux41_BM11 (
    .A0(BM11_input[0]),
    .A1(BM11_input[1]),
    .A2(BM11_input[2]),
    .A3(BM11_input[3]),
    .S0(ConfigBits[150+0]),
    .S0N(ConfigBits_N[150+0]),
    .S1(ConfigBits[150+1]),
    .S1N(ConfigBits_N[150+1]),
    .X(BM11)
);

 //switch matrix multiplexer BM12 MUX-4
assign BM12_input = {EE4END12,EE4END4,E2END3,E1END0};
cus_mux41 inst_cus_mux41_BM12 (
    .A0(BM12_input[0]),
    .A1(BM12_input[1]),
    .A2(BM12_input[2]),
    .A3(BM12_input[3]),
    .S0(ConfigBits[152+0]),
    .S0N(ConfigBits_N[152+0]),
    .S1(ConfigBits[152+1]),
    .S1N(ConfigBits_N[152+1]),
    .X(BM12)
);

 //switch matrix multiplexer BM13 MUX-4
assign BM13_input = {EE4END13,EE4END5,E2END2,E1END1};
cus_mux41 inst_cus_mux41_BM13 (
    .A0(BM13_input[0]),
    .A1(BM13_input[1]),
    .A2(BM13_input[2]),
    .A3(BM13_input[3]),
    .S0(ConfigBits[154+0]),
    .S0N(ConfigBits_N[154+0]),
    .S1(ConfigBits[154+1]),
    .S1N(ConfigBits_N[154+1]),
    .X(BM13)
);

 //switch matrix multiplexer BM14 MUX-4
assign BM14_input = {EE4END14,EE4END6,E2END1,E1END2};
cus_mux41 inst_cus_mux41_BM14 (
    .A0(BM14_input[0]),
    .A1(BM14_input[1]),
    .A2(BM14_input[2]),
    .A3(BM14_input[3]),
    .S0(ConfigBits[156+0]),
    .S0N(ConfigBits_N[156+0]),
    .S1(ConfigBits[156+1]),
    .S1N(ConfigBits_N[156+1]),
    .X(BM14)
);

 //switch matrix multiplexer BM15 MUX-4
assign BM15_input = {EE4END15,EE4END7,E2END0,E1END3};
cus_mux41 inst_cus_mux41_BM15 (
    .A0(BM15_input[0]),
    .A1(BM15_input[1]),
    .A2(BM15_input[2]),
    .A3(BM15_input[3]),
    .S0(ConfigBits[158+0]),
    .S0N(ConfigBits_N[158+0]),
    .S1(ConfigBits[158+1]),
    .S1N(ConfigBits_N[158+1]),
    .X(BM15)
);

 //switch matrix multiplexer BM16 MUX-1
assign BM16 = top2bot_BM0;

 //switch matrix multiplexer BM17 MUX-1
assign BM17 = top2bot_BM1;

 //switch matrix multiplexer BM18 MUX-1
assign BM18 = top2bot_BM2;

 //switch matrix multiplexer BM19 MUX-1
assign BM19 = top2bot_BM3;

 //switch matrix multiplexer BM20 MUX-1
assign BM20 = top2bot_BM4;

 //switch matrix multiplexer BM21 MUX-1
assign BM21 = top2bot_BM5;

 //switch matrix multiplexer BM22 MUX-1
assign BM22 = top2bot_BM6;

 //switch matrix multiplexer BM23 MUX-1
assign BM23 = top2bot_BM7;

 //switch matrix multiplexer BM24 MUX-1
assign BM24 = top2bot_BM8;

 //switch matrix multiplexer BM25 MUX-1
assign BM25 = top2bot_BM9;

 //switch matrix multiplexer BM26 MUX-1
assign BM26 = top2bot_BM10;

 //switch matrix multiplexer BM27 MUX-1
assign BM27 = top2bot_BM11;

 //switch matrix multiplexer BM28 MUX-1
assign BM28 = top2bot_BM12;

 //switch matrix multiplexer BM29 MUX-1
assign BM29 = top2bot_BM13;

 //switch matrix multiplexer BM30 MUX-1
assign BM30 = top2bot_BM14;

 //switch matrix multiplexer BM31 MUX-1
assign BM31 = top2bot_BM15;

 //switch matrix multiplexer WEN MUX-15
assign WEN_input = {VCC0,GND0,E6END3,E6END2,E6END0,EE4END15,EE4END5,E2END4,E2END3,E2END2,E2END1,E2MID6,E2MID2,E1END3,E1END0};
cus_mux161 inst_cus_mux161_WEN (
    .A0(WEN_input[0]),
    .A1(WEN_input[1]),
    .A2(WEN_input[2]),
    .A3(WEN_input[3]),
    .A4(WEN_input[4]),
    .A5(WEN_input[5]),
    .A6(WEN_input[6]),
    .A7(WEN_input[7]),
    .A8(WEN_input[8]),
    .A9(WEN_input[9]),
    .A10(WEN_input[10]),
    .A11(WEN_input[11]),
    .A12(WEN_input[12]),
    .A13(WEN_input[13]),
    .A14(WEN_input[14]),
    .A15(GND0),
    .S0(ConfigBits[160+0]),
    .S0N(ConfigBits_N[160+0]),
    .S1(ConfigBits[160+1]),
    .S1N(ConfigBits_N[160+1]),
    .S2(ConfigBits[160+2]),
    .S2N(ConfigBits_N[160+2]),
    .S3(ConfigBits[160+3]),
    .S3N(ConfigBits_N[160+3]),
    .X(WEN)
);

 //switch matrix multiplexer MEN MUX-15
assign MEN_input = {VCC0,GND0,E6END3,E6END2,E6END0,EE4END15,EE4END5,E2END4,E2END3,E2END2,E2END1,E2MID6,E2MID2,E1END3,E1END0};
cus_mux161 inst_cus_mux161_MEN (
    .A0(MEN_input[0]),
    .A1(MEN_input[1]),
    .A2(MEN_input[2]),
    .A3(MEN_input[3]),
    .A4(MEN_input[4]),
    .A5(MEN_input[5]),
    .A6(MEN_input[6]),
    .A7(MEN_input[7]),
    .A8(MEN_input[8]),
    .A9(MEN_input[9]),
    .A10(MEN_input[10]),
    .A11(MEN_input[11]),
    .A12(MEN_input[12]),
    .A13(MEN_input[13]),
    .A14(MEN_input[14]),
    .A15(GND0),
    .S0(ConfigBits[164+0]),
    .S0N(ConfigBits_N[164+0]),
    .S1(ConfigBits[164+1]),
    .S1N(ConfigBits_N[164+1]),
    .S2(ConfigBits[164+2]),
    .S2N(ConfigBits_N[164+2]),
    .S3(ConfigBits[164+3]),
    .S3N(ConfigBits_N[164+3]),
    .X(MEN)
);

 //switch matrix multiplexer REN MUX-15
assign REN_input = {VCC0,GND0,E6END3,E6END2,E6END0,EE4END15,EE4END5,E2END4,E2END3,E2END2,E2END1,E2MID6,E2MID2,E1END3,E1END0};
cus_mux161 inst_cus_mux161_REN (
    .A0(REN_input[0]),
    .A1(REN_input[1]),
    .A2(REN_input[2]),
    .A3(REN_input[3]),
    .A4(REN_input[4]),
    .A5(REN_input[5]),
    .A6(REN_input[6]),
    .A7(REN_input[7]),
    .A8(REN_input[8]),
    .A9(REN_input[9]),
    .A10(REN_input[10]),
    .A11(REN_input[11]),
    .A12(REN_input[12]),
    .A13(REN_input[13]),
    .A14(REN_input[14]),
    .A15(GND0),
    .S0(ConfigBits[168+0]),
    .S0N(ConfigBits_N[168+0]),
    .S1(ConfigBits[168+1]),
    .S1N(ConfigBits_N[168+1]),
    .S2(ConfigBits[168+2]),
    .S2N(ConfigBits_N[168+2]),
    .S3(ConfigBits[168+3]),
    .S3N(ConfigBits_N[168+3]),
    .X(REN)
);

endmodule