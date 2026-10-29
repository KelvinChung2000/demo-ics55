// Post-route timing simulation of sequential_16bit_en with nextpnr's SDF
// back-annotated, run by the run-timing-sim task. Icarus applies the IOPATH and
// INTERCONNECT delays but not SETUPHOLD, so a setup or hold verdict comes from
// nextpnr's report. The routed netlist has no ports, so the testbench drives
// the pad side of the IO cells hierarchically.
// Input paths reach the flops a design-dependent number of cycles late, so the
// flop check is self-consistency once the inputs have been stable for SETTLE
// cycles: counting gives q+1, holding gives q, and an rst pulse gives 0. A
// register-to-register violation breaks the increment. The flops are sampled
// half a period after the clock reaches REF_CLK, a flop's own CLK pin, since
// clock insertion through the fabric is a large part of a period. The pads are
// compared with the flops just before each testbench rising edge, which fails
// when clock-to-pad exceeds the period.
`timescale 1ps / 1ps
`include "refs.vh"
module sequential_16bit_en_timing_tb;
    parameter integer PERIOD = 1000000;
    parameter integer SETTLE = 4;
    parameter SDF = "design.sdf";

    reg clk = 1'b0;
    reg user_reset = 1'b1;
    reg rst = 1'b0;
    reg en = 1'b1;
    always #(PERIOD / 2) clk = ~clk;

    top dut ();
    initial $sdf_annotate(SDF, dut);

    always @(clk) dut.clk_pad_i.pad_drive = clk;
    always @(user_reset) dut.reset_pad_i.pad_drive = user_reset;
    always @(rst) dut.io0_i.pad_drive = rst;
    always @(en) dut.io1_i.pad_drive = en;
    initial begin
        dut.clk_pad_i.pad_drive = clk;
        dut.reset_pad_i.pad_drive = user_reset;
        dut.io0_i.pad_drive = rst;
        dut.io1_i.pad_drive = en;
    end

    wire [7:0] pad = {dut.io9_i.IN, dut.io8_i.IN, dut.io7_i.IN, dut.io6_i.IN,
                      dut.io5_i.IN, dut.io4_i.IN, dut.io3_i.IN, dut.io2_i.IN};
    // With -ginterconnect the delay sits at each sink, so a driver's net
    // carries Q after CLK->Q only.
    wire [7:0] q = {dut.\io_out[9] , dut.\io_out[8] , dut.\io_out[7] , dut.\io_out[6] ,
                    dut.\io_out[5] , dut.\io_out[4] , dut.\io_out[3] , dut.\io_out[2] };

    // Cycles since the last input change, counted at the check point.
    integer stable = 0;
    always @(user_reset or rst or en) stable = -1;

    // Latest pad change after a rising edge in a stable cycle: the observed
    // clock-to-pad delay.
    time edge_at = 0;
    time settle = 0;
    time settle_max = 0;
    always @(posedge clk) edge_at = $time;
    always @(pad) if (stable >= SETTLE) begin
        settle = $time - edge_at;
        if (settle > settle_max) settle_max = settle;
    end

    integer cycles = 0;
    integer checked = 0;
    integer errors = 0;
    integer pad_errors = 0;
    integer zeros = 0;
    reg [7:0] q_prev = 8'hxx;
    reg [7:0] expect_q;
    always @(posedge `REF_CLK) begin
        #(PERIOD / 2);
        cycles = cycles + 1;
        stable = stable + 1;
        if (stable >= SETTLE && !user_reset) begin
            expect_q = rst ? 8'h00 : en ? q_prev + 8'h01 : q_prev;
            checked = checked + 1;
            if (q !== expect_q) begin
                errors = errors + 1;
                if (errors <= 10)
                    $display("t=%0t cycle %0d: flops %h, expected %h", $time, cycles, q, expect_q);
            end
        end
        if (q === 8'h00) zeros = zeros + 1;
        q_prev = q;
    end
    always @(posedge clk) begin
        #(PERIOD - 1);
        if (stable >= SETTLE && !user_reset && pad !== q) pad_errors = pad_errors + 1;
    end

    task automatic wait_cycles(input integer n);
        repeat (n) @(negedge clk);
    endtask

    integer zeros_before_rst;
    initial begin
        wait_cycles(SETTLE + 2);
        user_reset = 1'b0;
        wait_cycles(300);
        en = 1'b0;
        wait_cycles(SETTLE + 10);
        en = 1'b1;
        wait_cycles(SETTLE + 10);
        zeros_before_rst = zeros;
        rst = 1'b1;
        wait_cycles(SETTLE + 2);
        if (zeros == zeros_before_rst) begin
            errors = errors + 1;
            $display("rst did not clear the counter");
        end
        rst = 1'b0;
        wait_cycles(SETTLE + 20);
        $display("PERIOD %0d ps, %0d cycles, %0d checked, %0d flop mismatches, %0d pad mismatches",
                 PERIOD, cycles, checked, errors, pad_errors);
        // settle_max counts from the latest edge, so it wraps once a pad lags past the next one.
        if (pad_errors == 0) $display("max clock-to-pad %0d ps", settle_max);
        else $display("clock-to-pad exceeds the period");
        if (errors != 0) $fatal(1, "FAIL");
        $display("PASS");
        $finish;
    end
endmodule
