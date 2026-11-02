`timescale 1ps / 1ps
`default_nettype none

// The RTL fabric (eFPGA_top) loads the paddle_ball bitstream over SPI, then
// runs beside a gold paddle_ball on the same clock, reset and buttons. Every
// cycle compares all ten pads; vga_monitor decodes the fabric's video pins.
// With EMULATION the tiles take the bitstream from bit_gen's .vh as parameters
// and the SPI load is skipped.
// Plusargs: +bitstream_hex=<file> (not under EMULATION) +frames=<frames after
// reset>, and vga_monitor's.
module paddle_ball_fabric_tb;
    localparam BUTTON_FIRST_FRAME = 100;
    localparam BUTTON_LAST_FRAME = 130;
    localparam integer MAX_BITBYTES = 16384;

    wire [9:0] A_IN_top, A_EN_top;
    reg p1_up = 1'b0;
    wire [9:0] pad_in = {4'b0000, p1_up, 5'b00000};

    reg CLK = 1'b0;
    reg resetn = 1'b1;
    reg spi_sck = 1'b0;
    reg spi_cs_n = 1'b1;
    reg spi_mosi = 1'b0;
    reg user_reset = 1'b1;
    wire config_busy, configured, com_active, receive_led;

    eFPGA_top fabric (
        .A_EN_top(A_EN_top),
        .A_IN_top(A_IN_top),
        .A_OUT_top(pad_in),
        .USER_CLK(CLK),
        .USER_RESET(user_reset),
        .CLK(CLK),
        .resetn(resetn),
        .Rx(1'b1),
        .ComActive(com_active),
        .ReceiveLED(receive_led),
        .spi_sck(spi_sck),
        .spi_cs_n(spi_cs_n),
        .spi_mosi(spi_mosi),
        .ConfigBusy(config_busy),
        .Configured(configured)
    );

`ifdef EMULATION
    // eFPGA.v instantiates the border-row tiles without the EMULATION override
    // the other tiles get, which leaves SW_term's GBUFs, and so USER_CLK and
    // USER_RESET, unconnected. Drop these once eFPGA.v passes them itself.
    defparam fabric.fabric.Tile_X0Y0_NW_term.Emulate_Bitstream = `Tile_X0Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X1Y0_N_term.Emulate_Bitstream = `Tile_X1Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X2Y0_N_term.Emulate_Bitstream = `Tile_X2Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X3Y0_N_term.Emulate_Bitstream = `Tile_X3Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X4Y0_N_term.Emulate_Bitstream = `Tile_X4Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X5Y0_N_term.Emulate_Bitstream = `Tile_X5Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X6Y0_N_term_MACC.Emulate_Bitstream = `Tile_X6Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X7Y0_N_term.Emulate_Bitstream = `Tile_X7Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X8Y0_N_term.Emulate_Bitstream = `Tile_X8Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X9Y0_N_term.Emulate_Bitstream = `Tile_X9Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X10Y0_N_term.Emulate_Bitstream = `Tile_X10Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X11Y0_N_term.Emulate_Bitstream = `Tile_X11Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X12Y0_NE_term.Emulate_Bitstream = `Tile_X12Y0_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X0Y11_SW_term.Emulate_Bitstream = `Tile_X0Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X1Y11_S_term.Emulate_Bitstream = `Tile_X1Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X2Y11_S_term.Emulate_Bitstream = `Tile_X2Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X3Y11_S_term.Emulate_Bitstream = `Tile_X3Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X4Y11_S_term.Emulate_Bitstream = `Tile_X4Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X5Y11_S_term.Emulate_Bitstream = `Tile_X5Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X6Y11_S_term_MACC.Emulate_Bitstream = `Tile_X6Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X7Y11_S_term.Emulate_Bitstream = `Tile_X7Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X8Y11_S_term.Emulate_Bitstream = `Tile_X8Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X9Y11_S_term.Emulate_Bitstream = `Tile_X9Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X10Y11_S_term.Emulate_Bitstream = `Tile_X10Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X11Y11_S_term.Emulate_Bitstream = `Tile_X11Y11_Emulate_Bitstream;
    defparam fabric.fabric.Tile_X12Y11_SE_term.Emulate_Bitstream = `Tile_X12Y11_Emulate_Bitstream;
`endif

    wire [9:0] io_out_gold, io_oeb_gold;
    paddle_ball gold (
        .clk(CLK),
        .user_reset(user_reset),
        .io_in(pad_in),
        .io_out(io_out_gold),
        .io_oeb(io_oeb_gold)
    );
    wire [9:0] A_EN_top_gold = ~io_oeb_gold;

    // 6.29375 MHz, a quarter of the 25.175 MHz VGA dot clock: 158.887 ns.
    always begin
        #79444 CLK = 1'b1;
        #79443 CLK = 1'b0;
    end

    reg running = 1'b0;
    integer frames = 200;
    integer frame;
    integer compares = 0;

    vga_monitor monitor (
        .clk(CLK),
        .active(running),
        .hsync(A_IN_top[0]),
        .vsync(A_IN_top[1]),
        .rgb({A_IN_top[2], A_IN_top[3], A_IN_top[4]}),
        .frame(frame)
    );

    // Pad output data is observable only while the gold enables that pad.
    always @(negedge CLK) if (running) begin
        compares = compares + 1;
        if (compares % 10000 == 0) begin
            $display("%0d compares match @ %0t", compares, $time);
            $fflush();
        end
        if ((A_IN_top & A_EN_top_gold) !== (io_out_gold & A_EN_top_gold) || A_EN_top !== A_EN_top_gold)
            $fatal(1, "pad mismatch at compare %0d, frame %0d: fabric out %b en %b, gold out %b en %b",
                   compares, frame, A_IN_top, A_EN_top, io_out_gold, A_EN_top_gold);
    end

    always @(frame) begin
        p1_up <= frame >= BUTTON_FIRST_FRAME && frame <= BUTTON_LAST_FRAME;
        if (frame >= 0) begin
            $display("frame %0d @ %0t, %0d compares match", frame, $time, compares);
            $fflush();
        end
        if (frame == frames) begin
            $display("SUMMARY frames=%0d written=%0d compares=%0d mismatches=0 score=%0d:%0d",
                     frame, monitor.frames_written, compares, gold.p1_score, gold.p2_score);
            $display("PASS");
            $finish;
        end
    end

    always @(configured) $display("Configured = %b @ %0t", configured, $time);

    reg [7:0] bitstream [MAX_BITBYTES];
    integer n_bytes = 0;
    integer hex_fd;
    reg [7:0] hex_byte;
    string bitstream_hex;
    integer i, b;
    reg [31:0] word;

    initial begin
        void'($value$plusargs("frames=%d", frames));
`ifndef EMULATION
        if (!$value$plusargs("bitstream_hex=%s", bitstream_hex)) $fatal(1, "no +bitstream_hex given");
        hex_fd = $fopen(bitstream_hex, "r");
        if (hex_fd == 0) $fatal(1, "cannot open %s", bitstream_hex);
        while ($fscanf(hex_fd, "%h", hex_byte) == 1) begin
            if (n_bytes == MAX_BITBYTES) $fatal(1, "the bitstream is longer than MAX_BITBYTES = %0d", MAX_BITBYTES);
            bitstream[n_bytes] = hex_byte;
            n_bytes = n_bytes + 1;
        end
        if (!$feof(hex_fd) || n_bytes == 0 || n_bytes % 4 != 0)
            $fatal(1, "%s holds %0d bytes before its first non-hex entry; expected whole 32-bit words to the end of the file",
                   bitstream_hex, n_bytes);
        $fclose(hex_fd);
        $display("Read %0d bitstream bytes from %s", n_bytes, bitstream_hex);

        #100;
        resetn = 1'b0;
        // fabric_config resets synchronously, so reset has to span clock edges.
        repeat (2) @(posedge CLK);
        resetn = 1'b1;
        repeat (20) @(posedge CLK);
        // SPI mode 0, MSB first, at the f_clk = 4 f_sck config_spi.v asks for:
        // SCK low and high two CLK periods each, every change on a falling edge.
        @(negedge CLK);
        spi_cs_n = 1'b0;
        repeat (4) @(negedge CLK);
        for (i = 0; i < n_bytes; i = i + 4) begin
            word = {bitstream[i], bitstream[i+1], bitstream[i+2], bitstream[i+3]};
            for (b = 31; b >= 0; b = b - 1) begin
                spi_mosi = word[b];
                repeat (2) @(negedge CLK);
                spi_sck = 1'b1;
                repeat (2) @(negedge CLK);
                spi_sck = 1'b0;
            end
        end
        repeat (4) @(negedge CLK);
        spi_cs_n = 1'b1;
        repeat (8) @(posedge CLK);
        if (configured !== 1'b1) $fatal(1, "the bitstream finished loading but Configured is %b", configured);
`endif

        // USER_RESET reaches the fabric's flops through GBUF B and GSR; held
        // across the gold's wake counter so both leave reset together.
        repeat (8) @(posedge CLK);
        @(negedge CLK);
        user_reset = 1'b0;
        running = 1'b1;
    end
endmodule

`default_nettype wire
