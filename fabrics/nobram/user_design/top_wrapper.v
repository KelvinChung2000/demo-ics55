`default_nettype none


module top_wrapper;

    // io[i] sits on the E_IO tile eFPGA_top binds to A_*_top[i], X12Y10 up to
    // X12Y1. IOBUF.EN is an active-high output enable, so it takes the inverted oeb.
    wire [9:0] io_in, io_out, io_oeb;
    (* keep, BEL="X12Y1.A" *) IOBUF io9_i (
        .OUT(io_in[9]),
        .IN (io_out[9]),
        .EN (~io_oeb[9])
    );
    (* keep, BEL="X12Y2.A" *) IOBUF io8_i (
        .OUT(io_in[8]),
        .IN (io_out[8]),
        .EN (~io_oeb[8])
    );
    (* keep, BEL="X12Y3.A" *) IOBUF io7_i (
        .OUT(io_in[7]),
        .IN (io_out[7]),
        .EN (~io_oeb[7])
    );
    (* keep, BEL="X12Y4.A" *) IOBUF io6_i (
        .OUT(io_in[6]),
        .IN (io_out[6]),
        .EN (~io_oeb[6])
    );
    (* keep, BEL="X12Y5.A" *) IOBUF io5_i (
        .OUT(io_in[5]),
        .IN (io_out[5]),
        .EN (~io_oeb[5])
    );
    (* keep, BEL="X12Y6.A" *) IOBUF io4_i (
        .OUT(io_in[4]),
        .IN (io_out[4]),
        .EN (~io_oeb[4])
    );
    (* keep, BEL="X12Y7.A" *) IOBUF io3_i (
        .OUT(io_in[3]),
        .IN (io_out[3]),
        .EN (~io_oeb[3])
    );
    (* keep, BEL="X12Y8.A" *) IOBUF io2_i (
        .OUT(io_in[2]),
        .IN (io_out[2]),
        .EN (~io_oeb[2])
    );
    (* keep, BEL="X12Y9.A" *) IOBUF io1_i (
        .OUT(io_in[1]),
        .IN (io_out[1]),
        .EN (~io_oeb[1])
    );
    (* keep, BEL="X12Y10.A" *) IOBUF io0_i (
        .OUT(io_in[0]),
        .IN (io_out[0]),
        .EN (~io_oeb[0])
    );

    // No UserCLK in this fabric: the clock enters on the SYS_RESET pad, whose
    // only fabric connection is the SW_term global buffers.
    wire clk_pad, clk;
    (* keep, BEL="X0Y11.E" *) SYS_RESET clk_pad_i (
        .RESET(clk_pad)
    );
    (* keep, BEL="X0Y11.A" *) GBUF clk_buf_i (
        .IN (clk_pad),
        .OUT(clk)
    );

    sequential_16bit_en top_i (
        .clk(clk),
        .io_in(io_in),
        .io_out(io_out),
        .io_oeb(io_oeb)
    );

endmodule
`default_nettype wire
