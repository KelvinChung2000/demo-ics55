`ifndef VERILATOR
`timescale 1ps / 1ps
`default_nettype none

module sequential_16bit_en_tb ();
    wire [9:0] A_IN_top ;
    wire [9:0] A_EN_top ;
    reg  [9:0] pad_in = 0;
    wire [9:0] A_OUT_top;

    reg         CLK                 = 1'b0 ;
    reg         resetn              = 1'b1 ;
    reg         spi_sck             = 1'b0 ;
    reg         spi_cs_n            = 1'b1 ;
    reg         spi_mosi            = 1'b0 ;
    reg         rx                  = 1'b1 ;
    wire        com_active                 ;
    wire        receive_led                ;
    reg         user_reset          = 1'b0 ;
    reg         config_done         = 1'b0 ;
    wire        config_busy                ;
    wire        configured                 ;

    assign A_OUT_top = pad_in;

    wire [9:0] A_IN_top_gold, oeb_gold, A_EN_top_gold;

    // Instantiate both the fabric and the reference DUT
`ifdef GL_CHIP
    // Every signal crosses a pad of submission/chip/top.v. The tester drives
    // only the user pins the reference design reads.
    eFPGA_chip_gl top_i (
        .A_OUT_top_drive    (oeb_gold         ),
`elsif GL_TOP
    // The hardened netlist's ports are per bit; Test/gen_gl_top.py's wrapper restores the vectors.
    eFPGA_top_gl top_i (
`else
    eFPGA_top top_i (
`endif
        .A_EN_top           (A_EN_top         ),
        .A_IN_top           (A_IN_top         ),
        .A_OUT_top          (A_OUT_top        ),
        // The fabric clock is CLK on its own pad (see user_design/top_wrapper.v).
        .USER_CLK           (CLK              ),
        .USER_RESET         (user_reset       ),
        .CLK                (CLK              ),
        .resetn             (resetn           ),
        .Rx                 (rx               ),
        .ComActive          (com_active       ),
        .ReceiveLED         (receive_led      ),
        .spi_sck            (spi_sck          ),
        .spi_cs_n           (spi_cs_n         ),
        .spi_mosi           (spi_mosi         ),
        .ConfigBusy         (config_busy      ),
        .Configured         (configured       )
    );


    sequential_16bit_en dut_i (
        .clk   (CLK          ),
        .user_reset(user_reset),
        .io_out(A_IN_top_gold),
        .io_oeb(oeb_gold     ),
        .io_in (A_OUT_top    )
    );

    assign A_EN_top_gold = ~oeb_gold;

    localparam integer       MAX_BITBYTES               = 16384;
    reg                [7:0] bitstream   [MAX_BITBYTES]        ;

    // a slower clock to make it easier to meet timing in gate-level sim
    always #500000 CLK = (CLK === 1'b0);

    integer i                 ;
    integer b                 ;
    reg     [31:0] word       ;
    reg     have_errors = 1'b0;
    integer compares    = 0   ;
    integer mismatches  = 0   ;

    // One compare on the next falling edge, where the pads also change.
    task automatic compare;
        begin
            @(negedge CLK);
            $display("fabric(A_IN_top) = 0x%X gold = 0x%X, fabric(A_EN_top) = 0x%X gold = 0x%X",
                A_IN_top, A_IN_top_gold, A_EN_top, A_EN_top_gold);
            compares = compares + 1;
            // A pad's output data is observable only while its output is enabled.
            if ((A_IN_top & A_EN_top_gold) !== (A_IN_top_gold & A_EN_top_gold)
                || A_EN_top !== A_EN_top_gold) begin
                mismatches = mismatches + 1;
                have_errors = 1'b1;
            end
        end
    endtask

    reg [2047:0] bitstream_hex_arg  ; // 256 bytes for characters
    reg [2047:0] output_waveform_arg; // 256 bytes for characters
    integer      waveform_depth     ;

    // Gate-level only: the hardened fabric powers up X-pessimistic. The
    // generated force_block.vh deposits 0 onto every fabric net and pulses the
    // flop async resets once config_done is high.
`ifdef GL_SIM
    `include "force_block.vh"
    `define GL_PROGRESS
`endif
`ifdef GL_TOP
    `define GL_PROGRESS
`endif

`ifdef GL_PROGRESS
    // Progress for runtime estimates of the (slow) whole-fabric GL run.
    // +max_cycles=N ends a smoke run after N CLK cycles.
    integer n_cycles = 0;
    integer max_cycles;
    initial if (!$value$plusargs("max_cycles=%d", max_cycles)) max_cycles = 0;
    always @(posedge CLK) begin
        n_cycles = n_cycles + 1;
        if (n_cycles % 1000 == 0) $display("[gl] %0d cycles @ %0t", n_cycles, $time);
        if (n_cycles == max_cycles) begin
            $display("[gl] stopped at +max_cycles=%0d @ %0t", max_cycles, $time);
            $finish;
        end
    end
`endif

    always @(config_busy) $display("ConfigBusy = %b @ %0t", config_busy, $time);
    always @(configured) $display("Configured = %b @ %0t", configured, $time);

    initial begin

        // +waveform_depth=1 keeps the dump to this scope; a whole-fabric dump
        // of the SPI load runs to tens of GB.
        if (!$value$plusargs("waveform_depth=%d", waveform_depth)) waveform_depth = 0;
        if ($value$plusargs("output_waveform=%s", output_waveform_arg)) begin
            $dumpfile(output_waveform_arg);
            $dumpvars(waveform_depth, sequential_16bit_en_tb);
            $display("Output waveform set to %s", output_waveform_arg);
        end

`ifndef EMULATION

        if ($value$plusargs("bitstream_hex=%s", bitstream_hex_arg)) begin
            $readmemh(bitstream_hex_arg, bitstream);
            $display("Read bitstream hex from %s", bitstream_hex_arg);
        end else begin
            $display("Error: No bitstream provided as $plusargs bitstream_hex.");
            $fatal;
        end


        #100;
        resetn = 1'b0;
        // fabric_config resets synchronously, so reset has to span clock edges.
        repeat (2) @(posedge CLK);
        resetn = 1'b1;
        #10000;
        repeat (20) @(posedge CLK);
        #2500;
        // SPI mode 0, MSB first, at the f_clk = 4 f_sck config_spi.v asks for:
        // SCK low and high two CLK periods each, every change on a falling edge.
        @(negedge CLK);
        spi_cs_n = 1'b0;
        repeat (4) @(negedge CLK);
        for (i = 0; i < MAX_BITBYTES; i = i + 4) begin
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
        if (configured !== 1'b1) begin
            $display("Error: the bitstream finished loading but Configured is %b", configured);
            $fatal;
        end
`endif
        config_done = 1'b1;  // configuration upload complete -> trigger GL X-init
`ifdef GL_TOP
        // Gate-level flops power up X, and the gate-level LUT does not mask X the
        // way the design's synchronous reset needs, so clear them through
        // USER_RESET (GBUF and GSR) first, as a bring-up would.
        user_reset = 1'b1;
        repeat (2) @(posedge CLK);
        user_reset = 1'b0;
`endif
        repeat (100) @(posedge CLK);
        // Pads change on the falling edge so the gold and the fabric (whose
        // clock arrives through the GBUF) sample the same value.
        @(negedge CLK);
        // Enable and reset the counter
        pad_in[1:0] = 2'b11;
        repeat (5) @(negedge CLK);
        // Deassert reset while keeping the counter enabled
        pad_in[1:0] = 2'b10;
        for (i = 0; i < 100; i = i + 1) compare;
        $display("count: %0d of %0d compares match", compares - mismatches, compares);
        // USER_RESET clears the counter through GBUF B and GSR while it counts.
        user_reset = 1'b1;
        for (i = 0; i < 3; i = i + 1) compare;
        if (A_IN_top_gold[9:2] !== 8'd0) begin
            $display("Error: the reference counter did not clear under USER_RESET");
            have_errors = 1'b1;
        end
        user_reset = 1'b0;
        for (i = 0; i < 20; i = i + 1) compare;
        $display("total: %0d of %0d compares match", compares - mismatches, compares);

        if (have_errors) $fatal;
        else $finish;
    end

endmodule
`endif
`default_nettype wire
