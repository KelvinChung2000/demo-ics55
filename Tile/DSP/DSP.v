module DSP
    #(
`ifdef EMULATION
        parameter [639:0] Tile_X0Y0_Emulate_Bitstream=640'b0,
        parameter [639:0] Tile_X0Y1_Emulate_Bitstream=640'b0,
`endif
        parameter MaxFramesPerCol=20,
        parameter FrameBitsPerRow=32
    )
    (
    //Tile_X0Y0_Direction.NORTH
        output  [3:0] Tile_X0Y0_N1BEG, //TilePort({N} OUTPUT N1BEG[3:0])
        output  [7:0] Tile_X0Y0_N2BEG, //TilePort({N} OUTPUT N2BEG[7:0])
        output  [7:0] Tile_X0Y0_N2BEGb, //TilePort({N} OUTPUT N2BEGb[7:0])
        output  [15:0] Tile_X0Y0_N4BEG, //TilePort({N} OUTPUT N4BEG[3:0])
        output  [15:0] Tile_X0Y0_NN4BEG, //TilePort({N} OUTPUT NN4BEG[3:0])
        input  [3:0] Tile_X0Y0_S1END, //TilePort({N} INPUT S1END[3:0])
        input  [7:0] Tile_X0Y0_S2MID, //TilePort({N} INPUT S2MID[7:0])
        input  [7:0] Tile_X0Y0_S2END, //TilePort({N} INPUT S2END[7:0])
        input  [15:0] Tile_X0Y0_S4END, //TilePort({N} INPUT S4END[3:0])
        input  [15:0] Tile_X0Y0_SS4END, //TilePort({N} INPUT SS4END[3:0])
    //Tile_X0Y0_Direction.EAST
        output  [3:0] Tile_X0Y0_E1BEG, //TilePort({E} OUTPUT E1BEG[3:0])
        output  [7:0] Tile_X0Y0_E2BEG, //TilePort({E} OUTPUT E2BEG[7:0])
        output  [7:0] Tile_X0Y0_E2BEGb, //TilePort({E} OUTPUT E2BEGb[7:0])
        output  [15:0] Tile_X0Y0_EE4BEG, //TilePort({E} OUTPUT EE4BEG[3:0])
        output  [11:0] Tile_X0Y0_E6BEG, //TilePort({E} OUTPUT E6BEG[1:0])
        input  [3:0] Tile_X0Y0_W1END, //TilePort({E} INPUT W1END[3:0])
        input  [7:0] Tile_X0Y0_W2MID, //TilePort({E} INPUT W2MID[7:0])
        input  [7:0] Tile_X0Y0_W2END, //TilePort({E} INPUT W2END[7:0])
        input  [15:0] Tile_X0Y0_WW4END, //TilePort({E} INPUT WW4END[3:0])
        input  [11:0] Tile_X0Y0_W6END, //TilePort({E} INPUT W6END[1:0])
    //Tile_X0Y0_Direction.EAST
        input  [3:0] Tile_X0Y0_E1END, //TilePort({W} INPUT E1END[3:0])
        input  [7:0] Tile_X0Y0_E2MID, //TilePort({W} INPUT E2MID[7:0])
        input  [7:0] Tile_X0Y0_E2END, //TilePort({W} INPUT E2END[7:0])
        input  [15:0] Tile_X0Y0_EE4END, //TilePort({W} INPUT EE4END[3:0])
        input  [11:0] Tile_X0Y0_E6END, //TilePort({W} INPUT E6END[1:0])
        output  [3:0] Tile_X0Y0_W1BEG, //TilePort({W} OUTPUT W1BEG[3:0])
        output  [7:0] Tile_X0Y0_W2BEG, //TilePort({W} OUTPUT W2BEG[7:0])
        output  [7:0] Tile_X0Y0_W2BEGb, //TilePort({W} OUTPUT W2BEGb[7:0])
        output  [15:0] Tile_X0Y0_WW4BEG, //TilePort({W} OUTPUT WW4BEG[3:0])
        output  [11:0] Tile_X0Y0_W6BEG, //TilePort({W} OUTPUT W6BEG[1:0])
    //Tile_X0Y1_Direction.EAST
        output  [3:0] Tile_X0Y1_E1BEG, //TilePort({E} OUTPUT E1BEG[3:0])
        output  [7:0] Tile_X0Y1_E2BEG, //TilePort({E} OUTPUT E2BEG[7:0])
        output  [7:0] Tile_X0Y1_E2BEGb, //TilePort({E} OUTPUT E2BEGb[7:0])
        output  [15:0] Tile_X0Y1_EE4BEG, //TilePort({E} OUTPUT EE4BEG[3:0])
        output  [11:0] Tile_X0Y1_E6BEG, //TilePort({E} OUTPUT E6BEG[1:0])
        input  [3:0] Tile_X0Y1_W1END, //TilePort({E} INPUT W1END[3:0])
        input  [7:0] Tile_X0Y1_W2MID, //TilePort({E} INPUT W2MID[7:0])
        input  [7:0] Tile_X0Y1_W2END, //TilePort({E} INPUT W2END[7:0])
        input  [15:0] Tile_X0Y1_WW4END, //TilePort({E} INPUT WW4END[3:0])
        input  [11:0] Tile_X0Y1_W6END, //TilePort({E} INPUT W6END[1:0])
    //Tile_X0Y1_Direction.NORTH
        input  [3:0] Tile_X0Y1_N1END, //TilePort({S} INPUT N1END[3:0])
        input  [7:0] Tile_X0Y1_N2MID, //TilePort({S} INPUT N2MID[7:0])
        input  [7:0] Tile_X0Y1_N2END, //TilePort({S} INPUT N2END[7:0])
        input  [15:0] Tile_X0Y1_N4END, //TilePort({S} INPUT N4END[3:0])
        input  [15:0] Tile_X0Y1_NN4END, //TilePort({S} INPUT NN4END[3:0])
        output  [3:0] Tile_X0Y1_S1BEG, //TilePort({S} OUTPUT S1BEG[3:0])
        output  [7:0] Tile_X0Y1_S2BEG, //TilePort({S} OUTPUT S2BEG[7:0])
        output  [7:0] Tile_X0Y1_S2BEGb, //TilePort({S} OUTPUT S2BEGb[7:0])
        output  [15:0] Tile_X0Y1_S4BEG, //TilePort({S} OUTPUT S4BEG[3:0])
        output  [15:0] Tile_X0Y1_SS4BEG, //TilePort({S} OUTPUT SS4BEG[3:0])
    //Tile_X0Y1_Direction.EAST
        input  [3:0] Tile_X0Y1_E1END, //TilePort({W} INPUT E1END[3:0])
        input  [7:0] Tile_X0Y1_E2MID, //TilePort({W} INPUT E2MID[7:0])
        input  [7:0] Tile_X0Y1_E2END, //TilePort({W} INPUT E2END[7:0])
        input  [15:0] Tile_X0Y1_EE4END, //TilePort({W} INPUT EE4END[3:0])
        input  [11:0] Tile_X0Y1_E6END, //TilePort({W} INPUT E6END[1:0])
        output  [3:0] Tile_X0Y1_W1BEG, //TilePort({W} OUTPUT W1BEG[3:0])
        output  [7:0] Tile_X0Y1_W2BEG, //TilePort({W} OUTPUT W2BEG[7:0])
        output  [7:0] Tile_X0Y1_W2BEGb, //TilePort({W} OUTPUT W2BEGb[7:0])
        output  [15:0] Tile_X0Y1_WW4BEG, //TilePort({W} OUTPUT WW4BEG[3:0])
        output  [11:0] Tile_X0Y1_W6BEG, //TilePort({W} OUTPUT W6BEG[1:0])
    //Tile IO ports from BELs
        output  [MaxFramesPerCol-1:0] Tile_X0Y0_FrameStrobe_O, //CONFIG_PORT
        input  [FrameBitsPerRow-1:0] Tile_X0Y0_FrameData, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] Tile_X0Y0_FrameData_O, //CONFIG_PORT
        input  [FrameBitsPerRow-1:0] Tile_X0Y1_FrameData, //CONFIG_PORT
        input  [MaxFramesPerCol-1:0] Tile_X0Y1_FrameStrobe, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] Tile_X0Y1_FrameData_O, //CONFIG_PORT
        output  Tile_X0Y0_UserCLKo,
        input  Tile_X0Y1_UserCLK
);

 //signal declarations
 //Tile_X0Y0_Direction.NORTH
    wire[3:0] Tile_X0Y0_S1BEG; //TilePort({S} OUTPUT S1BEG[3:0])
    wire[7:0] Tile_X0Y0_S2BEG; //TilePort({S} OUTPUT S2BEG[7:0])
    wire[7:0] Tile_X0Y0_S2BEGb; //TilePort({S} OUTPUT S2BEGb[7:0])
    wire[15:0] Tile_X0Y0_S4BEG; //TilePort({S} OUTPUT S4BEG[3:0])
    wire[15:0] Tile_X0Y0_SS4BEG; //TilePort({S} OUTPUT SS4BEG[3:0])
    wire[17:0] Tile_X0Y0_top2bot; //TilePort({S} OUTPUT top2bot[17:0])
 //Tile_X0Y1_Direction.NORTH
    wire[3:0] Tile_X0Y1_N1BEG; //TilePort({N} OUTPUT N1BEG[3:0])
    wire[7:0] Tile_X0Y1_N2BEG; //TilePort({N} OUTPUT N2BEG[7:0])
    wire[7:0] Tile_X0Y1_N2BEGb; //TilePort({N} OUTPUT N2BEGb[7:0])
    wire[15:0] Tile_X0Y1_N4BEG; //TilePort({N} OUTPUT N4BEG[3:0])
    wire[15:0] Tile_X0Y1_NN4BEG; //TilePort({N} OUTPUT NN4BEG[3:0])
    wire[9:0] Tile_X0Y1_bot2top; //TilePort({N} OUTPUT bot2top[9:0])
    wire[MaxFramesPerCol-1:0] Tile_X0Y1_FrameStrobe_O;
    wire Tile_X0Y1_UserCLKo;

DSP_top
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Tile_X0Y0_Emulate_Bitstream)
    )
`endif
    Tile_X0Y0_DSP_top
    (
    .N1END(Tile_X0Y1_N1BEG),
    .N2MID(Tile_X0Y1_N2BEG),
    .N2END(Tile_X0Y1_N2BEGb),
    .N4END(Tile_X0Y1_N4BEG),
    .NN4END(Tile_X0Y1_NN4BEG),
    .bot2top(Tile_X0Y1_bot2top),
    .E1END(Tile_X0Y0_E1END),
    .E2MID(Tile_X0Y0_E2MID),
    .E2END(Tile_X0Y0_E2END),
    .EE4END(Tile_X0Y0_EE4END),
    .E6END(Tile_X0Y0_E6END),
    .S1END(Tile_X0Y0_S1END),
    .S2MID(Tile_X0Y0_S2MID),
    .S2END(Tile_X0Y0_S2END),
    .S4END(Tile_X0Y0_S4END),
    .SS4END(Tile_X0Y0_SS4END),
    .W1END(Tile_X0Y0_W1END),
    .W2MID(Tile_X0Y0_W2MID),
    .W2END(Tile_X0Y0_W2END),
    .WW4END(Tile_X0Y0_WW4END),
    .W6END(Tile_X0Y0_W6END),
    .N1BEG(Tile_X0Y0_N1BEG),
    .N2BEG(Tile_X0Y0_N2BEG),
    .N2BEGb(Tile_X0Y0_N2BEGb),
    .N4BEG(Tile_X0Y0_N4BEG),
    .NN4BEG(Tile_X0Y0_NN4BEG),
    .E1BEG(Tile_X0Y0_E1BEG),
    .E2BEG(Tile_X0Y0_E2BEG),
    .E2BEGb(Tile_X0Y0_E2BEGb),
    .EE4BEG(Tile_X0Y0_EE4BEG),
    .E6BEG(Tile_X0Y0_E6BEG),
    .S1BEG(Tile_X0Y0_S1BEG),
    .S2BEG(Tile_X0Y0_S2BEG),
    .S2BEGb(Tile_X0Y0_S2BEGb),
    .S4BEG(Tile_X0Y0_S4BEG),
    .SS4BEG(Tile_X0Y0_SS4BEG),
    .top2bot(Tile_X0Y0_top2bot),
    .W1BEG(Tile_X0Y0_W1BEG),
    .W2BEG(Tile_X0Y0_W2BEG),
    .W2BEGb(Tile_X0Y0_W2BEGb),
    .WW4BEG(Tile_X0Y0_WW4BEG),
    .W6BEG(Tile_X0Y0_W6BEG),
    .UserCLK(Tile_X0Y1_UserCLKo),
    .UserCLKo(Tile_X0Y0_UserCLKo),
    .FrameData(Tile_X0Y0_FrameData),
    .FrameData_O(Tile_X0Y0_FrameData_O),
    .FrameStrobe(Tile_X0Y1_FrameStrobe_O),
    .FrameStrobe_O(Tile_X0Y0_FrameStrobe_O)
);

DSP_bot
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Tile_X0Y1_Emulate_Bitstream)
    )
`endif
    Tile_X0Y1_DSP_bot
    (
    .N1END(Tile_X0Y1_N1END),
    .N2MID(Tile_X0Y1_N2MID),
    .N2END(Tile_X0Y1_N2END),
    .N4END(Tile_X0Y1_N4END),
    .NN4END(Tile_X0Y1_NN4END),
    .E1END(Tile_X0Y1_E1END),
    .E2MID(Tile_X0Y1_E2MID),
    .E2END(Tile_X0Y1_E2END),
    .EE4END(Tile_X0Y1_EE4END),
    .E6END(Tile_X0Y1_E6END),
    .S1END(Tile_X0Y0_S1BEG),
    .S2MID(Tile_X0Y0_S2BEG),
    .S2END(Tile_X0Y0_S2BEGb),
    .S4END(Tile_X0Y0_S4BEG),
    .SS4END(Tile_X0Y0_SS4BEG),
    .top2bot(Tile_X0Y0_top2bot),
    .W1END(Tile_X0Y1_W1END),
    .W2MID(Tile_X0Y1_W2MID),
    .W2END(Tile_X0Y1_W2END),
    .WW4END(Tile_X0Y1_WW4END),
    .W6END(Tile_X0Y1_W6END),
    .N1BEG(Tile_X0Y1_N1BEG),
    .N2BEG(Tile_X0Y1_N2BEG),
    .N2BEGb(Tile_X0Y1_N2BEGb),
    .N4BEG(Tile_X0Y1_N4BEG),
    .NN4BEG(Tile_X0Y1_NN4BEG),
    .bot2top(Tile_X0Y1_bot2top),
    .E1BEG(Tile_X0Y1_E1BEG),
    .E2BEG(Tile_X0Y1_E2BEG),
    .E2BEGb(Tile_X0Y1_E2BEGb),
    .EE4BEG(Tile_X0Y1_EE4BEG),
    .E6BEG(Tile_X0Y1_E6BEG),
    .S1BEG(Tile_X0Y1_S1BEG),
    .S2BEG(Tile_X0Y1_S2BEG),
    .S2BEGb(Tile_X0Y1_S2BEGb),
    .S4BEG(Tile_X0Y1_S4BEG),
    .SS4BEG(Tile_X0Y1_SS4BEG),
    .W1BEG(Tile_X0Y1_W1BEG),
    .W2BEG(Tile_X0Y1_W2BEG),
    .W2BEGb(Tile_X0Y1_W2BEGb),
    .WW4BEG(Tile_X0Y1_WW4BEG),
    .W6BEG(Tile_X0Y1_W6BEG),
    .UserCLK(Tile_X0Y1_UserCLK),
    .UserCLKo(Tile_X0Y1_UserCLKo),
    .FrameData(Tile_X0Y1_FrameData),
    .FrameData_O(Tile_X0Y1_FrameData_O),
    .FrameStrobe(Tile_X0Y1_FrameStrobe),
    .FrameStrobe_O(Tile_X0Y1_FrameStrobe_O)
);

endmodule