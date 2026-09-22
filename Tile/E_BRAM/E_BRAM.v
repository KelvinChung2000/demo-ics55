module E_BRAM
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
        output  [3:0] Tile_X0Y0_N_GBUF_BEG, //TilePort({N} OUTPUT N_GBUF_BEG[3:0])
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
    //Tile_X0Y1_Direction.NORTH
        input  [3:0] Tile_X0Y1_N_GBUF_END, //TilePort({S} INPUT N_GBUF_END[3:0])
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
        input  CONFIGURED_top,
        output  [MaxFramesPerCol-1:0] Tile_X0Y0_FrameStrobe_O, //CONFIG_PORT
        input  [FrameBitsPerRow-1:0] Tile_X0Y0_FrameData, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] Tile_X0Y0_FrameData_O, //CONFIG_PORT
        input  [FrameBitsPerRow-1:0] Tile_X0Y1_FrameData, //CONFIG_PORT
        input  [MaxFramesPerCol-1:0] Tile_X0Y1_FrameStrobe, //CONFIG_PORT
        output  [FrameBitsPerRow-1:0] Tile_X0Y1_FrameData_O //CONFIG_PORT
);

 //signal declarations
 //Tile_X0Y0_Direction.NORTH
    wire[15:0] Tile_X0Y0_top2bot_DIN; //TilePort({S} OUTPUT top2bot_DIN[15:0])
    wire[15:0] Tile_X0Y0_top2bot_BM; //TilePort({S} OUTPUT top2bot_BM[15:0])
    wire[4:0] Tile_X0Y0_top2bot_ADDR; //TilePort({S} OUTPUT top2bot_ADDR[4:0])
 //Tile_X0Y1_Direction.NORTH
    wire[3:0] Tile_X0Y1_N_GBUF_BEG; //TilePort({N} OUTPUT N_GBUF_BEG[3:0])
    wire[15:0] Tile_X0Y1_bot2top_DOUT; //TilePort({N} OUTPUT bot2top_DOUT[15:0])
    wire[MaxFramesPerCol-1:0] Tile_X0Y1_FrameStrobe_O;

E_BRAM_top
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Tile_X0Y0_Emulate_Bitstream)
    )
`endif
    Tile_X0Y0_E_BRAM_top
    (
    .N_GBUF_END(Tile_X0Y1_N_GBUF_BEG),
    .bot2top_DOUT(Tile_X0Y1_bot2top_DOUT),
    .E1END(Tile_X0Y0_E1END),
    .E2MID(Tile_X0Y0_E2MID),
    .E2END(Tile_X0Y0_E2END),
    .EE4END(Tile_X0Y0_EE4END),
    .E6END(Tile_X0Y0_E6END),
    .N_GBUF_BEG(Tile_X0Y0_N_GBUF_BEG),
    .top2bot_DIN(Tile_X0Y0_top2bot_DIN),
    .top2bot_BM(Tile_X0Y0_top2bot_BM),
    .top2bot_ADDR(Tile_X0Y0_top2bot_ADDR),
    .W1BEG(Tile_X0Y0_W1BEG),
    .W2BEG(Tile_X0Y0_W2BEG),
    .W2BEGb(Tile_X0Y0_W2BEGb),
    .WW4BEG(Tile_X0Y0_WW4BEG),
    .W6BEG(Tile_X0Y0_W6BEG),
    .FrameData(Tile_X0Y0_FrameData),
    .FrameData_O(Tile_X0Y0_FrameData_O),
    .FrameStrobe(Tile_X0Y1_FrameStrobe_O),
    .FrameStrobe_O(Tile_X0Y0_FrameStrobe_O)
);

E_BRAM_bot
`ifdef EMULATION
    #(
    .Emulate_Bitstream(Tile_X0Y1_Emulate_Bitstream)
    )
`endif
    Tile_X0Y1_E_BRAM_bot
    (
    .N_GBUF_END(Tile_X0Y1_N_GBUF_END),
    .E1END(Tile_X0Y1_E1END),
    .E2MID(Tile_X0Y1_E2MID),
    .E2END(Tile_X0Y1_E2END),
    .EE4END(Tile_X0Y1_EE4END),
    .E6END(Tile_X0Y1_E6END),
    .top2bot_DIN(Tile_X0Y0_top2bot_DIN),
    .top2bot_BM(Tile_X0Y0_top2bot_BM),
    .top2bot_ADDR(Tile_X0Y0_top2bot_ADDR),
    .N_GBUF_BEG(Tile_X0Y1_N_GBUF_BEG),
    .bot2top_DOUT(Tile_X0Y1_bot2top_DOUT),
    .W1BEG(Tile_X0Y1_W1BEG),
    .W2BEG(Tile_X0Y1_W2BEG),
    .W2BEGb(Tile_X0Y1_W2BEGb),
    .WW4BEG(Tile_X0Y1_WW4BEG),
    .W6BEG(Tile_X0Y1_W6BEG),
    .CONFIGURED_top(CONFIGURED_top),
    .FrameData(Tile_X0Y1_FrameData),
    .FrameData_O(Tile_X0Y1_FrameData_O),
    .FrameStrobe(Tile_X0Y1_FrameStrobe),
    .FrameStrobe_O(Tile_X0Y1_FrameStrobe_O)
);

endmodule