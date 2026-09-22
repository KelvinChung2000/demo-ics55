module eFPGA_top
    #(
        parameter include_eFPGA=1,
        parameter NumberOfRows=10,
        parameter NumberOfCols=11,
        parameter FrameBitsPerRow=32,
        parameter MaxFramesPerCol=20,
        parameter desync_flag=20,
        parameter FrameSelectWidth=5,
        parameter RowSelectWidth=5
    )
    (
        //External IO port
        output  [35:0] A_EN_top,
        output  [35:0] A_IN_top,
        input  [35:0] A_OUT_top,
        input  [0:0] SYS_RESET_RESET_top,
        //Config related ports
        input  CLK,
        input  resetn,
        input  SelfWriteStrobe,
        input  [31:0] SelfWriteData,
        input  Rx,
        output  ComActive,
        output  ReceiveLED,
        input  s_clk,
        input  s_data
);

 //Signal declarations
wire[(NumberOfRows*FrameBitsPerRow)-1:0] FrameRegister;
wire[(MaxFramesPerCol*NumberOfCols)-1:0] FrameSelect;
wire[(FrameBitsPerRow*(NumberOfRows+2))-1:0] FrameData;
wire[FrameBitsPerRow-1:0] FrameAddressRegister;
wire LongFrameStrobe;
wire[31:0] LocalWriteData;
wire LocalWriteStrobe;
wire[RowSelectWidth-1:0] RowSelect;
`ifndef EMULATION

eFPGA_Config
    #(
    .RowSelectWidth(RowSelectWidth),
    .NumberOfRows(NumberOfRows),
    .desync_flag(desync_flag),
    .FrameBitsPerRow(FrameBitsPerRow)
    )
    eFPGA_Config_inst
    (
    .CLK(CLK),
    .resetn(resetn),
    .Rx(Rx),
    .ComActive(ComActive),
    .ReceiveLED(ReceiveLED),
    .s_clk(s_clk),
    .s_data(s_data),
    .SelfWriteData(SelfWriteData),
    .SelfWriteStrobe(SelfWriteStrobe),
    .ConfigWriteData(LocalWriteData),
    .ConfigWriteStrobe(LocalWriteStrobe),
    .FrameAddressRegister(FrameAddressRegister),
    .LongFrameStrobe(LongFrameStrobe),
    .RowSelect(RowSelect)
);


Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(1)
    )
    inst_Frame_Data_Reg_0
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[0*FrameBitsPerRow+FrameBitsPerRow-1:0*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(2)
    )
    inst_Frame_Data_Reg_1
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[1*FrameBitsPerRow+FrameBitsPerRow-1:1*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(3)
    )
    inst_Frame_Data_Reg_2
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[2*FrameBitsPerRow+FrameBitsPerRow-1:2*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(4)
    )
    inst_Frame_Data_Reg_3
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[3*FrameBitsPerRow+FrameBitsPerRow-1:3*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(5)
    )
    inst_Frame_Data_Reg_4
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[4*FrameBitsPerRow+FrameBitsPerRow-1:4*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(6)
    )
    inst_Frame_Data_Reg_5
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[5*FrameBitsPerRow+FrameBitsPerRow-1:5*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(7)
    )
    inst_Frame_Data_Reg_6
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[6*FrameBitsPerRow+FrameBitsPerRow-1:6*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(8)
    )
    inst_Frame_Data_Reg_7
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[7*FrameBitsPerRow+FrameBitsPerRow-1:7*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(9)
    )
    inst_Frame_Data_Reg_8
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[8*FrameBitsPerRow+FrameBitsPerRow-1:8*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);

Frame_Data_Reg
    #(
    .FrameBitsPerRow(FrameBitsPerRow),
    .RowSelectWidth(RowSelectWidth),
    .Row(10)
    )
    inst_Frame_Data_Reg_9
    (
    .FrameData_I(LocalWriteData),
    .FrameData_O(FrameRegister[9*FrameBitsPerRow+FrameBitsPerRow-1:9*FrameBitsPerRow]),
    .RowSelect(RowSelect),
    .CLK(CLK)
);


Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(0)
    )
    inst_Frame_Select_0
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[0*MaxFramesPerCol+MaxFramesPerCol-1:0*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(1)
    )
    inst_Frame_Select_1
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[1*MaxFramesPerCol+MaxFramesPerCol-1:1*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(2)
    )
    inst_Frame_Select_2
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[2*MaxFramesPerCol+MaxFramesPerCol-1:2*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(3)
    )
    inst_Frame_Select_3
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[3*MaxFramesPerCol+MaxFramesPerCol-1:3*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(4)
    )
    inst_Frame_Select_4
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[4*MaxFramesPerCol+MaxFramesPerCol-1:4*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(5)
    )
    inst_Frame_Select_5
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[5*MaxFramesPerCol+MaxFramesPerCol-1:5*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(6)
    )
    inst_Frame_Select_6
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[6*MaxFramesPerCol+MaxFramesPerCol-1:6*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(7)
    )
    inst_Frame_Select_7
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[7*MaxFramesPerCol+MaxFramesPerCol-1:7*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(8)
    )
    inst_Frame_Select_8
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[8*MaxFramesPerCol+MaxFramesPerCol-1:8*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(9)
    )
    inst_Frame_Select_9
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[9*MaxFramesPerCol+MaxFramesPerCol-1:9*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);

Frame_Select
    #(
    .MaxFramesPerCol(MaxFramesPerCol),
    .FrameSelectWidth(FrameSelectWidth),
    .Col(10)
    )
    inst_Frame_Select_10
    (
    .FrameStrobe_I(FrameAddressRegister[MaxFramesPerCol-1:0]),
    .FrameStrobe_O(FrameSelect[10*MaxFramesPerCol+MaxFramesPerCol-1:10*MaxFramesPerCol]),
    .FrameSelect(FrameAddressRegister[FrameBitsPerRow-1:FrameBitsPerRow-FrameSelectWidth]),
    .FrameStrobe(LongFrameStrobe)
);


`endif
eFPGA eFPGA_inst (
    .Tile_X1Y11_A_EN_top(A_EN_top[0]),
    .Tile_X2Y11_A_EN_top(A_EN_top[1]),
    .Tile_X3Y11_A_EN_top(A_EN_top[2]),
    .Tile_X4Y11_A_EN_top(A_EN_top[3]),
    .Tile_X5Y11_A_EN_top(A_EN_top[4]),
    .Tile_X7Y11_A_EN_top(A_EN_top[5]),
    .Tile_X8Y11_A_EN_top(A_EN_top[6]),
    .Tile_X9Y11_A_EN_top(A_EN_top[7]),
    .Tile_X0Y10_A_EN_top(A_EN_top[8]),
    .Tile_X10Y10_A_EN_top(A_EN_top[9]),
    .Tile_X0Y9_A_EN_top(A_EN_top[10]),
    .Tile_X10Y9_A_EN_top(A_EN_top[11]),
    .Tile_X0Y8_A_EN_top(A_EN_top[12]),
    .Tile_X10Y8_A_EN_top(A_EN_top[13]),
    .Tile_X0Y7_A_EN_top(A_EN_top[14]),
    .Tile_X10Y7_A_EN_top(A_EN_top[15]),
    .Tile_X0Y6_A_EN_top(A_EN_top[16]),
    .Tile_X10Y6_A_EN_top(A_EN_top[17]),
    .Tile_X0Y5_A_EN_top(A_EN_top[18]),
    .Tile_X10Y5_A_EN_top(A_EN_top[19]),
    .Tile_X0Y4_A_EN_top(A_EN_top[20]),
    .Tile_X10Y4_A_EN_top(A_EN_top[21]),
    .Tile_X0Y3_A_EN_top(A_EN_top[22]),
    .Tile_X10Y3_A_EN_top(A_EN_top[23]),
    .Tile_X0Y2_A_EN_top(A_EN_top[24]),
    .Tile_X10Y2_A_EN_top(A_EN_top[25]),
    .Tile_X0Y1_A_EN_top(A_EN_top[26]),
    .Tile_X10Y1_A_EN_top(A_EN_top[27]),
    .Tile_X1Y0_A_EN_top(A_EN_top[28]),
    .Tile_X2Y0_A_EN_top(A_EN_top[29]),
    .Tile_X3Y0_A_EN_top(A_EN_top[30]),
    .Tile_X4Y0_A_EN_top(A_EN_top[31]),
    .Tile_X5Y0_A_EN_top(A_EN_top[32]),
    .Tile_X7Y0_A_EN_top(A_EN_top[33]),
    .Tile_X8Y0_A_EN_top(A_EN_top[34]),
    .Tile_X9Y0_A_EN_top(A_EN_top[35]),
    .Tile_X1Y11_A_IN_top(A_IN_top[0]),
    .Tile_X2Y11_A_IN_top(A_IN_top[1]),
    .Tile_X3Y11_A_IN_top(A_IN_top[2]),
    .Tile_X4Y11_A_IN_top(A_IN_top[3]),
    .Tile_X5Y11_A_IN_top(A_IN_top[4]),
    .Tile_X7Y11_A_IN_top(A_IN_top[5]),
    .Tile_X8Y11_A_IN_top(A_IN_top[6]),
    .Tile_X9Y11_A_IN_top(A_IN_top[7]),
    .Tile_X0Y10_A_IN_top(A_IN_top[8]),
    .Tile_X10Y10_A_IN_top(A_IN_top[9]),
    .Tile_X0Y9_A_IN_top(A_IN_top[10]),
    .Tile_X10Y9_A_IN_top(A_IN_top[11]),
    .Tile_X0Y8_A_IN_top(A_IN_top[12]),
    .Tile_X10Y8_A_IN_top(A_IN_top[13]),
    .Tile_X0Y7_A_IN_top(A_IN_top[14]),
    .Tile_X10Y7_A_IN_top(A_IN_top[15]),
    .Tile_X0Y6_A_IN_top(A_IN_top[16]),
    .Tile_X10Y6_A_IN_top(A_IN_top[17]),
    .Tile_X0Y5_A_IN_top(A_IN_top[18]),
    .Tile_X10Y5_A_IN_top(A_IN_top[19]),
    .Tile_X0Y4_A_IN_top(A_IN_top[20]),
    .Tile_X10Y4_A_IN_top(A_IN_top[21]),
    .Tile_X0Y3_A_IN_top(A_IN_top[22]),
    .Tile_X10Y3_A_IN_top(A_IN_top[23]),
    .Tile_X0Y2_A_IN_top(A_IN_top[24]),
    .Tile_X10Y2_A_IN_top(A_IN_top[25]),
    .Tile_X0Y1_A_IN_top(A_IN_top[26]),
    .Tile_X10Y1_A_IN_top(A_IN_top[27]),
    .Tile_X1Y0_A_IN_top(A_IN_top[28]),
    .Tile_X2Y0_A_IN_top(A_IN_top[29]),
    .Tile_X3Y0_A_IN_top(A_IN_top[30]),
    .Tile_X4Y0_A_IN_top(A_IN_top[31]),
    .Tile_X5Y0_A_IN_top(A_IN_top[32]),
    .Tile_X7Y0_A_IN_top(A_IN_top[33]),
    .Tile_X8Y0_A_IN_top(A_IN_top[34]),
    .Tile_X9Y0_A_IN_top(A_IN_top[35]),
    .Tile_X1Y11_A_OUT_top(A_OUT_top[0]),
    .Tile_X2Y11_A_OUT_top(A_OUT_top[1]),
    .Tile_X3Y11_A_OUT_top(A_OUT_top[2]),
    .Tile_X4Y11_A_OUT_top(A_OUT_top[3]),
    .Tile_X5Y11_A_OUT_top(A_OUT_top[4]),
    .Tile_X7Y11_A_OUT_top(A_OUT_top[5]),
    .Tile_X8Y11_A_OUT_top(A_OUT_top[6]),
    .Tile_X9Y11_A_OUT_top(A_OUT_top[7]),
    .Tile_X0Y10_A_OUT_top(A_OUT_top[8]),
    .Tile_X10Y10_A_OUT_top(A_OUT_top[9]),
    .Tile_X0Y9_A_OUT_top(A_OUT_top[10]),
    .Tile_X10Y9_A_OUT_top(A_OUT_top[11]),
    .Tile_X0Y8_A_OUT_top(A_OUT_top[12]),
    .Tile_X10Y8_A_OUT_top(A_OUT_top[13]),
    .Tile_X0Y7_A_OUT_top(A_OUT_top[14]),
    .Tile_X10Y7_A_OUT_top(A_OUT_top[15]),
    .Tile_X0Y6_A_OUT_top(A_OUT_top[16]),
    .Tile_X10Y6_A_OUT_top(A_OUT_top[17]),
    .Tile_X0Y5_A_OUT_top(A_OUT_top[18]),
    .Tile_X10Y5_A_OUT_top(A_OUT_top[19]),
    .Tile_X0Y4_A_OUT_top(A_OUT_top[20]),
    .Tile_X10Y4_A_OUT_top(A_OUT_top[21]),
    .Tile_X0Y3_A_OUT_top(A_OUT_top[22]),
    .Tile_X10Y3_A_OUT_top(A_OUT_top[23]),
    .Tile_X0Y2_A_OUT_top(A_OUT_top[24]),
    .Tile_X10Y2_A_OUT_top(A_OUT_top[25]),
    .Tile_X0Y1_A_OUT_top(A_OUT_top[26]),
    .Tile_X10Y1_A_OUT_top(A_OUT_top[27]),
    .Tile_X1Y0_A_OUT_top(A_OUT_top[28]),
    .Tile_X2Y0_A_OUT_top(A_OUT_top[29]),
    .Tile_X3Y0_A_OUT_top(A_OUT_top[30]),
    .Tile_X4Y0_A_OUT_top(A_OUT_top[31]),
    .Tile_X5Y0_A_OUT_top(A_OUT_top[32]),
    .Tile_X7Y0_A_OUT_top(A_OUT_top[33]),
    .Tile_X8Y0_A_OUT_top(A_OUT_top[34]),
    .Tile_X9Y0_A_OUT_top(A_OUT_top[35]),
    .Tile_X0Y11_SYS_RESET_RESET_top(SYS_RESET_RESET_top[0]),
    .UserCLK(CLK),
    .FrameData(FrameData),
    .FrameStrobe(FrameSelect)
);


assign FrameData = {32'h12345678,FrameRegister,32'h12345678};
endmodule