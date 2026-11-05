`timescale 1ps / 1ps
`default_nettype none

// RTL-only testbench for paddle_ball. vga_monitor checks the timing on the
// pins and writes the frames; hierarchical counters check the game was played.
// Plusargs: +frames=<frames to simulate>, and vga_monitor's.
module paddle_ball_rtl_tb;
    localparam BUTTON_FIRST_FRAME = 100;
    localparam BUTTON_LAST_FRAME = 130;

    reg clk = 1'b0;
    reg user_reset = 1'b1;
    reg p1_up = 1'b0;
    wire [9:0] io_in = {4'b0000, p1_up, 5'b00000};
    wire [9:0] io_out, io_oeb;

    paddle_ball dut (
        .clk(clk),
        .user_reset(user_reset),
        .io_in(io_in),
        .io_out(io_out),
        .io_oeb(io_oeb)
    );

    // 6.29375 MHz, a quarter of the 25.175 MHz VGA dot clock: 158.887 ns.
    always begin
        #79444 clk = 1'b1;
        #79443 clk = 1'b0;
    end

    integer frames = 1200;

    initial begin
        void'($value$plusargs("frames=%d", frames));
        repeat (8) @(posedge clk);
        user_reset <= 1'b0;
    end

    integer frame;
    vga_monitor monitor (
        .clk(clk),
        .active(!user_reset),
        .hsync(io_out[0]),
        .vsync(io_out[1]),
        .rgb({io_out[2], io_out[3], io_out[4]}),
        .frame(frame)
    );

    always @(negedge clk) if (!user_reset) begin
        if (^io_out === 1'bx) $fatal(1, "io_out has X: %b", io_out);
        if (io_oeb !== 10'b0_1111_00000) $fatal(1, "io_oeb %b, expected pads 5..8 as inputs", io_oeb);
    end

    always @(frame) begin
        p1_up <= frame >= BUTTON_FIRST_FRAME && frame <= BUTTON_LAST_FRAME;
        if (frame == frames) finish_run();
    end

    integer p1_points = 0;
    integer p2_points = 0;
    integer paddle_hits = 0;
    integer wall_hits = 0;
    integer both_play_frames = 0;
    reg a_played = 1'b0;
    reg b_played = 1'b0;

    always @(negedge clk) if (!user_reset && dut.frame_tick) begin
        p1_points = p1_points + dut.a_p1_scores + dut.b_p1_scores;
        p2_points = p2_points + dut.a_p2_scores + dut.b_p2_scores;
        paddle_hits = paddle_hits + dut.a_paddle_hit + dut.b_paddle_hit;
        wall_hits = wall_hits + dut.a_wall_hit + dut.b_wall_hit;
        if (dut.a_play && dut.b_play) both_play_frames = both_play_frames + 1;
        a_played = a_played | dut.a_play;
        b_played = b_played | dut.b_play;
    end

    task finish_run;
        begin
            $display("SUMMARY frames=%0d written=%0d p1_points=%0d p2_points=%0d paddle_hits=%0d wall_hits=%0d both_play_frames=%0d score=%0d:%0d",
                     frame, monitor.frames_written, p1_points, p2_points, paddle_hits, wall_hits, both_play_frames,
                     dut.p1_score, dut.p2_score);
            if (p1_points + p2_points < 1) $fatal(1, "FAIL: no point scored");
            if (paddle_hits < 4) $fatal(1, "FAIL: %0d paddle hits, expected at least 4", paddle_hits);
            if (!a_played || !b_played) $fatal(1, "FAIL: a ball never reached PLAY (A %0d, B %0d)", a_played, b_played);
            $display("PASS");
            $finish;
        end
    endtask
endmodule

`default_nettype wire
