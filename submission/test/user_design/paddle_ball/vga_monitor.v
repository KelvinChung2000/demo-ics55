`timescale 1ps / 1ps
`default_nettype none

// A VGA monitor that sees only the five video pins. It checks the line and
// frame timing in clocks and writes each frame_stride-th frame as a binary
// 160x480 PPM. frame counts completed vsyncs, -1 until the first one ends.
// Plusargs: +frame_stride=<write every Nth> +out_dir=<dir>
// +stream=<path> also appends every frame to one PPM stream, such as a FIFO
// that ffplay reads.
module vga_monitor (
    input wire clk,
    input wire active,
    input wire hsync,
    input wire vsync,
    input wire [2:0] rgb,
    output integer frame
);
    localparam H_TOTAL = 200;
    localparam H_SYNC = 24;
    localparam H_BACK = 12;
    localparam H_VISIBLE = 160;
    localparam V_TOTAL = 525;
    localparam V_SYNC = 2;
    localparam V_BACK = 33;
    localparam V_VISIBLE = 480;

    integer frame_stride = 20;
    string out_dir = "frames";
    string stream_path;
    integer stream_fd = 0;

    initial begin
        void'($value$plusargs("frame_stride=%d", frame_stride));
        void'($value$plusargs("out_dir=%s", out_dir));
        // A FIFO blocks here until its reader opens it.
        if ($value$plusargs("stream=%s", stream_path)) begin
            stream_fd = $fopen(stream_path, "wb");
            if (stream_fd == 0) $fatal(1, "cannot open stream %s", stream_path);
        end
        frame = -1;
    end

    reg [2:0] framebuffer [0:H_VISIBLE * V_VISIBLE - 1];

    reg hsync_prev = 1'b1;
    reg vsync_prev = 1'b1;
    integer cycle = 0;
    integer hsync_fall_cycle = -1;
    integer clocks_since_hsync_end = -1;
    integer lines_since_vsync_end = -1;
    integer lines_in_frame = 0;
    integer lines_in_vsync = 0;
    integer frames_written = 0;
    reg timing_checked = 1'b0;

    task write_ppm(input integer fd);
        integer i;
        begin
            $fwrite(fd, "P6\n%0d %0d\n255\n", H_VISIBLE, V_VISIBLE);
            for (i = 0; i < H_VISIBLE * V_VISIBLE; i = i + 1)
                $fwrite(fd, "%c%c%c", framebuffer[i][2] ? 8'd255 : 8'd0,
                        framebuffer[i][1] ? 8'd255 : 8'd0, framebuffer[i][0] ? 8'd255 : 8'd0);
        end
    endtask

    task write_frame(input integer index);
        integer fd;
        string path;
        begin
            path = $sformatf("%s/frame_%04d.ppm", out_dir, index);
            fd = $fopen(path, "wb");
            if (fd == 0) $fatal(1, "cannot open %s", path);
            write_ppm(fd);
            $fclose(fd);
            frames_written = frames_written + 1;
        end
    endtask

    // Sample mid-cycle, after the design settles from the rising edge.
    always @(negedge clk) if (active) begin
        cycle = cycle + 1;
        if (^{hsync, vsync, rgb} === 1'bx)
            $fatal(1, "VGA pins have X at cycle %0d: hsync %b vsync %b rgb %b", cycle, hsync, vsync, rgb);

        if (!hsync && hsync_prev) begin
            if (timing_checked && cycle - hsync_fall_cycle != H_TOTAL)
                $fatal(1, "line period %0d clocks, expected %0d", cycle - hsync_fall_cycle, H_TOTAL);
            hsync_fall_cycle = cycle;
            lines_in_frame = lines_in_frame + 1;
            if (!vsync) lines_in_vsync = lines_in_vsync + 1;
        end
        if (hsync && !hsync_prev) begin
            if (timing_checked && cycle - hsync_fall_cycle != H_SYNC)
                $fatal(1, "hsync width %0d clocks, expected %0d", cycle - hsync_fall_cycle, H_SYNC);
            clocks_since_hsync_end = 0;
            if (lines_since_vsync_end >= 0) lines_since_vsync_end = lines_since_vsync_end + 1;
        end else if (clocks_since_hsync_end >= 0) begin
            clocks_since_hsync_end = clocks_since_hsync_end + 1;
        end

        if (!vsync && vsync_prev) begin
            if (timing_checked && lines_in_frame != V_TOTAL)
                $fatal(1, "%0d lines per frame, expected %0d", lines_in_frame, V_TOTAL);
            lines_in_frame = 0;
            lines_in_vsync = 0;
        end
        if (vsync && !vsync_prev) begin
            if (timing_checked && lines_in_vsync != V_SYNC)
                $fatal(1, "vsync width %0d lines, expected %0d", lines_in_vsync, V_SYNC);
            if (frame >= 0 && frame % frame_stride == 0) write_frame(frame);
            if (frame >= 0 && stream_fd != 0) begin
                write_ppm(stream_fd);
                $fflush(stream_fd);
            end
            // The frame before the first vsync end is partial; checks start one frame later.
            timing_checked = frame >= 0;
            frame = frame + 1;
            lines_since_vsync_end = 0;
        end

        // The V_BACK-th hsync end after vsync ends opens the first visible line.
        if (frame >= 0 && clocks_since_hsync_end >= H_BACK && clocks_since_hsync_end < H_BACK + H_VISIBLE
                && lines_since_vsync_end >= V_BACK && lines_since_vsync_end < V_BACK + V_VISIBLE)
            framebuffer[(lines_since_vsync_end - V_BACK) * H_VISIBLE + clocks_since_hsync_end - H_BACK] = rgb;

        hsync_prev = hsync;
        vsync_prev = vsync;
    end
endmodule

`default_nettype wire
