`default_nettype none

// Merges the configuration ports into the 32-bit word stream fabric_config
// takes. Priority, highest first: UART > bitbang > SPI > parallel SelfWrite.
module config_frontend #(
    // config_UART: [0:auto|1:hex|2:bin]. Its bit period is ComRate + 1 clk
    // cycles, since the tick counter runs from ComRate down to 0.
    parameter [1:0] UartMode = 2'd0,
    parameter [11:0] ComRate = 12'd217
) (
    input wire CLK,
    input wire resetn,
    // UART configuration port
    input wire Rx,
    output wire ComActive,
    output wire ReceiveLED,
    // BitBang configuration port
    input wire s_clk,
    input wire s_data,
    // SPI configuration port, mode 0, write only
    input wire spi_sck,
    input wire spi_cs_n,
    input wire spi_mosi,
    // Parallel configuration port
    input wire [31:0] SelfWriteData,
    input wire SelfWriteStrobe,
    // To fabric_config
    output wire [31:0] bitstream_data,
    output wire bitstream_valid
);

    wire [31:0] uart_data;
    wire uart_strobe;
    wire uart_active;
    wire uart_led;

    wire [31:0] bitbang_data;
    wire bitbang_strobe;
    wire bitbang_active;

    wire [31:0] spi_data;
    wire spi_strobe;
    wire spi_active;

    config_UART #(
        .Mode(UartMode),
        .ComRate(ComRate)
    ) inst_config_UART (
        .CLK(CLK),
        .reset_n(resetn),
        .Rx(Rx),
        .WriteData(uart_data),
        .ComActive(uart_active),
        .WriteStrobe(uart_strobe),
        .Command(),
        .ReceiveLED(uart_led)
    );

    bitbang inst_bitbang (
        .s_clk(s_clk),
        .s_data(s_data),
        .strobe(bitbang_strobe),
        .data(bitbang_data),
        .active(bitbang_active),
        .clk(CLK),
        .reset_n(resetn)
    );

    config_spi inst_config_spi (
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .strobe(spi_strobe),
        .data(spi_data),
        .active(spi_active),
        .clk(CLK),
        .reset_n(resetn)
    );

    assign bitstream_data =
        uart_active    ? uart_data    :
        bitbang_active ? bitbang_data :
        spi_active     ? spi_data     :
                         SelfWriteData;
    assign bitstream_valid =
        uart_active    ? uart_strobe    :
        bitbang_active ? bitbang_strobe :
        spi_active     ? spi_strobe     :
                         SelfWriteStrobe;

    assign ComActive = uart_active;
    assign ReceiveLED = uart_led ^ bitbang_strobe ^ spi_strobe;

endmodule
`resetall
