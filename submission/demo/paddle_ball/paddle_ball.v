`default_nettype none

// Two-player paddle-and-ball game with two balls in play, on 640x480 VGA at a
// quarter of the dot clock. The playfield is 160x120 logical pixels, each 4x4
// screen pixels.
module paddle_ball (
    input wire clk,
    // Synchronous; the fabric takes it from the USER_RESET pad.
    input wire user_reset,
    input wire [9:0] io_in,
    output wire [9:0] io_out,
    output wire [9:0] io_oeb
);
    localparam [7:0] FIELD_W = 8'd160;
    localparam [6:0] FIELD_H = 7'd120;
    localparam [6:0] PADDLE_H = 7'd16;
    localparam [7:0] LEFT_PADDLE_X = 8'd4;
    localparam [7:0] RIGHT_PADDLE_X = 8'd154;
    localparam [2:0] BALL_R = 3'd3;
    localparam [7:0] NET_X = 8'd79;
    localparam [7:0] AI_VIEW = 8'd64;
    // Score glyphs are 3x5 cells of 4x4 pixels, on 4-pixel boundaries.
    localparam [5:0] P1_DIGIT_CELL_X = 6'd15;
    localparam [5:0] P2_DIGIT_CELL_X = 6'd22;
    localparam [4:0] DIGIT_CELL_Y = 5'd1;

    // The reset GBUF reaches a flop's SR but no LUT input, and Yosys ORs a
    // reset into LUT logic for any register that also holds or wraps. So
    // user_reset clears this counter alone and the game resets from its
    // output. One flop with D = 1 would become a LUT on user_reset.
    reg [1:0] wake;
    always @(posedge clk)
        if (user_reset) wake <= 2'd0;
        else wake <= wake + (wake != 2'd3);
    wire reset = wake != 2'd3;

    wire p1_up = io_in[5];
    wire p1_down = io_in[6];
    wire p2_up = io_in[7];
    wire p2_down = io_in[8];

    wire [7:0] x;
    wire [9:0] vcount;
    wire [6:0] y = vcount[8:2];
    wire visible, hsync_n, vsync_n, frame_tick;
    vga_timing timing (
        .clk(clk),
        .reset(reset),
        .hcount(x),
        .vcount(vcount),
        .visible(visible),
        .hsync_n(hsync_n),
        .vsync_n(vsync_n),
        .frame_tick(frame_tick)
    );

    // x' = 141x + 1 mod 256: 141 = 1 mod 4 and odd c give the full period 256.
    reg [7:0] lcg;
    wire [19:0] lcg_q;
    macc_comb lcg_macc (.clk(clk), .a(lcg), .b(8'd141), .c(20'd1), .q(lcg_q));
    always @(posedge clk)
        if (reset) lcg <= 8'd0;
        else if (frame_tick) lcg <= lcg_q[7:0];

    wire [6:0] left_y, right_y;
    wire a_play, a_visible, a_left, a_paddle_hit, a_wall_hit, a_p1_scores, a_p2_scores;
    wire b_play, b_visible, b_left, b_paddle_hit, b_wall_hit, b_p1_scores, b_p2_scores;
    wire [7:0] a_x, b_x;
    wire [6:0] a_y, b_y;
    wire [3:0] a_aim_row, b_aim_row;

    ball #(
        .FIRST_SERVE(7'd40),
        .FIELD_W(FIELD_W),
        .FIELD_H(FIELD_H),
        .PADDLE_H(PADDLE_H),
        .RADIUS(BALL_R),
        .LEFT_CONTACT_X(LEFT_PADDLE_X + 8'd1 + BALL_R),
        .RIGHT_CONTACT_X(RIGHT_PADDLE_X - BALL_R)
    ) ball_a (
        .clk(clk),
        .reset(reset),
        .frame_tick(frame_tick),
        .rnd(lcg),
        .left_paddle_y(left_y),
        .right_paddle_y(right_y),
        .in_play(a_play),
        .visible(a_visible),
        .x(a_x),
        .y(a_y),
        .moving_left(a_left),
        .aim_row(a_aim_row),
        .paddle_hit(a_paddle_hit),
        .wall_hit(a_wall_hit),
        .left_scores(a_p1_scores),
        .right_scores(a_p2_scores)
    );

    // Its first serve 30 frames after ball A's keeps the two out of phase.
    ball #(
        .FIRST_SERVE(7'd70),
        .FIELD_W(FIELD_W),
        .FIELD_H(FIELD_H),
        .PADDLE_H(PADDLE_H),
        .RADIUS(BALL_R),
        .LEFT_CONTACT_X(LEFT_PADDLE_X + 8'd1 + BALL_R),
        .RIGHT_CONTACT_X(RIGHT_PADDLE_X - BALL_R)
    ) ball_b (
        .clk(clk),
        .reset(reset),
        .frame_tick(frame_tick),
        .rnd(~lcg),
        .left_paddle_y(left_y),
        .right_paddle_y(right_y),
        .in_play(b_play),
        .visible(b_visible),
        .x(b_x),
        .y(b_y),
        .moving_left(b_left),
        .aim_row(b_aim_row),
        .paddle_hit(b_paddle_hit),
        .wall_hit(b_wall_hit),
        .left_scores(b_p1_scores),
        .right_scores(b_p2_scores)
    );

    // Each AI chases the incoming ball nearest to its paddle, and only within
    // AI_VIEW of its own wall: watching the whole court it never misses.
    wire a_to_left = a_play & a_left & (a_x < AI_VIEW);
    wire b_to_left = b_play & b_left & (b_x < AI_VIEW);
    wire a_to_right = a_play & ~a_left & (a_x >= FIELD_W - AI_VIEW);
    wire b_to_right = b_play & ~b_left & (b_x >= FIELD_W - AI_VIEW);
    wire b_nearer_left = b_x < a_x;
    wire left_chases_b = b_to_left & (~a_to_left | b_nearer_left);
    wire right_chases_b = b_to_right & (~a_to_right | ~b_nearer_left);

    paddle #(
        .FIELD_H(FIELD_H),
        .PADDLE_H(PADDLE_H)
    ) left_paddle (
        .clk(clk),
        .reset(reset),
        .frame_tick(frame_tick),
        .button_up(p1_up),
        .button_down(p1_down),
        .target_valid(a_to_left | b_to_left),
        .target_y(left_chases_b ? b_y : a_y),
        .target_row(left_chases_b ? b_aim_row : a_aim_row),
        .y(left_y)
    );

    paddle #(
        .FIELD_H(FIELD_H),
        .PADDLE_H(PADDLE_H)
    ) right_paddle (
        .clk(clk),
        .reset(reset),
        .frame_tick(frame_tick),
        .button_up(p2_up),
        .button_down(p2_down),
        .target_valid(a_to_right | b_to_right),
        .target_y(right_chases_b ? b_y : a_y),
        .target_row(right_chases_b ? b_aim_row : a_aim_row),
        .y(right_y)
    );

    reg [3:0] p1_score, p2_score;
    wire [4:0] p1_next = p1_score + a_p1_scores + b_p1_scores;
    wire [4:0] p2_next = p2_score + a_p2_scores + b_p2_scores;
    // A score past 9 restarts the match.
    wire match_over = (p1_next > 5'd9) | (p2_next > 5'd9);
    always @(posedge clk)
        if (reset || (frame_tick && match_over)) begin
            p1_score <= 4'd0;
            p2_score <= 4'd0;
        end else if (frame_tick) begin
            p1_score <= p1_next[3:0];
            p2_score <= p2_next[3:0];
        end

    localparam [2:0] BEEP_FRAMES = 3'd6;
    reg [2:0] beep_left;
    wire beep_event = a_paddle_hit | a_wall_hit | a_p1_scores | a_p2_scores
        | b_paddle_hit | b_wall_hit | b_p1_scores | b_p2_scores;
    always @(posedge clk)
        if (reset) beep_left <= 3'd0;
        else if (frame_tick && beep_event) beep_left <= BEEP_FRAMES;
        else if (frame_tick && beep_left != 3'd0) beep_left <= beep_left - 3'd1;
    // vcount[4] flips every 16 lines of 31.47 kHz: a 983 Hz square wave.
    wire sound = (beep_left != 3'd0) & vcount[4];

    wire in_ball_a, in_ball_b;
    ball_disc #(.RADIUS(BALL_R)) disc_a (
        .clk(clk),
        .x(x),
        .y(y),
        .centre_x(a_x),
        .centre_y(a_y),
        .in_disc(in_ball_a)
    );
    ball_disc #(.RADIUS(BALL_R)) disc_b (
        .clk(clk),
        .x(x),
        .y(y),
        .centre_x(b_x),
        .centre_y(b_y),
        .in_disc(in_ball_b)
    );

    function in_paddle(input [7:0] px, input [6:0] py, input [7:0] paddle_x, input [6:0] paddle_y);
        reg [7:0] row;
        begin
            row = {1'b0, py} - {1'b0, paddle_y};
            in_paddle = (px == paddle_x || px == paddle_x + 8'd1) && row < PADDLE_H;
        end
    endfunction

    function [14:0] glyph(input [3:0] digit);
        case (digit)
            4'd0: glyph = 15'b111_101_101_101_111;
            4'd1: glyph = 15'b010_110_010_010_111;
            4'd2: glyph = 15'b111_001_111_100_111;
            4'd3: glyph = 15'b111_001_111_001_111;
            4'd4: glyph = 15'b101_101_111_001_001;
            4'd5: glyph = 15'b111_100_111_001_111;
            4'd6: glyph = 15'b111_100_111_101_111;
            4'd7: glyph = 15'b111_001_001_001_001;
            4'd8: glyph = 15'b111_101_111_101_111;
            4'd9: glyph = 15'b111_101_111_001_111;
            default: glyph = 15'b000_000_000_000_000;
        endcase
    endfunction

    wire on_paddle = in_paddle(x, y, LEFT_PADDLE_X, left_y) | in_paddle(x, y, RIGHT_PADDLE_X, right_y);

    // One glyph lookup serves both scores: the one under the beam.
    wire [5:0] cell_x = x[7:2];
    wire [4:0] cell_y = y[6:2];
    wire right_score = cell_x >= P2_DIGIT_CELL_X;
    wire [5:0] glyph_col = cell_x - (right_score ? P2_DIGIT_CELL_X : P1_DIGIT_CELL_X);
    wire [4:0] glyph_row = cell_y - DIGIT_CELL_Y;
    wire [14:0] glyph_bits = glyph(right_score ? p2_score : p1_score);
    wire on_digit = glyph_col < 6'd3 && glyph_row < 5'd5
        && glyph_bits[5'd14 - (glyph_row * 5'd3 + glyph_col[1:0])];
    // Dashed: 4 rows on, 4 off.
    wire on_net = (x == NET_X || x == NET_X + 8'd1) && !y[2];

    reg red, green, blue;
    always @(*)
        if (!visible) {red, green, blue} = 3'b000;
        else if (in_ball_a && a_visible) {red, green, blue} = 3'b110;
        else if (in_ball_b && b_visible) {red, green, blue} = 3'b011;
        else if (on_paddle || on_digit || on_net) {red, green, blue} = 3'b111;
        else {red, green, blue} = 3'b000;

    assign io_out = {sound, 4'b0000, blue, green, red, vsync_n, hsync_n};
    // Input pads: 5..8 (paddle buttons).
    assign io_oeb = 10'b0_1111_00000;
endmodule

module vga_timing (
    input wire clk,
    input wire reset,
    output reg [7:0] hcount,
    output reg [9:0] vcount,
    output wire visible,
    output wire hsync_n,
    output wire vsync_n,
    output wire frame_tick
);
    // 640x480 at 60 Hz with a quarter of the 25.175 MHz dot clock.
    localparam H_VISIBLE = 160, H_FRONT = 4, H_SYNC = 24, H_BACK = 12;
    localparam V_VISIBLE = 480, V_FRONT = 10, V_SYNC = 2, V_BACK = 33;
    localparam H_TOTAL = H_VISIBLE + H_FRONT + H_SYNC + H_BACK;
    localparam V_TOTAL = V_VISIBLE + V_FRONT + V_SYNC + V_BACK;
    localparam H_SYNC_START = H_VISIBLE + H_FRONT;
    localparam V_SYNC_START = V_VISIBLE + V_FRONT;

    wire h_last = hcount == H_TOTAL - 1;
    wire v_last = vcount == V_TOTAL - 1;

    always @(posedge clk)
        if (reset || h_last) hcount <= 8'd0;
        else hcount <= hcount + 8'd1;

    always @(posedge clk)
        if (reset || (h_last && v_last)) vcount <= 10'd0;
        else if (h_last) vcount <= vcount + 10'd1;

    assign frame_tick = hcount == 0 && vcount == V_VISIBLE;
    assign visible = hcount < H_VISIBLE && vcount < V_VISIBLE;
    assign hsync_n = !(hcount >= H_SYNC_START && hcount < H_SYNC_START + H_SYNC);
    assign vsync_n = !(vcount >= V_SYNC_START && vcount < V_SYNC_START + V_SYNC);
endmodule

// One ball: a SERVE_WAIT/PLAY state machine updated once per frame.
module ball (
    input wire clk,
    input wire reset,
    input wire frame_tick,
    // [7] serve direction, [6:4] serve vy, [3:0] next aim row.
    input wire [7:0] rnd,
    input wire [6:0] left_paddle_y,
    input wire [6:0] right_paddle_y,
    output wire in_play,
    output wire visible,
    output reg [7:0] x,
    output reg [6:0] y,
    output reg moving_left,
    // Paddle row the AI puts at this ball, so returns leave at every angle,
    // not flat off the middle band.
    output reg [3:0] aim_row,
    output wire paddle_hit,
    output wire wall_hit,
    output wire left_scores,
    output wire right_scores
);
    parameter [6:0] FIRST_SERVE = 7'd40;
    parameter [6:0] SERVE_FRAMES = 7'd40;
    parameter [7:0] FIELD_W = 8'd160;
    parameter [6:0] FIELD_H = 7'd120;
    parameter [6:0] PADDLE_H = 7'd16;
    parameter [2:0] RADIUS = 3'd3;
    // Centre x at which the ball's edge meets each paddle face.
    parameter [7:0] LEFT_CONTACT_X = 8'd8;
    parameter [7:0] RIGHT_CONTACT_X = 8'd151;

    localparam SERVE_WAIT = 1'b0;
    localparam PLAY = 1'b1;
    localparam [7:0] CENTRE_X = FIELD_W / 2;
    localparam [6:0] CENTRE_Y = FIELD_H / 2;
    localparam [6:0] TOP_Y = RADIUS;
    localparam [6:0] BOTTOM_Y = FIELD_H - 7'd1 - RADIUS;
    // Paddle rows the ball can touch, counted from RADIUS above its top.
    localparam [7:0] CONTACT_ROWS = PADDLE_H + 2 * RADIUS;

    reg phase;
    // |vx| = 2 + fast.
    reg fast;
    // Two's complement, -2..2.
    reg [2:0] vy;
    reg [6:0] wait_frames;
    reg served;

    function [2:0] serve_vy(input [2:0] pick);
        case (pick)
            3'd0, 3'd4: serve_vy = 3'b110;
            3'd1, 3'd5: serve_vy = 3'b111;
            3'd2, 3'd6: serve_vy = 3'b001;
            default: serve_vy = 3'b010;
        endcase
    endfunction

    // Five bands over the 22 contact rows: -2, -1, 0, +1, +2.
    function [2:0] bounce_vy(input [7:0] contact);
        if (contact < 8'd5) bounce_vy = 3'b110;
        else if (contact < 8'd9) bounce_vy = 3'b111;
        else if (contact < 8'd13) bounce_vy = 3'b000;
        else if (contact < 8'd17) bounce_vy = 3'b001;
        else bounce_vy = 3'b010;
    endfunction

    assign in_play = phase == PLAY;
    // Blinks at the centre while it waits to serve.
    assign visible = in_play || wait_frames[3];

    wire serve_now = phase == SERVE_WAIT && wait_frames == (served ? SERVE_FRAMES : FIRST_SERVE);

    // vx in two's complement: +2, +3, -2, -3.
    wire [2:0] vx = {moving_left, !(moving_left && fast), fast};
    // Bit 9 set means the ball left past x = 0.
    wire [9:0] x_next = {2'b00, x} + {{7{vx[2]}}, vx};
    wire [8:0] y_next = {2'b00, y} + {{6{vy[2]}}, vy};
    wire top_wall = y_next[8] || y_next < TOP_Y;
    wire bottom_wall = !y_next[8] && y_next > BOTTOM_Y;

    // Only the paddle the ball moves toward can hit it.
    wire [6:0] facing_paddle_y = moving_left ? left_paddle_y : right_paddle_y;
    wire [7:0] contact = {1'b0, y} + RADIUS - {1'b0, facing_paddle_y};
    wire left_hit = moving_left && x > LEFT_CONTACT_X && x_next <= LEFT_CONTACT_X;
    wire right_hit = !moving_left && x < RIGHT_CONTACT_X && x_next >= RIGHT_CONTACT_X;

    assign right_scores = in_play && x_next[9];
    assign left_scores = in_play && !x_next[9] && x_next >= FIELD_W;
    wire scored = left_scores || right_scores;
    assign paddle_hit = in_play && !scored && (left_hit || right_hit) && contact < CONTACT_ROWS;
    assign wall_hit = in_play && !scored && !paddle_hit && (top_wall || bottom_wall);

    always @(posedge clk)
        if (reset) begin
            phase <= SERVE_WAIT;
            x <= 8'd0;
            y <= 7'd0;
            moving_left <= 1'b0;
            aim_row <= 4'd0;
            fast <= 1'b0;
            vy <= 3'd0;
            wait_frames <= 7'd0;
            served <= 1'b0;
        end else if (frame_tick) begin
            if (phase == SERVE_WAIT) begin
                x <= CENTRE_X;
                y <= CENTRE_Y;
                wait_frames <= serve_now ? 7'd0 : wait_frames + 7'd1;
                if (serve_now) begin
                    phase <= PLAY;
                    served <= 1'b1;
                    moving_left <= rnd[7];
                    vy <= serve_vy(rnd[6:4]);
                    aim_row <= rnd[3:0];
                    fast <= 1'b0;
                end
            end else if (scored) begin
                phase <= SERVE_WAIT;
            end else if (paddle_hit) begin
                moving_left <= !moving_left;
                fast <= 1'b1;
                aim_row <= rnd[3:0];
                x <= left_hit ? LEFT_CONTACT_X : RIGHT_CONTACT_X;
                vy <= bounce_vy(contact);
            end else begin
                x <= x_next[7:0];
                if (top_wall) begin
                    y <= TOP_Y;
                    vy <= -vy;
                end else if (bottom_wall) begin
                    y <= BOTTOM_Y;
                    vy <= -vy;
                end else begin
                    y <= y_next[6:0];
                end
            end
        end
endmodule

// AI puts its row target_row at target_y at up to 2 px per frame, or its
// centre at mid-field with no target; either button takes it over at 3.
module paddle (
    input wire clk,
    input wire reset,
    input wire frame_tick,
    input wire button_up,
    input wire button_down,
    input wire target_valid,
    input wire [6:0] target_y,
    input wire [3:0] target_row,
    output reg [6:0] y
);
    parameter [6:0] FIELD_H = 7'd120;
    parameter [6:0] PADDLE_H = 7'd16;

    localparam [6:0] Y_MAX = FIELD_H - PADDLE_H;
    localparam [7:0] AI_STEP = 8'd2;
    localparam [7:0] MANUAL_STEP = 8'd3;

    wire [6:0] aim_y = target_valid ? target_y : FIELD_H / 2;
    wire [3:0] aim_row = target_valid ? target_row : PADDLE_H / 2;
    // Two's complement distance from the aiming row to aim_y.
    wire [7:0] gap = {1'b0, aim_y} - ({1'b0, y} + aim_row);

    // |gap| <= AI_STEP as one unsigned compare; a clamp per sign leaves Yosys
    // 0.62 a coarse $mux that ABC never maps.
    wire [7:0] gap_biased = gap + AI_STEP;
    wire gap_near = gap_biased <= AI_STEP + AI_STEP;

    // Two's complement, -3..3.
    reg [7:0] step;
    always @(*)
        if (button_up || button_down)
            step = (button_down ? MANUAL_STEP : 8'd0) - (button_up ? MANUAL_STEP : 8'd0);
        else if (gap_near)
            step = gap;
        else
            step = gap[7] ? -AI_STEP : AI_STEP;

    wire [8:0] y_next = {2'b00, y} + {step[7], step};

    always @(posedge clk)
        if (reset) y <= 7'd0;
        else if (frame_tick)
            if (y_next[8]) y <= 7'd0;
            else if (y_next > Y_MAX) y <= Y_MAX;
            else y <= y_next[6:0];
endmodule

// Pixel inside a ball of radius about r: m(dx)^2 + m(dy)^2 <= r(r+1) on two
// chained MACCs, m the magnitude below.
module ball_disc (
    input wire clk,
    input wire [7:0] x,
    input wire [6:0] y,
    input wire [7:0] centre_x,
    input wire [6:0] centre_y,
    output wire in_disc
);
    parameter [2:0] RADIUS = 3'd3;
    // r(r+1) is the midpoint-circle bound: rounder than r^2 on a pixel grid.
    localparam [19:0] DIST2_MAX = RADIUS * (RADIUS + 1);

    // Ones' complement gives |d| - 1 for d < 0: the disc spans d = -r-1..r,
    // an even width centred half a pixel left and up, for no incrementer.
    // Eight-bit coordinates keep it within 255, so A and B need no saturation.
    function [7:0] magnitude(input [8:0] d);
        magnitude = d[7:0] ^ {8{d[8]}};
    endfunction

    wire [7:0] dx = magnitude({1'b0, x} - {1'b0, centre_x});
    wire [7:0] dy = magnitude({2'b00, y} - {2'b00, centre_y});
    wire [19:0] dx2, dist2;

    macc_comb square_dx (.clk(clk), .a(dx), .b(dx), .c(20'd0), .q(dx2));

    macc_comb add_dy2 (.clk(clk), .a(dy), .b(dy), .c(dx2), .q(dist2));

    assign in_disc = dist2 <= DIST2_MAX;
endmodule


// q = a * b + c on one MACC_8x8_20 with every register bypassed. The BEL has
// scalar ports, so this adapter restores the buses. CLK takes the real clock
// because the MACC tile routes CLK only from the global clock lines, never GND.
module macc_comb (
    input wire clk,
    input wire [7:0] a,
    input wire [7:0] b,
    input wire [19:0] c,
    output wire [19:0] q
);
    MACC_8x8_20 #(
        .A_REG(0),
        .B_REG(0),
        .C_REG(0),
        .SIGN_EXT(0),
        .ACC_SEL(0),
        .ACC_OUT(0),
        .CLK_INV(0)
    ) macc (
        .CLK(clk),
        .EN(1'b0),
        .ACC_RST(1'b0),
        .ACC_CI(1'b0),
        .ACC_CO(),
        .A0(a[0]),
        .A1(a[1]),
        .A2(a[2]),
        .A3(a[3]),
        .A4(a[4]),
        .A5(a[5]),
        .A6(a[6]),
        .A7(a[7]),
        .B0(b[0]),
        .B1(b[1]),
        .B2(b[2]),
        .B3(b[3]),
        .B4(b[4]),
        .B5(b[5]),
        .B6(b[6]),
        .B7(b[7]),
        .C0(c[0]),
        .C1(c[1]),
        .C2(c[2]),
        .C3(c[3]),
        .C4(c[4]),
        .C5(c[5]),
        .C6(c[6]),
        .C7(c[7]),
        .C8(c[8]),
        .C9(c[9]),
        .C10(c[10]),
        .C11(c[11]),
        .C12(c[12]),
        .C13(c[13]),
        .C14(c[14]),
        .C15(c[15]),
        .C16(c[16]),
        .C17(c[17]),
        .C18(c[18]),
        .C19(c[19]),
        .Q0(q[0]),
        .Q1(q[1]),
        .Q2(q[2]),
        .Q3(q[3]),
        .Q4(q[4]),
        .Q5(q[5]),
        .Q6(q[6]),
        .Q7(q[7]),
        .Q8(q[8]),
        .Q9(q[9]),
        .Q10(q[10]),
        .Q11(q[11]),
        .Q12(q[12]),
        .Q13(q[13]),
        .Q14(q[14]),
        .Q15(q[15]),
        .Q16(q[16]),
        .Q17(q[17]),
        .Q18(q[18]),
        .Q19(q[19])
    );
endmodule

`default_nettype wire
