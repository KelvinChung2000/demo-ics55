// Written by flow/topwrap.py from fabrics/nobram/Fabric/eFPGA.v; regenerate with `flow gen-top`.
`default_nettype none

module eFPGA_top (
    output wire [9:0] A_EN_top,
    output wire [9:0] A_IN_top,
    input wire [9:0] A_OUT_top,
    input wire USER_CLK,
    input wire USER_RESET,
    // Configuration clock and reset. The fabric's own clock arrives on a pad
    // through the global buffers, since the grid sets DisableUserCLK.
    input wire CLK,
    input wire resetn,
    input wire Rx,
    output wire ComActive,
    output wire ReceiveLED,
    input wire spi_sck,
    input wire spi_cs_n,
    input wire spi_mosi,
    output wire ConfigBusy,
    output wire Configured
);
    localparam integer FRAME_BITS_PER_ROW = 32;
    localparam integer MAX_FRAMES_PER_COL = 20;
    localparam integer NUM_ROWS = 12;
    localparam integer NUM_COLUMNS = 13;

    wire [31:0] bitstream_data;
    wire bitstream_valid;
    wire configured;
    wire [FRAME_BITS_PER_ROW*NUM_ROWS-1:0] frame_data;
    wire [MAX_FRAMES_PER_COL*NUM_COLUMNS-1:0] frame_strobe;

    assign Configured = configured;

    config_frontend frontend (
        .CLK(CLK),
        .resetn(resetn),
        .Rx(Rx),
        .ComActive(ComActive),
        .ReceiveLED(ReceiveLED),
        .s_clk(1'b0),
        .s_data(1'b0),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .SelfWriteData(32'b0),
        .SelfWriteStrobe(1'b0),
        .bitstream_data(bitstream_data),
        .bitstream_valid(bitstream_valid)
    );

    fabric_config #(
        .FRAME_BITS_PER_ROW(FRAME_BITS_PER_ROW),
        .MAX_FRAMES_PER_COL(MAX_FRAMES_PER_COL),
        .FRAME_SELECT_WIDTH(5),
        .FABRIC_NUM_COLUMNS(NUM_COLUMNS),
        .FABRIC_NUM_ROWS(NUM_ROWS)
    ) loader (
        .clk_i(CLK),
        .rst_ni(resetn),
        .bitstream_data_i(bitstream_data),
        .bitstream_valid_i(bitstream_valid),
        .busy_o(ConfigBusy),
        .configured_o(configured),
        .frame_data_o(frame_data),
        .frame_strobe_o(frame_strobe)
    );

    eFPGA #(
        .MaxFramesPerCol(MAX_FRAMES_PER_COL),
        .FrameBitsPerRow(FRAME_BITS_PER_ROW)
    ) fabric (
        .Tile_X12Y10_A_EN_top(A_EN_top[0]),
        .Tile_X12Y9_A_EN_top(A_EN_top[1]),
        .Tile_X12Y8_A_EN_top(A_EN_top[2]),
        .Tile_X12Y7_A_EN_top(A_EN_top[3]),
        .Tile_X12Y6_A_EN_top(A_EN_top[4]),
        .Tile_X12Y5_A_EN_top(A_EN_top[5]),
        .Tile_X12Y4_A_EN_top(A_EN_top[6]),
        .Tile_X12Y3_A_EN_top(A_EN_top[7]),
        .Tile_X12Y2_A_EN_top(A_EN_top[8]),
        .Tile_X12Y1_A_EN_top(A_EN_top[9]),
        .Tile_X12Y10_A_IN_top(A_IN_top[0]),
        .Tile_X12Y9_A_IN_top(A_IN_top[1]),
        .Tile_X12Y8_A_IN_top(A_IN_top[2]),
        .Tile_X12Y7_A_IN_top(A_IN_top[3]),
        .Tile_X12Y6_A_IN_top(A_IN_top[4]),
        .Tile_X12Y5_A_IN_top(A_IN_top[5]),
        .Tile_X12Y4_A_IN_top(A_IN_top[6]),
        .Tile_X12Y3_A_IN_top(A_IN_top[7]),
        .Tile_X12Y2_A_IN_top(A_IN_top[8]),
        .Tile_X12Y1_A_IN_top(A_IN_top[9]),
        .Tile_X12Y10_A_OUT_top(A_OUT_top[0]),
        .Tile_X12Y9_A_OUT_top(A_OUT_top[1]),
        .Tile_X12Y8_A_OUT_top(A_OUT_top[2]),
        .Tile_X12Y7_A_OUT_top(A_OUT_top[3]),
        .Tile_X12Y6_A_OUT_top(A_OUT_top[4]),
        .Tile_X12Y5_A_OUT_top(A_OUT_top[5]),
        .Tile_X12Y4_A_OUT_top(A_OUT_top[6]),
        .Tile_X12Y3_A_OUT_top(A_OUT_top[7]),
        .Tile_X12Y2_A_OUT_top(A_OUT_top[8]),
        .Tile_X12Y1_A_OUT_top(A_OUT_top[9]),
        .Tile_X0Y11_SYS_RESET_RESET_top(USER_RESET),
        .Tile_X0Y11_USER_CLOCK_top(USER_CLK),
        .FrameData(frame_data),
        .FrameStrobe(frame_strobe)
    );
endmodule

`default_nettype wire
