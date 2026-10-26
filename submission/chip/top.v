// Chip-level netlist for the FABulous eFPGA on ICS55, written by `flow cli chip-top`.
// Do not edit; regenerate. The macro's pins are read from eFPGA_top_Harden.lib.
//
// 22 P65_1233_PBMUX signal pads: 10 bidirectional user IO, each
// joining A_OUT_top_i (pad to fabric), A_IN_top_i (fabric to pad) and A_EN_top_i
// (output enable), and 12 single-pin pads.
// Every pad: OD = 0 push-pull, CS = 0 Schmitt input, DS0 = DS1 = 0 for 16 mA (both
// active low), IE = 1 except on outputs. PU = 1 only on PAD_RSTN and PAD_SPI_CSN.
// Corner and supply pads carry no signal and are placed by the physical flow.

`timescale 1ns / 1ps

module top (
    PAD_CLK,
    PAD_UART_RX,
    PAD_USER_CLK,
    PAD_USER_RESET,
    PAD_RSTN,
    PAD_SPI_CSN,
    PAD_SPI_MOSI,
    PAD_SPI_SCK,
    PAD_UART_ACTIVE,
    PAD_CFG_BUSY,
    PAD_CFG_DONE,
    PAD_CFG_LED,
    PAD_IO
);

input  PAD_CLK;
input  PAD_UART_RX;
input  PAD_USER_CLK;
input  PAD_USER_RESET;
input  PAD_RSTN;
input  PAD_SPI_CSN;
input  PAD_SPI_MOSI;
input  PAD_SPI_SCK;
output PAD_UART_ACTIVE;
output PAD_CFG_BUSY;
output PAD_CFG_DONE;
output PAD_CFG_LED;
inout  [9:0] PAD_IO;

// The ring's supplies; the IO LEF makes them USE POWER / USE GROUND pins.
supply1 VDD;
supply1 VDDIO;
supply0 VSS;
supply0 VSSIO;

wire A_EN_top_0, A_EN_top_1, A_EN_top_2, A_EN_top_3, A_EN_top_4, A_EN_top_5, A_EN_top_6, A_EN_top_7, A_EN_top_8, A_EN_top_9, A_IN_top_0, A_IN_top_1, A_IN_top_2, A_IN_top_3, A_IN_top_4, A_IN_top_5, A_IN_top_6, A_IN_top_7, A_IN_top_8, A_IN_top_9, A_OUT_top_0, A_OUT_top_1, A_OUT_top_2, A_OUT_top_3, A_OUT_top_4, A_OUT_top_5, A_OUT_top_6, A_OUT_top_7, A_OUT_top_8, A_OUT_top_9, CLK, ComActive, ConfigBusy, Configured, ReceiveLED, Rx, USER_CLK, USER_RESET, resetn, spi_cs_n, spi_mosi, spi_sck;

eFPGA_top u_efpga (
    .A_EN_top_0  (A_EN_top_0),
    .A_EN_top_1  (A_EN_top_1),
    .A_EN_top_2  (A_EN_top_2),
    .A_EN_top_3  (A_EN_top_3),
    .A_EN_top_4  (A_EN_top_4),
    .A_EN_top_5  (A_EN_top_5),
    .A_EN_top_6  (A_EN_top_6),
    .A_EN_top_7  (A_EN_top_7),
    .A_EN_top_8  (A_EN_top_8),
    .A_EN_top_9  (A_EN_top_9),
    .A_IN_top_0  (A_IN_top_0),
    .A_IN_top_1  (A_IN_top_1),
    .A_IN_top_2  (A_IN_top_2),
    .A_IN_top_3  (A_IN_top_3),
    .A_IN_top_4  (A_IN_top_4),
    .A_IN_top_5  (A_IN_top_5),
    .A_IN_top_6  (A_IN_top_6),
    .A_IN_top_7  (A_IN_top_7),
    .A_IN_top_8  (A_IN_top_8),
    .A_IN_top_9  (A_IN_top_9),
    .A_OUT_top_0 (A_OUT_top_0),
    .A_OUT_top_1 (A_OUT_top_1),
    .A_OUT_top_2 (A_OUT_top_2),
    .A_OUT_top_3 (A_OUT_top_3),
    .A_OUT_top_4 (A_OUT_top_4),
    .A_OUT_top_5 (A_OUT_top_5),
    .A_OUT_top_6 (A_OUT_top_6),
    .A_OUT_top_7 (A_OUT_top_7),
    .A_OUT_top_8 (A_OUT_top_8),
    .A_OUT_top_9 (A_OUT_top_9),
    .CLK         (CLK),
    .ComActive   (ComActive),
    .ConfigBusy  (ConfigBusy),
    .Configured  (Configured),
    .ReceiveLED  (ReceiveLED),
    .Rx          (Rx),
    .USER_CLK    (USER_CLK),
    .USER_RESET  (USER_RESET),
    .resetn      (resetn),
    .spi_cs_n    (spi_cs_n),
    .spi_mosi    (spi_mosi),
    .spi_sck     (spi_sck)
);

// CLK
P65_1233_PBMUX u_pad_0 (
    .PAD (PAD_CLK),
    .C   (CLK),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// ComActive
P65_1233_PBMUX u_pad_1 (
    .PAD (PAD_UART_ACTIVE),
    .C   (),
    .I   (ComActive),
    .OE  (1'b1),
    .IE  (1'b0),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// ConfigBusy
P65_1233_PBMUX u_pad_2 (
    .PAD (PAD_CFG_BUSY),
    .C   (),
    .I   (ConfigBusy),
    .OE  (1'b1),
    .IE  (1'b0),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// Configured
P65_1233_PBMUX u_pad_3 (
    .PAD (PAD_CFG_DONE),
    .C   (),
    .I   (Configured),
    .OE  (1'b1),
    .IE  (1'b0),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// ReceiveLED
P65_1233_PBMUX u_pad_4 (
    .PAD (PAD_CFG_LED),
    .C   (),
    .I   (ReceiveLED),
    .OE  (1'b1),
    .IE  (1'b0),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// Rx
P65_1233_PBMUX u_pad_5 (
    .PAD (PAD_UART_RX),
    .C   (Rx),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// USER_CLK
P65_1233_PBMUX u_pad_6 (
    .PAD (PAD_USER_CLK),
    .C   (USER_CLK),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// USER_RESET
P65_1233_PBMUX u_pad_7 (
    .PAD (PAD_USER_RESET),
    .C   (USER_RESET),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// resetn
P65_1233_PBMUX u_pad_8 (
    .PAD (PAD_RSTN),
    .C   (resetn),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b1),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// spi_cs_n
P65_1233_PBMUX u_pad_9 (
    .PAD (PAD_SPI_CSN),
    .C   (spi_cs_n),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b1),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// spi_mosi
P65_1233_PBMUX u_pad_10 (
    .PAD (PAD_SPI_MOSI),
    .C   (spi_mosi),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// spi_sck
P65_1233_PBMUX u_pad_11 (
    .PAD (PAD_SPI_SCK),
    .C   (spi_sck),
    .I   (1'b0),
    .OE  (1'b0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 0
P65_1233_PBMUX u_pad_12 (
    .PAD (PAD_IO[0]),
    .C   (A_OUT_top_0),
    .I   (A_IN_top_0),
    .OE  (A_EN_top_0),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 1
P65_1233_PBMUX u_pad_13 (
    .PAD (PAD_IO[1]),
    .C   (A_OUT_top_1),
    .I   (A_IN_top_1),
    .OE  (A_EN_top_1),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 2
P65_1233_PBMUX u_pad_14 (
    .PAD (PAD_IO[2]),
    .C   (A_OUT_top_2),
    .I   (A_IN_top_2),
    .OE  (A_EN_top_2),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 3
P65_1233_PBMUX u_pad_15 (
    .PAD (PAD_IO[3]),
    .C   (A_OUT_top_3),
    .I   (A_IN_top_3),
    .OE  (A_EN_top_3),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 4
P65_1233_PBMUX u_pad_16 (
    .PAD (PAD_IO[4]),
    .C   (A_OUT_top_4),
    .I   (A_IN_top_4),
    .OE  (A_EN_top_4),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 5
P65_1233_PBMUX u_pad_17 (
    .PAD (PAD_IO[5]),
    .C   (A_OUT_top_5),
    .I   (A_IN_top_5),
    .OE  (A_EN_top_5),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 6
P65_1233_PBMUX u_pad_18 (
    .PAD (PAD_IO[6]),
    .C   (A_OUT_top_6),
    .I   (A_IN_top_6),
    .OE  (A_EN_top_6),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 7
P65_1233_PBMUX u_pad_19 (
    .PAD (PAD_IO[7]),
    .C   (A_OUT_top_7),
    .I   (A_IN_top_7),
    .OE  (A_EN_top_7),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 8
P65_1233_PBMUX u_pad_20 (
    .PAD (PAD_IO[8]),
    .C   (A_OUT_top_8),
    .I   (A_IN_top_8),
    .OE  (A_EN_top_8),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

// user IO bit 9
P65_1233_PBMUX u_pad_21 (
    .PAD (PAD_IO[9]),
    .C   (A_OUT_top_9),
    .I   (A_IN_top_9),
    .OE  (A_EN_top_9),
    .IE  (1'b1),
    .OD  (1'b0),
    .CS  (1'b0),
    .PU  (1'b0),
    .PD  (1'b0),
    .DS0 (1'b0),
    .DS1 (1'b0),
    .A   (),
    .VDD (VDD), .VSS (VSS), .VDDIO (VDDIO), .VSSIO (VSSIO)
);

endmodule
