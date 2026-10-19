`ifndef VERILATOR
`timescale 1ps / 1ps
`default_nettype none

module sequential_16bit_en_tb ();
    // Pad 16 carries the fabric clock (see user_design/top_wrapper.v).
    localparam integer CLK_PAD = 16;

    wire [39:0] A_IN_top ;
    wire [39:0] A_EN_top ;
    reg  [39:0] pad_in = 0;
    wire [39:0] A_OUT_top;

    reg         CLK                 = 1'b0 ;
    reg         resetn              = 1'b1 ;
    reg         self_write_strobe   = 1'b0 ;
    reg  [31:0] self_write_data     = 32'b0;
    reg         rx                  = 1'b1 ;
    wire        com_active                 ;
    wire        receive_led                ;
    reg         s_clk               = 1'b0 ;
    reg         s_data              = 1'b0 ;
    reg         config_done         = 1'b0 ;
    wire        config_busy                ;
    wire        configured                 ;

    assign A_OUT_top = {pad_in[39:CLK_PAD+1], CLK, pad_in[CLK_PAD-1:0]};

    // Instantiate both the fabric and the reference DUT
    eFPGA_top top_i (
        .A_EN_top           (A_EN_top         ),
        .A_IN_top           (A_IN_top         ),
        .A_OUT_top          (A_OUT_top        ),
        .SYS_RESET_RESET_top(1'b0             ),
        .CLK                (CLK              ),
        .resetn             (resetn           ),
        .SelfWriteStrobe    (self_write_strobe),
        .SelfWriteData      (self_write_data  ),
        .Rx                 (rx               ),
        .ComActive          (com_active       ),
        .ReceiveLED         (receive_led      ),
        .s_clk              (s_clk            ),
        .s_data             (s_data           ),
        .spi_sck            (1'b0             ),
        .spi_cs_n           (1'b1             ),
        .spi_mosi           (1'b0             ),
        .ConfigBusy         (config_busy      ),
        .Configured         (configured       )
    );


    wire [39:0] A_IN_top_gold, oeb_gold, A_EN_top_gold;
    sequential_16bit_en dut_i (
        .clk   (CLK          ),
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
    reg     have_errors = 1'b0;

    reg [2047:0] bitstream_hex_arg  ; // 256 bytes for characters
    reg [2047:0] output_waveform_arg; // 256 bytes for characters

    // Gate-level only: the hardened fabric powers up X-pessimistic. The
    // generated force_block.vh deposits 0 onto every fabric net and pulses the
    // flop async resets once config_done is high.
`ifdef GL_SIM
    `include "force_block.vh"

    // Progress for runtime estimates of the (slow) whole-fabric GL run.
    integer n_cycles = 0;
    always @(posedge CLK) begin
        n_cycles = n_cycles + 1;
        if (n_cycles % 1000 == 0) $display("[gl] %0d cycles @ %0t", n_cycles, $time);
    end
`endif

    initial begin

        if ($value$plusargs("output_waveform=%s", output_waveform_arg)) begin
            $dumpfile(output_waveform_arg);
            $dumpvars(0, sequential_16bit_en_tb);
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
        for (i = 0; i < MAX_BITBYTES; i = i + 4) begin
            self_write_data <= {bitstream[i], bitstream[i+1], bitstream[i+2], bitstream[i+3]};
            repeat (2) @(posedge CLK);
            self_write_strobe <= 1'b1;
            @(posedge CLK);
            self_write_strobe <= 1'b0;
            repeat (2) @(posedge CLK);
        end
        if (configured !== 1'b1) begin
            $display("Error: the bitstream finished loading but Configured is %b", configured);
            $fatal;
        end
`endif
        config_done = 1'b1;  // configuration upload complete -> trigger GL X-init
        repeat (100) @(posedge CLK);
        // Pads change on the falling edge so the gold and the fabric (whose
        // clock arrives through the GBUF) sample the same value.
        @(negedge CLK);
        // Enable and reset the counter
        pad_in[1:0] = 2'b11;
        repeat (5) @(negedge CLK);
        // Deassert reset while keeping the counter enabled
        pad_in[1:0] = 2'b10;
        for (i = 0; i < 100; i = i + 1) begin
            @(negedge CLK);
            $display("fabric(A_IN_top) = 0x%X gold = 0x%X, fabric(A_EN_top) = 0x%X gold = 0x%X",
                A_IN_top, A_IN_top_gold, A_EN_top, A_EN_top_gold);
            // A pad's output data is observable only while its output is enabled.
            if ((A_IN_top & A_EN_top_gold) !== (A_IN_top_gold & A_EN_top_gold)) have_errors = 1'b1;
            if (A_EN_top !== A_EN_top_gold) have_errors = 1'b1;
        end

        if (have_errors) $fatal;
        else $finish;
    end

endmodule
`endif
`default_nettype wire
