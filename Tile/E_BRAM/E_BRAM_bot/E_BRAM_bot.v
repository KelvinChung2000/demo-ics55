module E_BRAM_bot
    #(
`ifdef EMULATION
        parameter [639:0] Emulate_Bitstream=640'b0,
`endif
        parameter MaxFramesPerCol=20,
        parameter FrameBitsPerRow=32,
        parameter NoConfigBits=172
    )
    (
 //N
        output  [3:0] N_GBUF_BEG,        //TilePort({N} OUTPUT N_GBUF_BEG[3:0])
        output  [15:0] bot2top_DOUT,        //TilePort({N} OUTPUT bot2top_DOUT[15:0])
        input  [15:0] top2bot_DIN,        //TilePort({N} INPUT top2bot_DIN[15:0])
        input  [15:0] top2bot_BM,        //TilePort({N} INPUT top2bot_BM[15:0])
        input  [4:0] top2bot_ADDR,        //TilePort({N} INPUT top2bot_ADDR[4:0])
 //W
        input  [3:0] E1END,        //TilePort({W} INPUT E1END[3:0])
        input  [7:0] E2MID,        //TilePort({W} INPUT E2MID[7:0])
        input  [7:0] E2END,        //TilePort({W} INPUT E2END[7:0])
        input  [15:0] EE4END,        //TilePort({W} INPUT EE4END[3:0])
        input  [11:0] E6END,        //TilePort({W} INPUT E6END[1:0])
        output  [3:0] W1BEG,        //TilePort({W} OUTPUT W1BEG[3:0])
        output  [7:0] W2BEG,        //TilePort({W} OUTPUT W2BEG[7:0])
        output  [7:0] W2BEGb,        //TilePort({W} OUTPUT W2BEGb[7:0])
        output  [15:0] WW4BEG,        //TilePort({W} OUTPUT WW4BEG[3:0])
        output  [11:0] W6BEG,        //TilePort({W} OUTPUT W6BEG[1:0])
 //S
        input  [3:0] N_GBUF_END,        //TilePort({S} INPUT N_GBUF_END[3:0])
        input  CONFIGURED_top,
    //Tile IO ports from BELs
        input  [FrameBitsPerRow-1:0] FrameData, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] FrameData_O,
        input  [MaxFramesPerCol-1:0] FrameStrobe, //CONFIG_PORT
        output  [MaxFramesPerCol-1:0] FrameStrobe_O
    //global
);
 //signal declarations
 //BEL ports (e.g., slices)
wire CLK;
wire ADDR0;
wire ADDR1;
wire ADDR2;
wire ADDR3;
wire ADDR4;
wire ADDR5;
wire ADDR6;
wire ADDR7;
wire ADDR8;
wire ADDR9;
wire DIN0;
wire DIN1;
wire DIN2;
wire DIN3;
wire DIN4;
wire DIN5;
wire DIN6;
wire DIN7;
wire DIN8;
wire DIN9;
wire DIN10;
wire DIN11;
wire DIN12;
wire DIN13;
wire DIN14;
wire DIN15;
wire DIN16;
wire DIN17;
wire DIN18;
wire DIN19;
wire DIN20;
wire DIN21;
wire DIN22;
wire DIN23;
wire DIN24;
wire DIN25;
wire DIN26;
wire DIN27;
wire DIN28;
wire DIN29;
wire DIN30;
wire DIN31;
wire BM0;
wire BM1;
wire BM2;
wire BM3;
wire BM4;
wire BM5;
wire BM6;
wire BM7;
wire BM8;
wire BM9;
wire BM10;
wire BM11;
wire BM12;
wire BM13;
wire BM14;
wire BM15;
wire BM16;
wire BM17;
wire BM18;
wire BM19;
wire BM20;
wire BM21;
wire BM22;
wire BM23;
wire BM24;
wire BM25;
wire BM26;
wire BM27;
wire BM28;
wire BM29;
wire BM30;
wire BM31;
wire WEN;
wire MEN;
wire REN;
wire DOUT0;
wire DOUT1;
wire DOUT2;
wire DOUT3;
wire DOUT4;
wire DOUT5;
wire DOUT6;
wire DOUT7;
wire DOUT8;
wire DOUT9;
wire DOUT10;
wire DOUT11;
wire DOUT12;
wire DOUT13;
wire DOUT14;
wire DOUT15;
wire DOUT16;
wire DOUT17;
wire DOUT18;
wire DOUT19;
wire DOUT20;
wire DOUT21;
wire DOUT22;
wire DOUT23;
wire DOUT24;
wire DOUT25;
wire DOUT26;
wire DOUT27;
wire DOUT28;
wire DOUT29;
wire DOUT30;
wire DOUT31;
 //Jump wires
 //internal configuration data signal to daisy-chain all BELs (if any and in the order they are listed in the fabric.csv)
wire[NoConfigBits-1:0] ConfigBits;
wire[NoConfigBits-1:0] ConfigBits_N;

 //Connection for outgoing wires
wire[FrameBitsPerRow-1:0] FrameData_i;
wire[FrameBitsPerRow-1:0] FrameData_O_i;
wire[MaxFramesPerCol-1:0] FrameStrobe_i;
wire[MaxFramesPerCol-1:0] FrameStrobe_O_i;

assign FrameData_O_i = FrameData_i;

my_buf data_inbuf_0 (
    .A(FrameData[0]),
    .X(FrameData_i[0])
);

my_buf data_inbuf_1 (
    .A(FrameData[1]),
    .X(FrameData_i[1])
);

my_buf data_inbuf_2 (
    .A(FrameData[2]),
    .X(FrameData_i[2])
);

my_buf data_inbuf_3 (
    .A(FrameData[3]),
    .X(FrameData_i[3])
);

my_buf data_inbuf_4 (
    .A(FrameData[4]),
    .X(FrameData_i[4])
);

my_buf data_inbuf_5 (
    .A(FrameData[5]),
    .X(FrameData_i[5])
);

my_buf data_inbuf_6 (
    .A(FrameData[6]),
    .X(FrameData_i[6])
);

my_buf data_inbuf_7 (
    .A(FrameData[7]),
    .X(FrameData_i[7])
);

my_buf data_inbuf_8 (
    .A(FrameData[8]),
    .X(FrameData_i[8])
);

my_buf data_inbuf_9 (
    .A(FrameData[9]),
    .X(FrameData_i[9])
);

my_buf data_inbuf_10 (
    .A(FrameData[10]),
    .X(FrameData_i[10])
);

my_buf data_inbuf_11 (
    .A(FrameData[11]),
    .X(FrameData_i[11])
);

my_buf data_inbuf_12 (
    .A(FrameData[12]),
    .X(FrameData_i[12])
);

my_buf data_inbuf_13 (
    .A(FrameData[13]),
    .X(FrameData_i[13])
);

my_buf data_inbuf_14 (
    .A(FrameData[14]),
    .X(FrameData_i[14])
);

my_buf data_inbuf_15 (
    .A(FrameData[15]),
    .X(FrameData_i[15])
);

my_buf data_inbuf_16 (
    .A(FrameData[16]),
    .X(FrameData_i[16])
);

my_buf data_inbuf_17 (
    .A(FrameData[17]),
    .X(FrameData_i[17])
);

my_buf data_inbuf_18 (
    .A(FrameData[18]),
    .X(FrameData_i[18])
);

my_buf data_inbuf_19 (
    .A(FrameData[19]),
    .X(FrameData_i[19])
);

my_buf data_inbuf_20 (
    .A(FrameData[20]),
    .X(FrameData_i[20])
);

my_buf data_inbuf_21 (
    .A(FrameData[21]),
    .X(FrameData_i[21])
);

my_buf data_inbuf_22 (
    .A(FrameData[22]),
    .X(FrameData_i[22])
);

my_buf data_inbuf_23 (
    .A(FrameData[23]),
    .X(FrameData_i[23])
);

my_buf data_inbuf_24 (
    .A(FrameData[24]),
    .X(FrameData_i[24])
);

my_buf data_inbuf_25 (
    .A(FrameData[25]),
    .X(FrameData_i[25])
);

my_buf data_inbuf_26 (
    .A(FrameData[26]),
    .X(FrameData_i[26])
);

my_buf data_inbuf_27 (
    .A(FrameData[27]),
    .X(FrameData_i[27])
);

my_buf data_inbuf_28 (
    .A(FrameData[28]),
    .X(FrameData_i[28])
);

my_buf data_inbuf_29 (
    .A(FrameData[29]),
    .X(FrameData_i[29])
);

my_buf data_inbuf_30 (
    .A(FrameData[30]),
    .X(FrameData_i[30])
);

my_buf data_inbuf_31 (
    .A(FrameData[31]),
    .X(FrameData_i[31])
);

my_buf data_outbuf_0 (
    .A(FrameData_O_i[0]),
    .X(FrameData_O[0])
);

my_buf data_outbuf_1 (
    .A(FrameData_O_i[1]),
    .X(FrameData_O[1])
);

my_buf data_outbuf_2 (
    .A(FrameData_O_i[2]),
    .X(FrameData_O[2])
);

my_buf data_outbuf_3 (
    .A(FrameData_O_i[3]),
    .X(FrameData_O[3])
);

my_buf data_outbuf_4 (
    .A(FrameData_O_i[4]),
    .X(FrameData_O[4])
);

my_buf data_outbuf_5 (
    .A(FrameData_O_i[5]),
    .X(FrameData_O[5])
);

my_buf data_outbuf_6 (
    .A(FrameData_O_i[6]),
    .X(FrameData_O[6])
);

my_buf data_outbuf_7 (
    .A(FrameData_O_i[7]),
    .X(FrameData_O[7])
);

my_buf data_outbuf_8 (
    .A(FrameData_O_i[8]),
    .X(FrameData_O[8])
);

my_buf data_outbuf_9 (
    .A(FrameData_O_i[9]),
    .X(FrameData_O[9])
);

my_buf data_outbuf_10 (
    .A(FrameData_O_i[10]),
    .X(FrameData_O[10])
);

my_buf data_outbuf_11 (
    .A(FrameData_O_i[11]),
    .X(FrameData_O[11])
);

my_buf data_outbuf_12 (
    .A(FrameData_O_i[12]),
    .X(FrameData_O[12])
);

my_buf data_outbuf_13 (
    .A(FrameData_O_i[13]),
    .X(FrameData_O[13])
);

my_buf data_outbuf_14 (
    .A(FrameData_O_i[14]),
    .X(FrameData_O[14])
);

my_buf data_outbuf_15 (
    .A(FrameData_O_i[15]),
    .X(FrameData_O[15])
);

my_buf data_outbuf_16 (
    .A(FrameData_O_i[16]),
    .X(FrameData_O[16])
);

my_buf data_outbuf_17 (
    .A(FrameData_O_i[17]),
    .X(FrameData_O[17])
);

my_buf data_outbuf_18 (
    .A(FrameData_O_i[18]),
    .X(FrameData_O[18])
);

my_buf data_outbuf_19 (
    .A(FrameData_O_i[19]),
    .X(FrameData_O[19])
);

my_buf data_outbuf_20 (
    .A(FrameData_O_i[20]),
    .X(FrameData_O[20])
);

my_buf data_outbuf_21 (
    .A(FrameData_O_i[21]),
    .X(FrameData_O[21])
);

my_buf data_outbuf_22 (
    .A(FrameData_O_i[22]),
    .X(FrameData_O[22])
);

my_buf data_outbuf_23 (
    .A(FrameData_O_i[23]),
    .X(FrameData_O[23])
);

my_buf data_outbuf_24 (
    .A(FrameData_O_i[24]),
    .X(FrameData_O[24])
);

my_buf data_outbuf_25 (
    .A(FrameData_O_i[25]),
    .X(FrameData_O[25])
);

my_buf data_outbuf_26 (
    .A(FrameData_O_i[26]),
    .X(FrameData_O[26])
);

my_buf data_outbuf_27 (
    .A(FrameData_O_i[27]),
    .X(FrameData_O[27])
);

my_buf data_outbuf_28 (
    .A(FrameData_O_i[28]),
    .X(FrameData_O[28])
);

my_buf data_outbuf_29 (
    .A(FrameData_O_i[29]),
    .X(FrameData_O[29])
);

my_buf data_outbuf_30 (
    .A(FrameData_O_i[30]),
    .X(FrameData_O[30])
);

my_buf data_outbuf_31 (
    .A(FrameData_O_i[31]),
    .X(FrameData_O[31])
);

assign FrameStrobe_O_i = FrameStrobe_i;

my_buf strobe_inbuf_0 (
    .A(FrameStrobe[0]),
    .X(FrameStrobe_i[0])
);

my_buf strobe_inbuf_1 (
    .A(FrameStrobe[1]),
    .X(FrameStrobe_i[1])
);

my_buf strobe_inbuf_2 (
    .A(FrameStrobe[2]),
    .X(FrameStrobe_i[2])
);

my_buf strobe_inbuf_3 (
    .A(FrameStrobe[3]),
    .X(FrameStrobe_i[3])
);

my_buf strobe_inbuf_4 (
    .A(FrameStrobe[4]),
    .X(FrameStrobe_i[4])
);

my_buf strobe_inbuf_5 (
    .A(FrameStrobe[5]),
    .X(FrameStrobe_i[5])
);

my_buf strobe_inbuf_6 (
    .A(FrameStrobe[6]),
    .X(FrameStrobe_i[6])
);

my_buf strobe_inbuf_7 (
    .A(FrameStrobe[7]),
    .X(FrameStrobe_i[7])
);

my_buf strobe_inbuf_8 (
    .A(FrameStrobe[8]),
    .X(FrameStrobe_i[8])
);

my_buf strobe_inbuf_9 (
    .A(FrameStrobe[9]),
    .X(FrameStrobe_i[9])
);

my_buf strobe_inbuf_10 (
    .A(FrameStrobe[10]),
    .X(FrameStrobe_i[10])
);

my_buf strobe_inbuf_11 (
    .A(FrameStrobe[11]),
    .X(FrameStrobe_i[11])
);

my_buf strobe_inbuf_12 (
    .A(FrameStrobe[12]),
    .X(FrameStrobe_i[12])
);

my_buf strobe_inbuf_13 (
    .A(FrameStrobe[13]),
    .X(FrameStrobe_i[13])
);

my_buf strobe_inbuf_14 (
    .A(FrameStrobe[14]),
    .X(FrameStrobe_i[14])
);

my_buf strobe_inbuf_15 (
    .A(FrameStrobe[15]),
    .X(FrameStrobe_i[15])
);

my_buf strobe_inbuf_16 (
    .A(FrameStrobe[16]),
    .X(FrameStrobe_i[16])
);

my_buf strobe_inbuf_17 (
    .A(FrameStrobe[17]),
    .X(FrameStrobe_i[17])
);

my_buf strobe_inbuf_18 (
    .A(FrameStrobe[18]),
    .X(FrameStrobe_i[18])
);

my_buf strobe_inbuf_19 (
    .A(FrameStrobe[19]),
    .X(FrameStrobe_i[19])
);

my_buf strobe_outbuf_0 (
    .A(FrameStrobe_O_i[0]),
    .X(FrameStrobe_O[0])
);

my_buf strobe_outbuf_1 (
    .A(FrameStrobe_O_i[1]),
    .X(FrameStrobe_O[1])
);

my_buf strobe_outbuf_2 (
    .A(FrameStrobe_O_i[2]),
    .X(FrameStrobe_O[2])
);

my_buf strobe_outbuf_3 (
    .A(FrameStrobe_O_i[3]),
    .X(FrameStrobe_O[3])
);

my_buf strobe_outbuf_4 (
    .A(FrameStrobe_O_i[4]),
    .X(FrameStrobe_O[4])
);

my_buf strobe_outbuf_5 (
    .A(FrameStrobe_O_i[5]),
    .X(FrameStrobe_O[5])
);

my_buf strobe_outbuf_6 (
    .A(FrameStrobe_O_i[6]),
    .X(FrameStrobe_O[6])
);

my_buf strobe_outbuf_7 (
    .A(FrameStrobe_O_i[7]),
    .X(FrameStrobe_O[7])
);

my_buf strobe_outbuf_8 (
    .A(FrameStrobe_O_i[8]),
    .X(FrameStrobe_O[8])
);

my_buf strobe_outbuf_9 (
    .A(FrameStrobe_O_i[9]),
    .X(FrameStrobe_O[9])
);

my_buf strobe_outbuf_10 (
    .A(FrameStrobe_O_i[10]),
    .X(FrameStrobe_O[10])
);

my_buf strobe_outbuf_11 (
    .A(FrameStrobe_O_i[11]),
    .X(FrameStrobe_O[11])
);

my_buf strobe_outbuf_12 (
    .A(FrameStrobe_O_i[12]),
    .X(FrameStrobe_O[12])
);

my_buf strobe_outbuf_13 (
    .A(FrameStrobe_O_i[13]),
    .X(FrameStrobe_O[13])
);

my_buf strobe_outbuf_14 (
    .A(FrameStrobe_O_i[14]),
    .X(FrameStrobe_O[14])
);

my_buf strobe_outbuf_15 (
    .A(FrameStrobe_O_i[15]),
    .X(FrameStrobe_O[15])
);

my_buf strobe_outbuf_16 (
    .A(FrameStrobe_O_i[16]),
    .X(FrameStrobe_O[16])
);

my_buf strobe_outbuf_17 (
    .A(FrameStrobe_O_i[17]),
    .X(FrameStrobe_O[17])
);

my_buf strobe_outbuf_18 (
    .A(FrameStrobe_O_i[18]),
    .X(FrameStrobe_O[18])
);

my_buf strobe_outbuf_19 (
    .A(FrameStrobe_O_i[19]),
    .X(FrameStrobe_O[19])
);


 //configuration storage latches
E_BRAM_bot_ConfigMem
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Emulate_Bitstream)
    )
`endif
    Inst_E_BRAM_bot_ConfigMem
    (
    .FrameData(FrameData),
    .FrameStrobe(FrameStrobe),
    .ConfigBits(ConfigBits),
    .ConfigBits_N(ConfigBits_N)
);


 //BEL component instantiations
ICS55_SRAM_512x32_1RW Inst_ICS55_SRAM_512x32_1RW (
    .CLK(CLK),
    .ADDR({ADDR9, ADDR8, ADDR7, ADDR6, ADDR5, ADDR4, ADDR3, ADDR2, ADDR1, ADDR0}),
    .DIN({DIN31, DIN30, DIN29, DIN28, DIN27, DIN26, DIN25, DIN24, DIN23, DIN22, DIN21, DIN20, DIN19, DIN18, DIN17, DIN16, DIN15, DIN14, DIN13, DIN12, DIN11, DIN10, DIN9, DIN8, DIN7, DIN6, DIN5, DIN4, DIN3, DIN2, DIN1, DIN0}),
    .BM({BM31, BM30, BM29, BM28, BM27, BM26, BM25, BM24, BM23, BM22, BM21, BM20, BM19, BM18, BM17, BM16, BM15, BM14, BM13, BM12, BM11, BM10, BM9, BM8, BM7, BM6, BM5, BM4, BM3, BM2, BM1, BM0}),
    .WEN(WEN),
    .MEN(MEN),
    .REN(REN),
    .DOUT({DOUT31, DOUT30, DOUT29, DOUT28, DOUT27, DOUT26, DOUT25, DOUT24, DOUT23, DOUT22, DOUT21, DOUT20, DOUT19, DOUT18, DOUT17, DOUT16, DOUT15, DOUT14, DOUT13, DOUT12, DOUT11, DOUT10, DOUT9, DOUT8, DOUT7, DOUT6, DOUT5, DOUT4, DOUT3, DOUT2, DOUT1, DOUT0}),
    .CONFIGURED_top(CONFIGURED_top)
);

E_BRAM_bot_switch_matrix Inst_E_BRAM_bot_switch_matrix (
    .N_GBUF_END0(N_GBUF_END[0]),
    .N_GBUF_END1(N_GBUF_END[1]),
    .N_GBUF_END2(N_GBUF_END[2]),
    .N_GBUF_END3(N_GBUF_END[3]),
    .E1END0(E1END[0]),
    .E1END1(E1END[1]),
    .E1END2(E1END[2]),
    .E1END3(E1END[3]),
    .E2MID0(E2MID[0]),
    .E2MID1(E2MID[1]),
    .E2MID2(E2MID[2]),
    .E2MID3(E2MID[3]),
    .E2MID4(E2MID[4]),
    .E2MID5(E2MID[5]),
    .E2MID6(E2MID[6]),
    .E2MID7(E2MID[7]),
    .E2END0(E2END[0]),
    .E2END1(E2END[1]),
    .E2END2(E2END[2]),
    .E2END3(E2END[3]),
    .E2END4(E2END[4]),
    .E2END5(E2END[5]),
    .E2END6(E2END[6]),
    .E2END7(E2END[7]),
    .EE4END0(EE4END[0]),
    .EE4END1(EE4END[1]),
    .EE4END2(EE4END[2]),
    .EE4END3(EE4END[3]),
    .EE4END4(EE4END[4]),
    .EE4END5(EE4END[5]),
    .EE4END6(EE4END[6]),
    .EE4END7(EE4END[7]),
    .EE4END8(EE4END[8]),
    .EE4END9(EE4END[9]),
    .EE4END10(EE4END[10]),
    .EE4END11(EE4END[11]),
    .EE4END12(EE4END[12]),
    .EE4END13(EE4END[13]),
    .EE4END14(EE4END[14]),
    .EE4END15(EE4END[15]),
    .E6END0(E6END[0]),
    .E6END1(E6END[1]),
    .E6END2(E6END[2]),
    .E6END3(E6END[3]),
    .E6END4(E6END[4]),
    .E6END5(E6END[5]),
    .E6END6(E6END[6]),
    .E6END7(E6END[7]),
    .E6END8(E6END[8]),
    .E6END9(E6END[9]),
    .E6END10(E6END[10]),
    .E6END11(E6END[11]),
    .top2bot_DIN0(top2bot_DIN[0]),
    .top2bot_DIN1(top2bot_DIN[1]),
    .top2bot_DIN2(top2bot_DIN[2]),
    .top2bot_DIN3(top2bot_DIN[3]),
    .top2bot_DIN4(top2bot_DIN[4]),
    .top2bot_DIN5(top2bot_DIN[5]),
    .top2bot_DIN6(top2bot_DIN[6]),
    .top2bot_DIN7(top2bot_DIN[7]),
    .top2bot_DIN8(top2bot_DIN[8]),
    .top2bot_DIN9(top2bot_DIN[9]),
    .top2bot_DIN10(top2bot_DIN[10]),
    .top2bot_DIN11(top2bot_DIN[11]),
    .top2bot_DIN12(top2bot_DIN[12]),
    .top2bot_DIN13(top2bot_DIN[13]),
    .top2bot_DIN14(top2bot_DIN[14]),
    .top2bot_DIN15(top2bot_DIN[15]),
    .top2bot_BM0(top2bot_BM[0]),
    .top2bot_BM1(top2bot_BM[1]),
    .top2bot_BM2(top2bot_BM[2]),
    .top2bot_BM3(top2bot_BM[3]),
    .top2bot_BM4(top2bot_BM[4]),
    .top2bot_BM5(top2bot_BM[5]),
    .top2bot_BM6(top2bot_BM[6]),
    .top2bot_BM7(top2bot_BM[7]),
    .top2bot_BM8(top2bot_BM[8]),
    .top2bot_BM9(top2bot_BM[9]),
    .top2bot_BM10(top2bot_BM[10]),
    .top2bot_BM11(top2bot_BM[11]),
    .top2bot_BM12(top2bot_BM[12]),
    .top2bot_BM13(top2bot_BM[13]),
    .top2bot_BM14(top2bot_BM[14]),
    .top2bot_BM15(top2bot_BM[15]),
    .top2bot_ADDR0(top2bot_ADDR[0]),
    .top2bot_ADDR1(top2bot_ADDR[1]),
    .top2bot_ADDR2(top2bot_ADDR[2]),
    .top2bot_ADDR3(top2bot_ADDR[3]),
    .top2bot_ADDR4(top2bot_ADDR[4]),
    .DOUT0(DOUT0),
    .DOUT1(DOUT1),
    .DOUT2(DOUT2),
    .DOUT3(DOUT3),
    .DOUT4(DOUT4),
    .DOUT5(DOUT5),
    .DOUT6(DOUT6),
    .DOUT7(DOUT7),
    .DOUT8(DOUT8),
    .DOUT9(DOUT9),
    .DOUT10(DOUT10),
    .DOUT11(DOUT11),
    .DOUT12(DOUT12),
    .DOUT13(DOUT13),
    .DOUT14(DOUT14),
    .DOUT15(DOUT15),
    .DOUT16(DOUT16),
    .DOUT17(DOUT17),
    .DOUT18(DOUT18),
    .DOUT19(DOUT19),
    .DOUT20(DOUT20),
    .DOUT21(DOUT21),
    .DOUT22(DOUT22),
    .DOUT23(DOUT23),
    .DOUT24(DOUT24),
    .DOUT25(DOUT25),
    .DOUT26(DOUT26),
    .DOUT27(DOUT27),
    .DOUT28(DOUT28),
    .DOUT29(DOUT29),
    .DOUT30(DOUT30),
    .DOUT31(DOUT31),
    .N_GBUF_BEG0(N_GBUF_BEG[0]),
    .N_GBUF_BEG1(N_GBUF_BEG[1]),
    .N_GBUF_BEG2(N_GBUF_BEG[2]),
    .N_GBUF_BEG3(N_GBUF_BEG[3]),
    .W1BEG0(W1BEG[0]),
    .W1BEG1(W1BEG[1]),
    .W1BEG2(W1BEG[2]),
    .W1BEG3(W1BEG[3]),
    .W2BEG0(W2BEG[0]),
    .W2BEG1(W2BEG[1]),
    .W2BEG2(W2BEG[2]),
    .W2BEG3(W2BEG[3]),
    .W2BEG4(W2BEG[4]),
    .W2BEG5(W2BEG[5]),
    .W2BEG6(W2BEG[6]),
    .W2BEG7(W2BEG[7]),
    .W2BEGb0(W2BEGb[0]),
    .W2BEGb1(W2BEGb[1]),
    .W2BEGb2(W2BEGb[2]),
    .W2BEGb3(W2BEGb[3]),
    .W2BEGb4(W2BEGb[4]),
    .W2BEGb5(W2BEGb[5]),
    .W2BEGb6(W2BEGb[6]),
    .W2BEGb7(W2BEGb[7]),
    .WW4BEG0(WW4BEG[0]),
    .WW4BEG1(WW4BEG[1]),
    .WW4BEG2(WW4BEG[2]),
    .WW4BEG3(WW4BEG[3]),
    .WW4BEG4(WW4BEG[4]),
    .WW4BEG5(WW4BEG[5]),
    .WW4BEG6(WW4BEG[6]),
    .WW4BEG7(WW4BEG[7]),
    .WW4BEG8(WW4BEG[8]),
    .WW4BEG9(WW4BEG[9]),
    .WW4BEG10(WW4BEG[10]),
    .WW4BEG11(WW4BEG[11]),
    .WW4BEG12(WW4BEG[12]),
    .WW4BEG13(WW4BEG[13]),
    .WW4BEG14(WW4BEG[14]),
    .WW4BEG15(WW4BEG[15]),
    .W6BEG0(W6BEG[0]),
    .W6BEG1(W6BEG[1]),
    .W6BEG2(W6BEG[2]),
    .W6BEG3(W6BEG[3]),
    .W6BEG4(W6BEG[4]),
    .W6BEG5(W6BEG[5]),
    .W6BEG6(W6BEG[6]),
    .W6BEG7(W6BEG[7]),
    .W6BEG8(W6BEG[8]),
    .W6BEG9(W6BEG[9]),
    .W6BEG10(W6BEG[10]),
    .W6BEG11(W6BEG[11]),
    .bot2top_DOUT0(bot2top_DOUT[0]),
    .bot2top_DOUT1(bot2top_DOUT[1]),
    .bot2top_DOUT2(bot2top_DOUT[2]),
    .bot2top_DOUT3(bot2top_DOUT[3]),
    .bot2top_DOUT4(bot2top_DOUT[4]),
    .bot2top_DOUT5(bot2top_DOUT[5]),
    .bot2top_DOUT6(bot2top_DOUT[6]),
    .bot2top_DOUT7(bot2top_DOUT[7]),
    .bot2top_DOUT8(bot2top_DOUT[8]),
    .bot2top_DOUT9(bot2top_DOUT[9]),
    .bot2top_DOUT10(bot2top_DOUT[10]),
    .bot2top_DOUT11(bot2top_DOUT[11]),
    .bot2top_DOUT12(bot2top_DOUT[12]),
    .bot2top_DOUT13(bot2top_DOUT[13]),
    .bot2top_DOUT14(bot2top_DOUT[14]),
    .bot2top_DOUT15(bot2top_DOUT[15]),
    .CLK(CLK),
    .ADDR0(ADDR0),
    .ADDR1(ADDR1),
    .ADDR2(ADDR2),
    .ADDR3(ADDR3),
    .ADDR4(ADDR4),
    .ADDR5(ADDR5),
    .ADDR6(ADDR6),
    .ADDR7(ADDR7),
    .ADDR8(ADDR8),
    .ADDR9(ADDR9),
    .DIN0(DIN0),
    .DIN1(DIN1),
    .DIN2(DIN2),
    .DIN3(DIN3),
    .DIN4(DIN4),
    .DIN5(DIN5),
    .DIN6(DIN6),
    .DIN7(DIN7),
    .DIN8(DIN8),
    .DIN9(DIN9),
    .DIN10(DIN10),
    .DIN11(DIN11),
    .DIN12(DIN12),
    .DIN13(DIN13),
    .DIN14(DIN14),
    .DIN15(DIN15),
    .DIN16(DIN16),
    .DIN17(DIN17),
    .DIN18(DIN18),
    .DIN19(DIN19),
    .DIN20(DIN20),
    .DIN21(DIN21),
    .DIN22(DIN22),
    .DIN23(DIN23),
    .DIN24(DIN24),
    .DIN25(DIN25),
    .DIN26(DIN26),
    .DIN27(DIN27),
    .DIN28(DIN28),
    .DIN29(DIN29),
    .DIN30(DIN30),
    .DIN31(DIN31),
    .BM0(BM0),
    .BM1(BM1),
    .BM2(BM2),
    .BM3(BM3),
    .BM4(BM4),
    .BM5(BM5),
    .BM6(BM6),
    .BM7(BM7),
    .BM8(BM8),
    .BM9(BM9),
    .BM10(BM10),
    .BM11(BM11),
    .BM12(BM12),
    .BM13(BM13),
    .BM14(BM14),
    .BM15(BM15),
    .BM16(BM16),
    .BM17(BM17),
    .BM18(BM18),
    .BM19(BM19),
    .BM20(BM20),
    .BM21(BM21),
    .BM22(BM22),
    .BM23(BM23),
    .BM24(BM24),
    .BM25(BM25),
    .BM26(BM26),
    .BM27(BM27),
    .BM28(BM28),
    .BM29(BM29),
    .BM30(BM30),
    .BM31(BM31),
    .WEN(WEN),
    .MEN(MEN),
    .REN(REN),
    .ConfigBits(ConfigBits[172-1:0]),
    .ConfigBits_N(ConfigBits_N[172-1:0])
);

endmodule